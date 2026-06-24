"""
Organic Facebook Page connectivity and metadata retrieval service.

How Facebook exposes organic Page metadata:
  Facebook Graph API (Pages API):
    GET /{page-id}                    → Page profile + fan counts
    GET /{page-id}/posts              → Page posts (organic content)
    GET /{page-id}/photos             → Page photos
    GET /{page-id}/videos             → Page videos
    GET /{page-id}/insights           → Page insights (optional, read_insights)

  Meta concept equivalents:
    Salesforce SObject  → Page / Post / Photo / Video
    Salesforce Field    → Graph API field on each object
    GA4 Dimension       → Post snippet field (message, created_time)

  Authentication (FREE for your own Page as app admin/test user):
    1. Create a Facebook Page (free)
    2. Meta Developer app → add Facebook Login + Pages API permissions
    3. Generate Page Access Token with pages_read_engagement, pages_show_list
    Required for live: FACEBOOK_PAGE_ACCESS_TOKEN, FACEBOOK_PAGE_ID

  Demo mode (no credentials):
    Returns real Facebook Graph API field schema catalogs.
"""

import logging
from typing import Any

import requests
from core.config import settings

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.facebook.com"

PAGE_FIELDS = [
    {"name": "id", "label": "Page ID", "type": "string", "description": "Unique Facebook Page identifier"},
    {"name": "name", "label": "Name", "type": "string", "description": "Page display name"},
    {"name": "about", "label": "About", "type": "string", "description": "Short Page description"},
    {"name": "category", "label": "Category", "type": "string", "description": "Page category (e.g. Business)"},
    {"name": "fan_count", "label": "Page Likes", "type": "integer", "description": "Total Page likes"},
    {"name": "followers_count", "label": "Followers", "type": "integer", "description": "Total Page followers"},
    {"name": "link", "label": "Page URL", "type": "string", "description": "facebook.com/... link"},
    {"name": "phone", "label": "Phone", "type": "string", "description": "Contact phone number"},
    {"name": "website", "label": "Website", "type": "string", "description": "Linked website URL"},
    {"name": "verification_status", "label": "Verification", "type": "enum", "description": "blue_verified, gray_verified, not_verified"},
    {"name": "is_published", "label": "Published", "type": "boolean", "description": "Whether Page is published"},
    {"name": "username", "label": "Username", "type": "string", "description": "Page @username handle"},
]

POST_FIELDS = [
    {"name": "id", "label": "Post ID", "type": "string", "description": "Unique post identifier"},
    {"name": "message", "label": "Message", "type": "string", "description": "Post text content"},
    {"name": "story", "label": "Story", "type": "string", "description": "Auto-generated story text"},
    {"name": "created_time", "label": "Created Time", "type": "datetime", "description": "When post was published"},
    {"name": "updated_time", "label": "Updated Time", "type": "datetime", "description": "Last update timestamp"},
    {"name": "permalink_url", "label": "Permalink", "type": "string", "description": "Direct link to post"},
    {"name": "type", "label": "Type", "type": "enum", "description": "photo, video, status, link, etc."},
    {"name": "full_picture", "label": "Picture", "type": "string", "description": "URL of attached image"},
    {"name": "shares", "label": "Shares", "type": "object", "description": "Share count summary"},
    {"name": "reactions", "label": "Reactions", "type": "object", "description": "Like/love/etc. reaction summary"},
    {"name": "comments", "label": "Comments", "type": "object", "description": "Comment count summary"},
    {"name": "is_published", "label": "Published", "type": "boolean", "description": "Whether post is visible"},
]

PHOTO_FIELDS = [
    {"name": "id", "label": "Photo ID", "type": "string", "description": "Unique photo identifier"},
    {"name": "name", "label": "Name", "type": "string", "description": "Photo caption/name"},
    {"name": "created_time", "label": "Created Time", "type": "datetime", "description": "Upload timestamp"},
    {"name": "link", "label": "Link", "type": "string", "description": "URL to photo on Facebook"},
    {"name": "images", "label": "Images", "type": "array", "description": "Available image sizes"},
    {"name": "width", "label": "Width", "type": "integer", "description": "Image width in pixels"},
    {"name": "height", "label": "Height", "type": "integer", "description": "Image height in pixels"},
]

VIDEO_FIELDS = [
    {"name": "id", "label": "Video ID", "type": "string", "description": "Unique video identifier"},
    {"name": "title", "label": "Title", "type": "string", "description": "Video title"},
    {"name": "description", "label": "Description", "type": "string", "description": "Video description"},
    {"name": "created_time", "label": "Created Time", "type": "datetime", "description": "Upload timestamp"},
    {"name": "permalink_url", "label": "Permalink", "type": "string", "description": "Direct link to video"},
    {"name": "length", "label": "Duration", "type": "float", "description": "Video length in seconds"},
    {"name": "views", "label": "Views", "type": "integer", "description": "View count"},
    {"name": "source", "label": "Source URL", "type": "string", "description": "Direct video source (if permitted)"},
]

INSIGHTS_METRICS = [
    {"name": "page_impressions", "label": "Page Impressions", "type": "integer", "description": "Times Page content was on screen"},
    {"name": "page_impressions_unique", "label": "Unique Impressions", "type": "integer", "description": "Unique people who saw Page content"},
    {"name": "page_engaged_users", "label": "Engaged Users", "type": "integer", "description": "People who engaged with Page"},
    {"name": "page_post_engagements", "label": "Post Engagements", "type": "integer", "description": "Likes, comments, shares on posts"},
    {"name": "page_fans", "label": "Page Fans", "type": "integer", "description": "Total Page likes over time"},
    {"name": "page_views_total", "label": "Page Views", "type": "integer", "description": "Total Page profile views"},
    {"name": "page_actions_post_reactions_total", "label": "Post Reactions", "type": "integer", "description": "Total reactions on posts"},
]

METADATA_CATEGORIES = [
    {"id": "page", "label": "Page", "description": "Live Facebook Page profile from Graph API"},
    {"id": "posts", "label": "Posts", "description": "Organic posts published on the Page"},
    {"id": "photos", "label": "Photos", "description": "Photos uploaded to the Page"},
    {"id": "videos", "label": "Videos", "description": "Videos on the Page"},
    {"id": "page_fields", "label": "Page Fields", "description": "Queryable fields on Page object"},
    {"id": "post_fields", "label": "Post Fields", "description": "Queryable fields on Post object"},
    {"id": "photo_fields", "label": "Photo Fields", "description": "Queryable fields on Photo object"},
    {"id": "video_fields", "label": "Video Fields", "description": "Queryable fields on Video object"},
    {"id": "insights_metrics", "label": "Insights Metrics", "description": "Page Insights metrics (read_insights scope)"},
]

FIELD_CATALOG: dict[str, list] = {
    "page_fields": PAGE_FIELDS,
    "post_fields": POST_FIELDS,
    "photo_fields": PHOTO_FIELDS,
    "video_fields": VIDEO_FIELDS,
    "insights_metrics": INSIGHTS_METRICS,
}

LIST_EDGES = {
    "posts": "posts",
    "photos": "photos",
    "videos": "videos",
}

LIST_FIELDS = {
    "posts": "id,message,story,created_time,permalink_url,type,shares,reactions.summary(true),comments.summary(true)",
    "photos": "id,name,created_time,link,images",
    "videos": "id,title,description,created_time,permalink_url,views,length",
}


def _is_demo_mode() -> bool:
    return not bool(settings.FACEBOOK_PAGE_ACCESS_TOKEN) or not bool(settings.FACEBOOK_PAGE_ID)


def _api_version() -> str:
    return settings.FACEBOOK_API_VERSION or settings.META_API_VERSION or "v21.0"


def _check_live_config() -> None:
    if not settings.FACEBOOK_PAGE_ACCESS_TOKEN:
        raise ConnectionError(
            "FACEBOOK_PAGE_ACCESS_TOKEN is not set in .env. "
            "Generate a Page access token with pages_read_engagement from Graph API Explorer."
        )
    if not settings.FACEBOOK_PAGE_ID:
        raise ConnectionError(
            "FACEBOOK_PAGE_ID is not set in .env. "
            "Find it in Page Settings → About, or via GET /me/accounts in Graph API Explorer."
        )


def _page_id() -> str:
    return settings.FACEBOOK_PAGE_ID.strip()


def _graph_get(path: str, params: dict | None = None) -> dict:
    _check_live_config()
    params = dict(params or {})
    params["access_token"] = settings.FACEBOOK_PAGE_ACCESS_TOKEN
    url = f"{GRAPH_BASE}/{_api_version()}/{path.lstrip('/')}"
    resp = requests.get(url, params=params, timeout=30)
    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"Facebook API returned non-JSON [{resp.status_code}]: {resp.text[:300]}")

    if "error" in data:
        err = data["error"]
        code = err.get("code", 0)
        msg = err.get("message", str(err))
        subcode = err.get("error_subcode", "")
        full = f"{msg} (code {code}, subcode {subcode})".strip()
        if code in (190, 102, 463):
            raise ConnectionError(f"Facebook authentication failed: {full}")
        if code in (10, 200, 294):
            raise PermissionError(
                f"Facebook access denied: {full}. "
                "Ensure token is a Page token with pages_read_engagement and pages_show_list."
            )
        raise RuntimeError(f"Facebook API error: {full}")

    return data


def _get_page() -> dict:
    fields = "id,name,about,category,fan_count,followers_count,link,phone,website,verification_status,is_published,username"
    return _graph_get(_page_id(), {"fields": fields})


def test_connection() -> dict:
    if _is_demo_mode():
        total_fields = sum(len(v) for v in FIELD_CATALOG.values())
        return {
            "connected": True,
            "mode": "demo",
            "message": (
                "Demo Mode — showing Facebook Pages Graph API field schema. "
                "Set FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID in .env for live data."
            ),
            "categories_count": len(METADATA_CATEGORIES),
            "total_fields": total_fields,
            "api_version": _api_version(),
            "scopes_needed": "pages_read_engagement, pages_show_list",
        }

    _check_live_config()
    page = _get_page()

    posts_sample = 0
    try:
        posts = _graph_get(f"{_page_id()}/posts", {"fields": "id", "limit": 1})
        posts_sample = len(posts.get("data", []))
        if posts.get("paging", {}).get("next"):
            posts_sample = "1+"
    except Exception:
        posts_sample = 0

    return {
        "connected": True,
        "mode": "live",
        "page_id": page.get("id", _page_id()),
        "page_name": page.get("name", ""),
        "category": page.get("category", ""),
        "fan_count": page.get("fan_count", 0),
        "followers_count": page.get("followers_count", 0),
        "link": page.get("link", ""),
        "posts_sample": posts_sample,
        "auth_method": "Page Access Token",
        "api_version": _api_version(),
        "content_type": "Organic Facebook Page (not ads)",
    }


def list_categories() -> list[dict]:
    counts: dict[str, Any] = {cat_id: len(fields) for cat_id, fields in FIELD_CATALOG.items()}

    if _is_demo_mode():
        counts["page"] = 1
        counts["posts"] = 0
        counts["photos"] = 0
        counts["videos"] = 0
        return [{**cat, "items_count": counts.get(cat["id"], 0)} for cat in METADATA_CATEGORIES]

    _check_live_config()
    counts["page"] = 1

    for cat_id, edge in LIST_EDGES.items():
        try:
            data = _graph_get(f"{_page_id()}/{edge}", {"fields": "id", "limit": 50})
            items = data.get("data", [])
            counts[cat_id] = len(items)
            if data.get("paging", {}).get("next") and len(items) == 50:
                counts[cat_id] = f"{len(items)}+"
        except Exception:
            counts[cat_id] = 0

    return [{**cat, "items_count": counts.get(cat["id"], 0)} for cat in METADATA_CATEGORIES]


def list_items(category_id: str) -> dict:
    if category_id in FIELD_CATALOG:
        items = [
            {
                "name": f["name"],
                "label": f["label"],
                "description": f.get("description", ""),
                "data_type": f.get("type", "string"),
            }
            for f in FIELD_CATALOG[category_id]
        ]
        mode = "demo" if _is_demo_mode() else "live"
        return {"category": category_id, "total": len(items), "items": items, "mode": mode}

    if _is_demo_mode():
        if category_id in ("page", "posts", "photos", "videos"):
            return {
                "category": category_id,
                "total": 0,
                "items": [],
                "mode": "demo",
                "message": "Set FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID in .env to load live objects.",
            }
        raise LookupError(
            f"Category '{category_id}' not found. Available: {[c['id'] for c in METADATA_CATEGORIES]}"
        )

    _check_live_config()

    if category_id == "page":
        page = _get_page()
        return {
            "category": category_id,
            "total": 1,
            "items": [
                {
                    "name": page.get("id", _page_id()),
                    "label": page.get("name", "Facebook Page"),
                    "description": f"{page.get('fan_count', 0)} likes · {page.get('followers_count', 0)} followers",
                    "raw": page,
                }
            ],
            "mode": "live",
        }

    if category_id in LIST_EDGES:
        edge = LIST_EDGES[category_id]
        fields = LIST_FIELDS[category_id]
        data = _graph_get(f"{_page_id()}/{edge}", {"fields": fields, "limit": 25})
        items = []
        for row in data.get("data", []):
            label = _row_label(row, category_id)
            items.append(
                {
                    "name": row.get("id", ""),
                    "label": label,
                    "description": _summarize_row(row, category_id),
                    "raw": row,
                }
            )
        return {"category": category_id, "total": len(items), "items": items, "mode": "live"}

    raise LookupError(
        f"Category '{category_id}' not found. Available: {[c['id'] for c in METADATA_CATEGORIES]}"
    )


def get_item_detail(category_id: str, item_id: str) -> dict:
    if category_id in FIELD_CATALOG:
        for f in FIELD_CATALOG[category_id]:
            if f["name"] == item_id:
                mode = "demo" if _is_demo_mode() else "live"
                return {**f, "category": category_id, "mode": mode}
        raise LookupError(f"Field '{item_id}' not found in '{category_id}'.")

    if _is_demo_mode():
        raise LookupError("Live object detail requires FACEBOOK_PAGE_ACCESS_TOKEN in .env.")

    _check_live_config()

    if category_id == "page":
        result = list_items("page")
        return {**result["items"][0], "category": category_id, "mode": "live"}

    if category_id in LIST_EDGES:
        fields = LIST_FIELDS[category_id]
        obj = _graph_get(item_id, {"fields": fields})
        return {
            "name": obj.get("id", item_id),
            "label": _row_label(obj, category_id),
            "category": category_id,
            "fields": obj,
            "mode": "live",
        }

    raise LookupError(f"Cannot get detail for category '{category_id}'.")


def _row_label(row: dict, category_id: str) -> str:
    if category_id == "posts":
        msg = (row.get("message") or row.get("story") or "").strip()
        return (msg[:60] + "…") if len(msg) > 60 else (msg or row.get("id", ""))
    if category_id == "photos":
        return row.get("name") or row.get("id", "")
    if category_id == "videos":
        return row.get("title") or row.get("id", "")
    return row.get("id", "")


def _summarize_row(row: dict, category_id: str) -> str:
    parts = []
    if row.get("created_time"):
        parts.append(str(row["created_time"])[:10])
    if category_id == "posts" and row.get("type"):
        parts.append(row["type"])
    if category_id == "videos" and row.get("views") is not None:
        parts.append(f"{row['views']} views")
    reactions = row.get("reactions", {}).get("summary", {}).get("total_count")
    if reactions is not None:
        parts.append(f"{reactions} reactions")
    comments = row.get("comments", {}).get("summary", {}).get("total_count")
    if comments is not None:
        parts.append(f"{comments} comments")
    return " · ".join(parts) if parts else category_id.rstrip("s")

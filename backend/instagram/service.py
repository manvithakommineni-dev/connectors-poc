"""
Organic Instagram Business/Creator account connectivity and metadata retrieval.

Instagram Graph API (via Facebook Graph API):
    GET /{ig-user-id}                 → Profile (username, followers, bio)
    GET /{ig-user-id}/media           → Posts, reels, carousels
    GET /{ig-user-id}/stories         → Active stories (if any)
    GET /{media-id}                   → Single media detail

  Authentication (FREE for your own account as app admin/test user):
    1. Instagram Business or Creator account linked to your Facebook Page
    2. Meta Developer app → permissions: instagram_basic, pages_show_list
    3. Page access token (can reuse FACEBOOK_PAGE_ACCESS_TOKEN)
    Required for live: INSTAGRAM_ACCESS_TOKEN (or Page token), INSTAGRAM_ACCOUNT_ID
    Optional: leave INSTAGRAM_ACCOUNT_ID empty if FACEBOOK_PAGE_ID is set — auto-resolved

  Demo mode (no credentials):
    Returns real Instagram Graph API field schema catalogs.
"""

import logging
from typing import Any

import requests
from core.config import settings

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.facebook.com"
IG_LOGIN_BASE = "https://graph.instagram.com"

ACCOUNT_PROFILE_FIELDS_IG_LOGIN = (
    "user_id,username,name,account_type,followers_count,follows_count,media_count"
)

ACCOUNT_FIELDS = [
    {"name": "id", "label": "Account ID", "type": "string", "description": "Instagram Business/Creator account ID"},
    {"name": "username", "label": "Username", "type": "string", "description": "@handle on Instagram"},
    {"name": "name", "label": "Name", "type": "string", "description": "Display name on profile"},
    {"name": "biography", "label": "Biography", "type": "string", "description": "Profile bio text"},
    {"name": "followers_count", "label": "Followers", "type": "integer", "description": "Total followers"},
    {"name": "follows_count", "label": "Following", "type": "integer", "description": "Accounts followed"},
    {"name": "media_count", "label": "Media Count", "type": "integer", "description": "Total posts/reels"},
    {"name": "profile_picture_url", "label": "Profile Picture", "type": "string", "description": "URL of profile image"},
    {"name": "website", "label": "Website", "type": "string", "description": "Link in bio"},
    {"name": "ig_id", "label": "Legacy IG ID", "type": "string", "description": "Legacy Instagram user ID"},
]

MEDIA_FIELDS = [
    {"name": "id", "label": "Media ID", "type": "string", "description": "Unique media identifier"},
    {"name": "caption", "label": "Caption", "type": "string", "description": "Post/reel caption text"},
    {"name": "media_type", "label": "Media Type", "type": "enum", "description": "IMAGE, VIDEO, or CAROUSEL_ALBUM"},
    {"name": "media_url", "label": "Media URL", "type": "string", "description": "Direct image or video URL"},
    {"name": "permalink", "label": "Permalink", "type": "string", "description": "instagram.com/p/... link"},
    {"name": "timestamp", "label": "Timestamp", "type": "datetime", "description": "Publish time"},
    {"name": "like_count", "label": "Likes", "type": "integer", "description": "Like count"},
    {"name": "comments_count", "label": "Comments", "type": "integer", "description": "Comment count"},
    {"name": "thumbnail_url", "label": "Thumbnail", "type": "string", "description": "Thumbnail for videos/reels"},
    {"name": "is_comment_enabled", "label": "Comments Enabled", "type": "boolean", "description": "Whether comments are on"},
    {"name": "media_product_type", "label": "Product Type", "type": "enum", "description": "FEED, REELS, STORY, etc."},
]

STORY_FIELDS = [
    {"name": "id", "label": "Story ID", "type": "string", "description": "Unique story media ID"},
    {"name": "media_type", "label": "Media Type", "type": "enum", "description": "IMAGE or VIDEO"},
    {"name": "media_url", "label": "Media URL", "type": "string", "description": "Story asset URL"},
    {"name": "timestamp", "label": "Timestamp", "type": "datetime", "description": "When story was posted"},
]

INSIGHTS_METRICS = [
    {"name": "impressions", "label": "Impressions", "type": "integer", "description": "Times content was seen"},
    {"name": "reach", "label": "Reach", "type": "integer", "description": "Unique accounts that saw content"},
    {"name": "profile_views", "label": "Profile Views", "type": "integer", "description": "Profile visits"},
    {"name": "website_clicks", "label": "Website Clicks", "type": "integer", "description": "Bio link clicks"},
    {"name": "follower_count", "label": "Follower Count", "type": "integer", "description": "Followers over time"},
    {"name": "email_contacts", "label": "Email Contacts", "type": "integer", "description": "Email button taps"},
    {"name": "phone_call_clicks", "label": "Phone Clicks", "type": "integer", "description": "Call button taps"},
    {"name": "accounts_engaged", "label": "Accounts Engaged", "type": "integer", "description": "Engaged accounts in period"},
]

METADATA_CATEGORIES = [
    {"id": "account", "label": "Account", "description": "Live Instagram Business/Creator profile"},
    {"id": "media", "label": "Media", "description": "Posts, reels, and carousels"},
    {"id": "stories", "label": "Stories", "description": "Active stories (24h window)"},
    {"id": "account_fields", "label": "Account Fields", "description": "Queryable fields on IG User object"},
    {"id": "media_fields", "label": "Media Fields", "description": "Queryable fields on Media object"},
    {"id": "story_fields", "label": "Story Fields", "description": "Queryable fields on Story object"},
    {"id": "insights_metrics", "label": "Insights Metrics", "description": "Instagram Insights metrics (instagram_manage_insights)"},
]

FIELD_CATALOG: dict[str, list] = {
    "account_fields": ACCOUNT_FIELDS,
    "media_fields": MEDIA_FIELDS,
    "story_fields": STORY_FIELDS,
    "insights_metrics": INSIGHTS_METRICS,
}

LIST_EDGES = {
    "media": "media",
    "stories": "stories",
}

LIST_FIELDS = {
    "media": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count,thumbnail_url,media_product_type",
    "stories": "id,media_type,media_url,timestamp",
}

ACCOUNT_PROFILE_FIELDS = (
    "id,username,name,biography,followers_count,follows_count,media_count,"
    "profile_picture_url,website,ig_id"
)


def _api_version() -> str:
    return settings.INSTAGRAM_API_VERSION or settings.FACEBOOK_API_VERSION or settings.META_API_VERSION or "v21.0"


def _access_token() -> str:
    if settings.INSTAGRAM_ACCESS_TOKEN.strip():
        return settings.INSTAGRAM_ACCESS_TOKEN.strip()
    if _has_explicit_instagram_config() and settings.FACEBOOK_PAGE_ACCESS_TOKEN.strip():
        return settings.FACEBOOK_PAGE_ACCESS_TOKEN.strip()
    return ""


def _has_explicit_instagram_config() -> bool:
    return bool(settings.INSTAGRAM_ACCESS_TOKEN.strip()) or bool(settings.INSTAGRAM_ACCOUNT_ID.strip())


def _is_demo_mode() -> bool:
    if not _has_explicit_instagram_config():
        return True
    return not bool(_access_token()) or (
        not settings.INSTAGRAM_ACCOUNT_ID.strip() and not settings.FACEBOOK_PAGE_ID.strip()
    )


def _check_live_config() -> None:
    if not _access_token():
        raise ConnectionError(
            "INSTAGRAM_ACCESS_TOKEN (or FACEBOOK_PAGE_ACCESS_TOKEN) is not set in .env. "
            "Generate a Page token with instagram_basic from Graph API Explorer."
        )
    if not settings.INSTAGRAM_ACCOUNT_ID.strip() and not settings.FACEBOOK_PAGE_ID.strip():
        raise ConnectionError(
            "INSTAGRAM_ACCOUNT_ID or FACEBOOK_PAGE_ID is not set in .env. "
            "Link Instagram to your Facebook Page, then set the IG account ID or Page ID."
        )


def _page_access_token() -> str:
    """Exchange a user token for a Page access token when FACEBOOK_PAGE_ID is set."""
    tok = _access_token()
    page_id = settings.FACEBOOK_PAGE_ID.strip()
    if not tok or not page_id:
        return tok
    try:
        data = requests.get(
            f"{GRAPH_BASE}/{_api_version()}/{page_id}",
            params={"fields": "access_token", "access_token": tok},
            timeout=30,
        ).json()
        return data.get("access_token") or tok
    except Exception:
        return tok


_api_mode_cache: str | None = None


def _detect_api_mode() -> str:
    """facebook_page (Graph API via Page) or instagram_login (graph.instagram.com token)."""
    global _api_mode_cache
    if _api_mode_cache:
        return _api_mode_cache

    tok = _access_token()
    if not tok:
        _api_mode_cache = "facebook_page"
        return _api_mode_cache

    try:
        resp = requests.get(
            f"{IG_LOGIN_BASE}/{_api_version()}/me",
            params={"fields": "user_id,username", "access_token": tok},
            timeout=30,
        )
        data = resp.json()
        if resp.status_code == 200 and ("user_id" in data or "username" in data):
            _api_mode_cache = "instagram_login"
            return _api_mode_cache
    except Exception:
        pass

    _api_mode_cache = "facebook_page"
    return _api_mode_cache


def _handle_api_error(data: dict) -> None:
    err = data.get("error", {})
    code = err.get("code", 0)
    msg = err.get("message", str(err))
    subcode = err.get("error_subcode", "")
    full = f"{msg} (code {code}, subcode {subcode})".strip()
    if code in (190, 102, 463):
        raise ConnectionError(f"Instagram authentication failed: {full}")
    if code in (10, 200, 294) or subcode == 33:
        raise PermissionError(
            f"Instagram access denied: {full}. "
            "Use an Instagram Login token from Ontio API Setup → Step 2 → Add account (test__poc), "
            "or a Page token with instagram_basic from Graph API Explorer."
        )
    raise RuntimeError(f"Instagram API error: {full}")


def _ig_login_get(path: str, params: dict | None = None) -> dict:
    _check_live_config()
    params = dict(params or {})
    params["access_token"] = _access_token()
    url = f"{IG_LOGIN_BASE}/{_api_version()}/{path.lstrip('/')}"
    resp = requests.get(url, params=params, timeout=30)
    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"Instagram API returned non-JSON [{resp.status_code}]: {resp.text[:300]}")
    if "error" in data:
        _handle_api_error(data)
    return data


def _normalize_ig_login_account(data: dict) -> dict:
    account = dict(data)
    if account.get("user_id") and not account.get("id"):
        account["id"] = account["user_id"]
    return account


def _graph_get(path: str, params: dict | None = None) -> dict:
    _check_live_config()
    params = dict(params or {})
    params["access_token"] = _page_access_token()
    url = f"{GRAPH_BASE}/{_api_version()}/{path.lstrip('/')}"
    resp = requests.get(url, params=params, timeout=30)
    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"Instagram API returned non-JSON [{resp.status_code}]: {resp.text[:300]}")

    if "error" in data:
        _handle_api_error(data)

    return data


def _resolve_account_id() -> str:
    explicit = settings.INSTAGRAM_ACCOUNT_ID.strip()
    if explicit:
        return explicit

    page_id = settings.FACEBOOK_PAGE_ID.strip()
    if not page_id:
        raise ConnectionError(
            "INSTAGRAM_ACCOUNT_ID is not set. Set it in .env or set FACEBOOK_PAGE_ID to auto-resolve."
        )

    data = _graph_get(page_id, {"fields": "instagram_business_account"})
    ig = data.get("instagram_business_account") or {}
    ig_id = ig.get("id", "")
    if not ig_id:
        raise ConnectionError(
            f"No Instagram Business account linked to Facebook Page {page_id}. "
            "Link Instagram to your Page in Instagram app → Settings → Account Centre."
        )
    return ig_id


def _get_account() -> dict:
    if _detect_api_mode() == "instagram_login":
        return _normalize_ig_login_account(
            _ig_login_get("me", {"fields": ACCOUNT_PROFILE_FIELDS_IG_LOGIN})
        )
    return _graph_get(_resolve_account_id(), {"fields": ACCOUNT_PROFILE_FIELDS})


def test_connection() -> dict:
    if _is_demo_mode():
        total_fields = sum(len(v) for v in FIELD_CATALOG.values())
        return {
            "connected": True,
            "mode": "demo",
            "message": (
                "Demo Mode — showing Instagram Graph API field schema. "
                "Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID in .env for live data."
            ),
            "categories_count": len(METADATA_CATEGORIES),
            "total_fields": total_fields,
            "api_version": _api_version(),
            "scopes_needed": "instagram_basic, pages_show_list",
        }

    _check_live_config()
    account = _get_account()
    ig_id = account.get("id") or settings.INSTAGRAM_ACCOUNT_ID.strip() or _resolve_account_id()
    api_mode = _detect_api_mode()

    media_sample = 0
    try:
        if api_mode == "instagram_login":
            media = _ig_login_get("me/media", {"fields": "id", "limit": 1})
        else:
            media = _graph_get(f"{ig_id}/media", {"fields": "id", "limit": 1})
        media_sample = len(media.get("data", []))
        if media.get("paging", {}).get("next"):
            media_sample = "1+"
    except Exception:
        media_sample = 0

    return {
        "connected": True,
        "mode": "live",
        "account_id": ig_id,
        "username": account.get("username", ""),
        "name": account.get("name", ""),
        "followers_count": account.get("followers_count", 0),
        "follows_count": account.get("follows_count", 0),
        "media_count": account.get("media_count", 0),
        "profile_url": f"https://instagram.com/{account.get('username', '')}" if account.get("username") else "",
        "media_sample": media_sample,
        "auth_method": "Instagram Login Token" if api_mode == "instagram_login" else "Page Access Token (instagram_basic)",
        "api_version": _api_version(),
        "content_type": "Organic Instagram (not ads)",
    }


def list_categories() -> list[dict]:
    counts: dict[str, Any] = {cat_id: len(fields) for cat_id, fields in FIELD_CATALOG.items()}

    if _is_demo_mode():
        counts["account"] = 1
        counts["media"] = 0
        counts["stories"] = 0
        return [{**cat, "items_count": counts.get(cat["id"], 0)} for cat in METADATA_CATEGORIES]

    _check_live_config()
    counts["account"] = 1
    api_mode = _detect_api_mode()
    ig_id = settings.INSTAGRAM_ACCOUNT_ID.strip() or (_resolve_account_id() if api_mode == "facebook_page" else "")

    for cat_id, edge in LIST_EDGES.items():
        try:
            if api_mode == "instagram_login" and edge == "media":
                data = _ig_login_get("me/media", {"fields": "id", "limit": 50})
            elif api_mode == "instagram_login":
                counts[cat_id] = 0
                continue
            else:
                data = _graph_get(f"{ig_id}/{edge}", {"fields": "id", "limit": 50})
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
        if category_id in ("account", "media", "stories"):
            return {
                "category": category_id,
                "total": 0,
                "items": [],
                "mode": "demo",
                "message": "Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID in .env to load live objects.",
            }
        raise LookupError(
            f"Category '{category_id}' not found. Available: {[c['id'] for c in METADATA_CATEGORIES]}"
        )

    _check_live_config()
    api_mode = _detect_api_mode()

    if category_id == "account":
        account = _get_account()
        username = account.get("username", "")
        ig_id = account.get("id", settings.INSTAGRAM_ACCOUNT_ID.strip())
        return {
            "category": category_id,
            "total": 1,
            "items": [
                {
                    "name": ig_id,
                    "label": f"@{username}" if username else account.get("name", "Instagram Account"),
                    "description": (
                        f"{account.get('followers_count', 0)} followers · "
                        f"{account.get('media_count', 0)} posts"
                    ),
                    "raw": account,
                }
            ],
            "mode": "live",
        }

    if category_id in LIST_EDGES:
        edge = LIST_EDGES[category_id]
        fields = LIST_FIELDS[category_id]
        if api_mode == "instagram_login" and edge == "media":
            data = _ig_login_get("me/media", {"fields": fields, "limit": 25})
        elif api_mode == "instagram_login":
            return {"category": category_id, "total": 0, "items": [], "mode": "live"}
        else:
            ig_id = _resolve_account_id()
            data = _graph_get(f"{ig_id}/{edge}", {"fields": fields, "limit": 25})
        items = [
            {
                "name": row.get("id", ""),
                "label": _row_label(row, category_id),
                "description": _summarize_row(row, category_id),
                "raw": row,
            }
            for row in data.get("data", [])
        ]
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
        raise LookupError("Live object detail requires INSTAGRAM_ACCESS_TOKEN in .env.")

    _check_live_config()

    if category_id == "account":
        result = list_items("account")
        return {**result["items"][0], "category": category_id, "mode": "live"}

    if category_id in LIST_EDGES:
        fields = LIST_FIELDS[category_id]
        api_mode = _detect_api_mode()
        if api_mode == "instagram_login" and category_id == "media":
            obj = _ig_login_get(item_id, {"fields": fields})
        else:
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
    if category_id == "media":
        caption = (row.get("caption") or "").strip()
        if caption:
            return (caption[:60] + "…") if len(caption) > 60 else caption
        return row.get("media_type", row.get("id", ""))
    if category_id == "stories":
        return f"{row.get('media_type', 'Story')} · {row.get('id', '')[:12]}"
    return row.get("id", "")


def _summarize_row(row: dict, category_id: str) -> str:
    parts = []
    if row.get("timestamp"):
        parts.append(str(row["timestamp"])[:10])
    if category_id == "media":
        if row.get("media_type"):
            parts.append(row["media_type"])
        if row.get("media_product_type"):
            parts.append(row["media_product_type"])
        if row.get("like_count") is not None:
            parts.append(f"{row['like_count']} likes")
        if row.get("comments_count") is not None:
            parts.append(f"{row['comments_count']} comments")
    if category_id == "stories" and row.get("media_type"):
        parts.append(row["media_type"])
    return " · ".join(parts) if parts else category_id.rstrip("s")

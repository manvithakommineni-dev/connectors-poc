"""
YouTube Data API v3 connectivity and metadata retrieval service.

How YouTube exposes metadata:
  YouTube Data API v3 (Google):
    GET /youtube/v3/channels          → Channel info + statistics
    GET /youtube/v3/videos          → Video metadata + stats
    GET /youtube/v3/playlists       → Playlists for a channel
    GET /youtube/v3/playlistItems   → Videos in a playlist
    GET /youtube/v3/search          → Search videos on channel

  YouTube Analytics API (separate, OAuth yt-analytics.readonly):
    Reports for views, watch time, subscribers, revenue

  YouTube concept equivalents:
    Salesforce SObject  → Channel / Video / Playlist
    Salesforce Field    → part= snippet, statistics, contentDetails fields
    GA4 Dimension       → Video snippet field (title, tags, categoryId)

  Authentication (FREE):
    1. Google Cloud project → enable YouTube Data API v3
    2. OAuth 2.0 credentials → access token with youtube.readonly scope
    3. Optional: API key for public channel reads only
    Required for live: YOUTUBE_ACCESS_TOKEN, YOUTUBE_CHANNEL_ID

  Demo mode (no credentials):
    Returns real YouTube Data API v3 field schema catalogs.
"""

import logging
from typing import Any

import requests
from core.config import settings

logger = logging.getLogger(__name__)

API_BASE = "https://www.googleapis.com/youtube/v3"

CHANNEL_FIELDS = [
    {"name": "id", "label": "Channel ID", "type": "string", "description": "Unique channel identifier (UC...)"},
    {"name": "title", "label": "Title", "type": "string", "description": "Channel title from snippet"},
    {"name": "description", "label": "Description", "type": "string", "description": "Channel description"},
    {"name": "customUrl", "label": "Custom URL", "type": "string", "description": "youtube.com/@handle"},
    {"name": "publishedAt", "label": "Published At", "type": "datetime", "description": "Channel creation date"},
    {"name": "country", "label": "Country", "type": "string", "description": "Channel country code"},
    {"name": "viewCount", "label": "View Count", "type": "integer", "description": "Total channel views"},
    {"name": "subscriberCount", "label": "Subscribers", "type": "integer", "description": "Subscriber count (may be hidden)"},
    {"name": "videoCount", "label": "Video Count", "type": "integer", "description": "Total public videos"},
    {"name": "uploadsPlaylistId", "label": "Uploads Playlist", "type": "string", "description": "Playlist ID for all uploads"},
]

VIDEO_FIELDS = [
    {"name": "id", "label": "Video ID", "type": "string", "description": "Unique video identifier"},
    {"name": "title", "label": "Title", "type": "string", "description": "Video title"},
    {"name": "description", "label": "Description", "type": "string", "description": "Video description"},
    {"name": "publishedAt", "label": "Published At", "type": "datetime", "description": "Upload/publish timestamp"},
    {"name": "channelId", "label": "Channel ID", "type": "string", "description": "Owning channel"},
    {"name": "tags", "label": "Tags", "type": "array", "description": "Video tags"},
    {"name": "categoryId", "label": "Category ID", "type": "string", "description": "YouTube video category"},
    {"name": "duration", "label": "Duration", "type": "string", "description": "ISO 8601 duration from contentDetails"},
    {"name": "definition", "label": "Definition", "type": "enum", "description": "hd or sd"},
    {"name": "viewCount", "label": "Views", "type": "integer", "description": "View count from statistics"},
    {"name": "likeCount", "label": "Likes", "type": "integer", "description": "Like count"},
    {"name": "commentCount", "label": "Comments", "type": "integer", "description": "Comment count"},
    {"name": "privacyStatus", "label": "Privacy", "type": "enum", "description": "public, private, unlisted"},
]

PLAYLIST_FIELDS = [
    {"name": "id", "label": "Playlist ID", "type": "string", "description": "Unique playlist identifier"},
    {"name": "title", "label": "Title", "type": "string", "description": "Playlist title"},
    {"name": "description", "label": "Description", "type": "string", "description": "Playlist description"},
    {"name": "publishedAt", "label": "Published At", "type": "datetime", "description": "Playlist creation time"},
    {"name": "channelId", "label": "Channel ID", "type": "string", "description": "Owning channel"},
    {"name": "itemCount", "label": "Item Count", "type": "integer", "description": "Number of videos in playlist"},
    {"name": "privacyStatus", "label": "Privacy", "type": "enum", "description": "public, private, unlisted"},
]

ANALYTICS_METRICS = [
    {"name": "views", "label": "Views", "type": "integer", "description": "YouTube Analytics — video views"},
    {"name": "estimatedMinutesWatched", "label": "Watch Time (minutes)", "type": "float", "description": "Estimated minutes watched"},
    {"name": "averageViewDuration", "label": "Avg View Duration", "type": "float", "description": "Average view duration in seconds"},
    {"name": "subscribersGained", "label": "Subscribers Gained", "type": "integer", "description": "New subscribers in period"},
    {"name": "subscribersLost", "label": "Subscribers Lost", "type": "integer", "description": "Unsubscribes in period"},
    {"name": "likes", "label": "Likes", "type": "integer", "description": "Likes in reporting period"},
    {"name": "comments", "label": "Comments", "type": "integer", "description": "Comments in reporting period"},
    {"name": "shares", "label": "Shares", "type": "integer", "description": "Shares in reporting period"},
    {"name": "impressions", "label": "Impressions", "type": "integer", "description": "Thumbnail impressions"},
    {"name": "impressionClickThroughRate", "label": "CTR", "type": "float", "description": "Impression click-through rate"},
    {"name": "estimatedRevenue", "label": "Revenue", "type": "float", "description": "Estimated revenue (monetized channels)"},
]

METADATA_CATEGORIES = [
    {"id": "channel", "label": "Channel", "description": "Live channel details from Data API"},
    {"id": "videos", "label": "Videos", "description": "Videos on the channel"},
    {"id": "playlists", "label": "Playlists", "description": "Channel playlists"},
    {"id": "playlist_items", "label": "Playlist Items", "description": "Videos inside the uploads playlist"},
    {"id": "channel_fields", "label": "Channel Fields", "description": "Queryable channel attributes (snippet, statistics)"},
    {"id": "video_fields", "label": "Video Fields", "description": "Queryable video attributes"},
    {"id": "playlist_fields", "label": "Playlist Fields", "description": "Queryable playlist attributes"},
    {"id": "analytics_metrics", "label": "Analytics Metrics", "description": "YouTube Analytics API metrics (yt-analytics.readonly)"},
]

FIELD_CATALOG: dict[str, list] = {
    "channel_fields": CHANNEL_FIELDS,
    "video_fields": VIDEO_FIELDS,
    "playlist_fields": PLAYLIST_FIELDS,
    "analytics_metrics": ANALYTICS_METRICS,
}

LIST_ENDPOINTS = {
    "videos": "videos",
    "playlists": "playlists",
}


def _is_demo_mode() -> bool:
    return not bool(settings.YOUTUBE_ACCESS_TOKEN) and not bool(settings.YOUTUBE_API_KEY)


def _check_live_config() -> None:
    if not settings.YOUTUBE_ACCESS_TOKEN and not settings.YOUTUBE_API_KEY:
        raise ConnectionError(
            "YOUTUBE_ACCESS_TOKEN or YOUTUBE_API_KEY is not set in .env. "
            "Enable YouTube Data API v3 in Google Cloud and create OAuth credentials."
        )
    if not settings.YOUTUBE_CHANNEL_ID:
        raise ConnectionError(
            "YOUTUBE_CHANNEL_ID is not set in .env. "
            "Find it in YouTube Studio → Settings → Channel → Advanced settings."
        )


def _channel_id() -> str:
    return settings.YOUTUBE_CHANNEL_ID.strip()


def _auth_params() -> dict:
    if settings.YOUTUBE_ACCESS_TOKEN:
        return {}
    return {"key": settings.YOUTUBE_API_KEY}


def _headers() -> dict:
    if settings.YOUTUBE_ACCESS_TOKEN:
        return {"Authorization": f"Bearer {settings.YOUTUBE_ACCESS_TOKEN}"}
    return {}


def _api_get(path: str, params: dict | None = None) -> dict:
    _check_live_config()
    params = dict(params or {})
    params.update(_auth_params())
    url = f"{API_BASE}/{path.lstrip('/')}"
    resp = requests.get(url, headers=_headers(), params=params, timeout=30)
    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"YouTube API returned non-JSON [{resp.status_code}]: {resp.text[:300]}")

    if resp.status_code == 401:
        raise ConnectionError("YouTube authentication failed (401). Check YOUTUBE_ACCESS_TOKEN in .env.")
    if resp.status_code == 403:
        err = data.get("error", {})
        msg = err.get("message", str(data))
        raise PermissionError(
            f"YouTube access denied: {msg}. Enable YouTube Data API v3 and check OAuth scopes (youtube.readonly)."
        )
    if resp.status_code >= 400:
        err = data.get("error", {})
        msg = err.get("message", str(data))
        raise RuntimeError(f"YouTube API error [{resp.status_code}]: {msg}")

    return data


def _get_channel() -> dict:
    data = _api_get(
        "channels",
        {
            "part": "snippet,contentDetails,statistics",
            "id": _channel_id(),
        },
    )
    items = data.get("items", [])
    if not items:
        raise LookupError(f"Channel not found: {_channel_id()}")
    return items[0]


def test_connection() -> dict:
    if _is_demo_mode():
        total_fields = sum(len(v) for v in FIELD_CATALOG.values())
        return {
            "connected": True,
            "mode": "demo",
            "message": (
                "Demo Mode — showing YouTube Data API v3 field schema. "
                "Set YOUTUBE_ACCESS_TOKEN and YOUTUBE_CHANNEL_ID in .env for live data."
            ),
            "categories_count": len(METADATA_CATEGORIES),
            "total_fields": total_fields,
            "api_version": "v3",
            "scopes_needed": "https://www.googleapis.com/auth/youtube.readonly",
        }

    _check_live_config()
    ch = _get_channel()
    snippet = ch.get("snippet", {})
    stats = ch.get("statistics", {})

    return {
        "connected": True,
        "mode": "live",
        "channel_id": ch.get("id", _channel_id()),
        "channel_title": snippet.get("title", ""),
        "custom_url": snippet.get("customUrl", ""),
        "subscriber_count": stats.get("subscriberCount", "hidden"),
        "video_count": stats.get("videoCount", "0"),
        "view_count": stats.get("viewCount", "0"),
        "auth_method": "OAuth Bearer" if settings.YOUTUBE_ACCESS_TOKEN else "API Key",
        "api_version": "v3",
    }


def list_categories() -> list[dict]:
    counts: dict[str, Any] = {cat_id: len(fields) for cat_id, fields in FIELD_CATALOG.items()}

    if _is_demo_mode():
        counts["channel"] = 1
        counts["videos"] = 0
        counts["playlists"] = 0
        counts["playlist_items"] = 0
        return [{**cat, "items_count": counts.get(cat["id"], 0)} for cat in METADATA_CATEGORIES]

    _check_live_config()
    ch = _get_channel()
    uploads_id = ch.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads", "")

    counts["channel"] = 1

    try:
        pl = _api_get("playlists", {"part": "id", "channelId": _channel_id(), "maxResults": 50})
        counts["playlists"] = len(pl.get("items", []))
    except Exception:
        counts["playlists"] = 0

    try:
        search = _api_get(
            "search",
            {"part": "id", "channelId": _channel_id(), "type": "video", "maxResults": 50, "order": "date"},
        )
        counts["videos"] = len(search.get("items", []))
    except Exception:
        counts["videos"] = 0

    try:
        if uploads_id:
            items = _api_get("playlistItems", {"part": "id", "playlistId": uploads_id, "maxResults": 50})
            counts["playlist_items"] = len(items.get("items", []))
        else:
            counts["playlist_items"] = 0
    except Exception:
        counts["playlist_items"] = 0

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
        if category_id in ("channel", "videos", "playlists", "playlist_items"):
            return {
                "category": category_id,
                "total": 0,
                "items": [],
                "mode": "demo",
                "message": "Set YOUTUBE_ACCESS_TOKEN and YOUTUBE_CHANNEL_ID in .env to load live objects.",
            }
        raise LookupError(
            f"Category '{category_id}' not found. Available: {[c['id'] for c in METADATA_CATEGORIES]}"
        )

    _check_live_config()

    if category_id == "channel":
        ch = _get_channel()
        snippet = ch.get("snippet", {})
        stats = ch.get("statistics", {})
        return {
            "category": category_id,
            "total": 1,
            "items": [
                {
                    "name": ch.get("id", ""),
                    "label": snippet.get("title", "Channel"),
                    "description": f"{stats.get('videoCount', 0)} videos · {stats.get('viewCount', 0)} views",
                    "raw": ch,
                }
            ],
            "mode": "live",
        }

    if category_id == "videos":
        search = _api_get(
            "search",
            {"part": "snippet", "channelId": _channel_id(), "type": "video", "maxResults": 25, "order": "date"},
        )
        video_ids = [i["id"]["videoId"] for i in search.get("items", []) if i.get("id", {}).get("videoId")]
        details: dict[str, dict] = {}
        if video_ids:
            vdata = _api_get(
                "videos",
                {"part": "snippet,statistics,contentDetails", "id": ",".join(video_ids)},
            )
            details = {v["id"]: v for v in vdata.get("items", [])}

        items = []
        for row in search.get("items", []):
            vid = row.get("id", {}).get("videoId", "")
            snip = row.get("snippet", {})
            detail = details.get(vid, {})
            items.append(
                {
                    "name": vid,
                    "label": snip.get("title", vid),
                    "description": snip.get("publishedAt", "")[:10],
                    "raw": detail or row,
                }
            )
        return {"category": category_id, "total": len(items), "items": items, "mode": "live"}

    if category_id == "playlists":
        data = _api_get(
            "playlists",
            {"part": "snippet,contentDetails", "channelId": _channel_id(), "maxResults": 25},
        )
        items = [
            {
                "name": row.get("id", ""),
                "label": row.get("snippet", {}).get("title", row.get("id", "")),
                "description": f"{row.get('contentDetails', {}).get('itemCount', 0)} items",
                "raw": row,
            }
            for row in data.get("items", [])
        ]
        return {"category": category_id, "total": len(items), "items": items, "mode": "live"}

    if category_id == "playlist_items":
        ch = _get_channel()
        uploads_id = ch.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads", "")
        if not uploads_id:
            return {"category": category_id, "total": 0, "items": [], "mode": "live"}
        data = _api_get(
            "playlistItems",
            {"part": "snippet,contentDetails", "playlistId": uploads_id, "maxResults": 25},
        )
        items = [
            {
                "name": row.get("snippet", {}).get("resourceId", {}).get("videoId", row.get("id", "")),
                "label": row.get("snippet", {}).get("title", ""),
                "description": row.get("snippet", {}).get("publishedAt", "")[:10],
                "raw": row,
            }
            for row in data.get("items", [])
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
        raise LookupError("Live object detail requires YOUTUBE_ACCESS_TOKEN in .env.")

    _check_live_config()

    if category_id == "channel":
        result = list_items("channel")
        return {**result["items"][0], "category": category_id, "mode": "live"}

    if category_id == "videos":
        data = _api_get("videos", {"part": "snippet,statistics,contentDetails,status", "id": item_id})
        items = data.get("items", [])
        if not items:
            raise LookupError(f"Video '{item_id}' not found.")
        obj = items[0]
        return {
            "name": obj.get("id", item_id),
            "label": obj.get("snippet", {}).get("title", item_id),
            "category": category_id,
            "fields": obj,
            "mode": "live",
        }

    if category_id == "playlists":
        data = _api_get("playlists", {"part": "snippet,contentDetails,status", "id": item_id})
        items = data.get("items", [])
        if not items:
            raise LookupError(f"Playlist '{item_id}' not found.")
        obj = items[0]
        return {
            "name": obj.get("id", item_id),
            "label": obj.get("snippet", {}).get("title", item_id),
            "category": category_id,
            "fields": obj,
            "mode": "live",
        }

    if category_id == "playlist_items":
        data = _api_get("playlistItems", {"part": "snippet,contentDetails,status", "id": item_id})
        items = data.get("items", [])
        if not items:
            raise LookupError(f"Playlist item '{item_id}' not found.")
        obj = items[0]
        return {
            "name": item_id,
            "label": obj.get("snippet", {}).get("title", item_id),
            "category": category_id,
            "fields": obj,
            "mode": "live",
        }

    raise LookupError(f"Cannot get detail for category '{category_id}'.")

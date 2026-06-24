"""
Pinterest API v5 connectivity and metadata retrieval service.

Pinterest Ads + organic content share one API (v5):
  Ads (ads_read scope):
    GET /ad_accounts
    GET /ad_accounts/{id}
    GET /ad_accounts/{id}/campaigns
    GET /ad_accounts/{id}/ad_groups
    GET /ad_accounts/{id}/ads
    GET /ad_accounts/{id}/analytics

  Organic (boards:read, pins:read scopes):
    GET /boards
    GET /pins

  Pinterest concept equivalents:
    Salesforce SObject  → Campaign / Ad Group / Ad / Board / Pin
    Salesforce Field    → API attribute on each object
    Meta Ad Set         → Pinterest Ad Group

Authentication:
  OAuth 2.0 Bearer token with ads_read (+ boards:read, pins:read for organic).
  Required for live: PINTEREST_ACCESS_TOKEN, PINTEREST_AD_ACCOUNT_ID

Demo mode (no credentials):
  Returns real Pinterest API v5 field schema catalogs.
  Live object lists empty until credentials are set.

Setup (free — Trial access):
  1. Pinterest Business account at pinterest.com/business
  2. developers.pinterest.com → Connect app → Trial access
  3. OAuth or trial token with ads_read scope
"""

import logging
from typing import Any

import requests
from core.config import settings

logger = logging.getLogger(__name__)

API_BASE = "https://api.pinterest.com/v5"

CAMPAIGN_FIELDS = [
    {"name": "id", "label": "Campaign ID", "type": "string", "description": "Unique campaign identifier"},
    {"name": "ad_account_id", "label": "Ad Account ID", "type": "string", "description": "Parent ad account"},
    {"name": "name", "label": "Name", "type": "string", "description": "Campaign name"},
    {"name": "status", "label": "Status", "type": "enum", "description": "ACTIVE, PAUSED, ARCHIVED"},
    {"name": "objective_type", "label": "Objective", "type": "enum", "description": "AWARENESS, CONSIDERATION, VIDEO_VIEW, WEB_CONVERSION, CATALOG_SALES, etc."},
    {"name": "lifetime_spend_cap", "label": "Lifetime Spend Cap", "type": "integer", "description": "Lifetime budget cap in micro currency"},
    {"name": "daily_spend_cap", "label": "Daily Spend Cap", "type": "integer", "description": "Daily budget cap in micro currency"},
    {"name": "order_line_id", "label": "Order Line ID", "type": "string", "description": "IO / order line reference"},
    {"name": "tracking_urls", "label": "Tracking URLs", "type": "object", "description": "Impression / click / engagement tracking"},
    {"name": "start_time", "label": "Start Time", "type": "integer", "description": "Campaign start (Unix timestamp)"},
    {"name": "end_time", "label": "End Time", "type": "integer", "description": "Campaign end (Unix timestamp)"},
    {"name": "summary_status", "label": "Summary Status", "type": "enum", "description": "RUNNING, PAUSED, NOT_STARTED, COMPLETED, etc."},
    {"name": "is_campaign_budget_optimization", "label": "CBO", "type": "boolean", "description": "Campaign budget optimization enabled"},
    {"name": "is_flexible_daily_budgets", "label": "Flexible Daily Budgets", "type": "boolean", "description": "Flexible daily budget pacing"},
]

AD_GROUP_FIELDS = [
    {"name": "id", "label": "Ad Group ID", "type": "string", "description": "Unique ad group identifier"},
    {"name": "campaign_id", "label": "Campaign ID", "type": "string", "description": "Parent campaign"},
    {"name": "name", "label": "Name", "type": "string", "description": "Ad group name"},
    {"name": "status", "label": "Status", "type": "enum", "description": "ACTIVE, PAUSED, ARCHIVED"},
    {"name": "budget_in_micro_currency", "label": "Budget", "type": "integer", "description": "Budget in micro currency units"},
    {"name": "bid_in_micro_currency", "label": "Bid", "type": "integer", "description": "Bid in micro currency units"},
    {"name": "budget_type", "label": "Budget Type", "type": "enum", "description": "DAILY or LIFETIME"},
    {"name": "start_time", "label": "Start Time", "type": "integer", "description": "Ad group start timestamp"},
    {"name": "end_time", "label": "End Time", "type": "integer", "description": "Ad group end timestamp"},
    {"name": "targeting_spec", "label": "Targeting", "type": "object", "description": "Audience, geo, interest, keyword targeting"},
    {"name": "placement_group", "label": "Placement", "type": "enum", "description": "ALL, SEARCH, BROWSE, OTHER"},
    {"name": "billable_event", "label": "Billable Event", "type": "enum", "description": "CLICKTHROUGH, IMPRESSION, VIDEO_V_50_MRC"},
    {"name": "bid_strategy_type", "label": "Bid Strategy", "type": "enum", "description": "AUTOMATIC_BID, MAX_BID, TARGET_AVG"},
    {"name": "pacing_delivery_type", "label": "Pacing", "type": "enum", "description": "STANDARD or ACCELERATED"},
    {"name": "lifetime_frequency_cap", "label": "Frequency Cap", "type": "integer", "description": "Max impressions per user"},
]

AD_FIELDS = [
    {"name": "id", "label": "Ad ID", "type": "string", "description": "Unique ad identifier"},
    {"name": "ad_group_id", "label": "Ad Group ID", "type": "string", "description": "Parent ad group"},
    {"name": "campaign_id", "label": "Campaign ID", "type": "string", "description": "Parent campaign"},
    {"name": "pin_id", "label": "Pin ID", "type": "string", "description": "Promoted Pin ID"},
    {"name": "name", "label": "Name", "type": "string", "description": "Ad name"},
    {"name": "status", "label": "Status", "type": "enum", "description": "ACTIVE, PAUSED, ARCHIVED"},
    {"name": "creative_type", "label": "Creative Type", "type": "enum", "description": "REGULAR, VIDEO, SHOPPING, CAROUSEL, etc."},
    {"name": "destination_url", "label": "Destination URL", "type": "string", "description": "Click-through landing page"},
    {"name": "tracking_urls", "label": "Tracking URLs", "type": "object", "description": "Ad-level tracking configuration"},
    {"name": "review_status", "label": "Review Status", "type": "enum", "description": "APPROVED, PENDING, REJECTED"},
    {"name": "summary_status", "label": "Summary Status", "type": "enum", "description": "Overall delivery status"},
]

ANALYTICS_METRICS = [
    {"name": "IMPRESSION", "label": "Impressions", "type": "integer", "description": "Times ad was shown"},
    {"name": "CLICKTHROUGH", "label": "Clicks", "type": "integer", "description": "Outbound clicks"},
    {"name": "SPEND_IN_MICRO_DOLLAR", "label": "Spend", "type": "integer", "description": "Amount spent in micro dollars"},
    {"name": "OUTBOUND_CLICK", "label": "Outbound Clicks", "type": "integer", "description": "Clicks leaving Pinterest"},
    {"name": "TOTAL_CONVERSIONS", "label": "Conversions", "type": "integer", "description": "Total conversion events"},
    {"name": "TOTAL_CLICKTHROUGH_CONVERSIONS", "label": "Click Conversions", "type": "integer", "description": "Conversions from clicks"},
    {"name": "TOTAL_VIEWTHROUGH_CONVERSIONS", "label": "View Conversions", "type": "integer", "description": "View-through conversions"},
    {"name": "CTR", "label": "CTR", "type": "float", "description": "Click-through rate"},
    {"name": "ECPC_IN_MICRO_DOLLAR", "label": "eCPC", "type": "integer", "description": "Effective cost per click (micro dollars)"},
    {"name": "ENGAGEMENT", "label": "Engagements", "type": "integer", "description": "Pin engagements (closeups, saves, etc.)"},
    {"name": "VIDEO_MRC_VIEWS", "label": "Video Views", "type": "integer", "description": "MRC video views"},
    {"name": "VIDEO_V_50_MRC", "label": "Video 50% Views", "type": "integer", "description": "50% video completion views"},
    {"name": "REPIN", "label": "Saves", "type": "integer", "description": "Pin saves / repins"},
]

BOARD_FIELDS = [
    {"name": "id", "label": "Board ID", "type": "string", "description": "Unique board identifier"},
    {"name": "name", "label": "Name", "type": "string", "description": "Board name"},
    {"name": "description", "label": "Description", "type": "string", "description": "Board description"},
    {"name": "privacy", "label": "Privacy", "type": "enum", "description": "PUBLIC, PROTECTED, SECRET"},
    {"name": "pin_count", "label": "Pin Count", "type": "integer", "description": "Number of pins on board"},
    {"name": "follower_count", "label": "Followers", "type": "integer", "description": "Board follower count"},
    {"name": "created_at", "label": "Created At", "type": "datetime", "description": "Board creation time"},
    {"name": "board_pins_modified_at", "label": "Pins Modified", "type": "datetime", "description": "Last pin activity"},
]

PIN_FIELDS = [
    {"name": "id", "label": "Pin ID", "type": "string", "description": "Unique pin identifier"},
    {"name": "title", "label": "Title", "type": "string", "description": "Pin title"},
    {"name": "description", "label": "Description", "type": "string", "description": "Pin description"},
    {"name": "link", "label": "Link", "type": "string", "description": "Destination URL"},
    {"name": "board_id", "label": "Board ID", "type": "string", "description": "Parent board"},
    {"name": "media_type", "label": "Media Type", "type": "enum", "description": "image, video, multiple_images"},
    {"name": "creative_type", "label": "Creative Type", "type": "enum", "description": "REGULAR, VIDEO, SHOPPING, etc."},
    {"name": "created_at", "label": "Created At", "type": "datetime", "description": "Pin creation time"},
    {"name": "is_standard", "label": "Standard Pin", "type": "boolean", "description": "Standard vs idea pin"},
]

METADATA_CATEGORIES = [
    {"id": "account", "label": "Ad Account", "description": "Pinterest ad account details"},
    {"id": "campaigns", "label": "Campaigns", "description": "Live ad campaigns"},
    {"id": "ad_groups", "label": "Ad Groups", "description": "Targeting and budget groups (like Meta ad sets)"},
    {"id": "ads", "label": "Ads", "description": "Promoted pins / ads"},
    {"id": "boards", "label": "Boards", "description": "Organic boards (org_read scope)"},
    {"id": "pins", "label": "Pins", "description": "Organic pins (pins:read scope)"},
    {"id": "campaign_fields", "label": "Campaign Fields", "description": "Queryable fields on Campaign object"},
    {"id": "ad_group_fields", "label": "Ad Group Fields", "description": "Queryable fields on Ad Group object"},
    {"id": "ad_fields", "label": "Ad Fields", "description": "Queryable fields on Ad object"},
    {"id": "analytics_metrics", "label": "Analytics Metrics", "description": "Ads reporting metrics"},
    {"id": "board_fields", "label": "Board Fields", "description": "Organic board object fields"},
    {"id": "pin_fields", "label": "Pin Fields", "description": "Organic pin object fields"},
]

FIELD_CATALOG: dict[str, list] = {
    "campaign_fields": CAMPAIGN_FIELDS,
    "ad_group_fields": AD_GROUP_FIELDS,
    "ad_fields": AD_FIELDS,
    "analytics_metrics": ANALYTICS_METRICS,
    "board_fields": BOARD_FIELDS,
    "pin_fields": PIN_FIELDS,
}

ADS_LIST_ENDPOINTS = {
    "campaigns": "campaigns",
    "ad_groups": "ad_groups",
    "ads": "ads",
}

ORGANIC_LIST_ENDPOINTS = {
    "boards": "boards",
    "pins": "pins",
}


def _is_demo_mode() -> bool:
    return not bool(settings.PINTEREST_ACCESS_TOKEN)


def _check_live_config() -> None:
    if not settings.PINTEREST_ACCESS_TOKEN:
        raise ConnectionError(
            "PINTEREST_ACCESS_TOKEN is not set in .env. "
            "Get a token from developers.pinterest.com → My apps → OAuth or trial token (ads_read scope)."
        )
    if not settings.PINTEREST_AD_ACCOUNT_ID:
        raise ConnectionError(
            "PINTEREST_AD_ACCOUNT_ID is not set in .env. "
            "Find it in Pinterest Ads Manager or via GET /ad_accounts after OAuth."
        )


def _ad_account_path() -> str:
    return f"ad_accounts/{settings.PINTEREST_AD_ACCOUNT_ID.strip()}"


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.PINTEREST_ACCESS_TOKEN}"}


def _api_get(path: str, params: dict | None = None) -> dict:
    _check_live_config()
    url = f"{API_BASE}/{path.lstrip('/')}"
    resp = requests.get(url, headers=_headers(), params=params or {}, timeout=30)
    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"Pinterest API returned non-JSON [{resp.status_code}]: {resp.text[:300]}")

    if resp.status_code == 401:
        raise ConnectionError(
            "Pinterest authentication failed (401). Check PINTEREST_ACCESS_TOKEN in .env."
        )
    if resp.status_code == 403:
        raise PermissionError(
            f"Pinterest access denied: {data.get('message', data)}. "
            "Ensure token has ads_read (and boards:read / pins:read for organic)."
        )
    if resp.status_code >= 400:
        msg = data.get("message", str(data))
        raise RuntimeError(f"Pinterest API error [{resp.status_code}]: {msg}")

    return data


def test_connection() -> dict:
    if _is_demo_mode():
        total_fields = sum(len(v) for v in FIELD_CATALOG.values())
        return {
            "connected": True,
            "mode": "demo",
            "message": (
                "Demo Mode — showing Pinterest API v5 field schema. "
                "Set PINTEREST_ACCESS_TOKEN and PINTEREST_AD_ACCOUNT_ID in .env for live data."
            ),
            "categories_count": len(METADATA_CATEGORIES),
            "total_fields": total_fields,
            "api_version": "v5",
            "scopes_needed": "ads_read, boards:read, pins:read",
        }

    _check_live_config()
    acct = _api_get(_ad_account_path())
    campaigns = _api_get(f"{_ad_account_path()}/campaigns", {"page_size": 1})
    items = campaigns.get("items", [])

    return {
        "connected": True,
        "mode": "live",
        "ad_account_id": acct.get("id", settings.PINTEREST_AD_ACCOUNT_ID),
        "ad_account_name": acct.get("name", ""),
        "account_status": acct.get("status"),
        "currency": acct.get("currency", ""),
        "country": acct.get("country", ""),
        "campaigns_sample": len(items),
        "platforms": "Pinterest Ads + Organic (API v5)",
        "auth_method": "OAuth Bearer (ads_read)",
        "api_version": "v5",
    }


def list_categories() -> list[dict]:
    counts: dict[str, Any] = {cat_id: len(fields) for cat_id, fields in FIELD_CATALOG.items()}

    if _is_demo_mode():
        counts["account"] = 1
        for key in ADS_LIST_ENDPOINTS:
            counts[key] = 0
        for key in ORGANIC_LIST_ENDPOINTS:
            counts[key] = 0
        return [{**cat, "items_count": counts.get(cat["id"], 0)} for cat in METADATA_CATEGORIES]

    _check_live_config()

    for cat_id, edge in ADS_LIST_ENDPOINTS.items():
        try:
            data = _api_get(f"{_ad_account_path()}/{edge}", {"page_size": 100})
            items = data.get("items", [])
            counts[cat_id] = len(items)
            if data.get("bookmark") and len(items) == 100:
                counts[cat_id] = f"{len(items)}+"
        except Exception:
            counts[cat_id] = 0

    for cat_id, edge in ORGANIC_LIST_ENDPOINTS.items():
        try:
            data = _api_get(edge, {"page_size": 25})
            items = data.get("items", [])
            counts[cat_id] = len(items)
        except Exception:
            counts[cat_id] = 0

    counts["account"] = 1
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
        if category_id in ("account", *ADS_LIST_ENDPOINTS, *ORGANIC_LIST_ENDPOINTS):
            return {
                "category": category_id,
                "total": 0,
                "items": [],
                "mode": "demo",
                "message": "Set PINTEREST_ACCESS_TOKEN in .env to load live objects.",
            }
        raise LookupError(
            f"Category '{category_id}' not found. Available: {[c['id'] for c in METADATA_CATEGORIES]}"
        )

    _check_live_config()

    if category_id == "account":
        acct = _api_get(_ad_account_path())
        return {
            "category": category_id,
            "total": 1,
            "items": [
                {
                    "name": acct.get("id", ""),
                    "label": acct.get("name", "Ad Account"),
                    "description": f"{acct.get('currency', '')} · {acct.get('country', '')}",
                    "raw": acct,
                }
            ],
            "mode": "live",
        }

    if category_id in ADS_LIST_ENDPOINTS:
        edge = ADS_LIST_ENDPOINTS[category_id]
        data = _api_get(f"{_ad_account_path()}/{edge}", {"page_size": 100})
        items = [
            {
                "name": row.get("id", ""),
                "label": row.get("name", row.get("id", "")),
                "description": _summarize_row(row, category_id),
                "raw": row,
            }
            for row in data.get("items", [])
        ]
        return {"category": category_id, "total": len(items), "items": items, "mode": "live"}

    if category_id in ORGANIC_LIST_ENDPOINTS:
        edge = ORGANIC_LIST_ENDPOINTS[category_id]
        data = _api_get(edge, {"page_size": 25})
        items = [
            {
                "name": row.get("id", ""),
                "label": row.get("name") or row.get("title", row.get("id", "")),
                "description": _summarize_row(row, category_id),
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
        raise LookupError("Live object detail requires PINTEREST_ACCESS_TOKEN in .env.")

    _check_live_config()

    if category_id == "account":
        result = list_items("account")
        return {**result["items"][0], "category": category_id, "mode": "live"}

    if category_id in ADS_LIST_ENDPOINTS:
        edge = ADS_LIST_ENDPOINTS[category_id]
        obj = _api_get(f"{_ad_account_path()}/{edge}/{item_id}")
        return {
            "name": obj.get("id", item_id),
            "label": obj.get("name", item_id),
            "category": category_id,
            "fields": obj,
            "mode": "live",
        }

    if category_id == "boards":
        obj = _api_get(f"boards/{item_id}")
        return {
            "name": obj.get("id", item_id),
            "label": obj.get("name", item_id),
            "category": category_id,
            "fields": obj,
            "mode": "live",
        }

    if category_id == "pins":
        obj = _api_get(f"pins/{item_id}")
        return {
            "name": obj.get("id", item_id),
            "label": obj.get("title") or obj.get("name", item_id),
            "category": category_id,
            "fields": obj,
            "mode": "live",
        }

    raise LookupError(f"Cannot get detail for category '{category_id}'.")


def _summarize_row(row: dict, category_id: str) -> str:
    parts = []
    if row.get("status"):
        parts.append(f"status={row['status']}")
    if row.get("summary_status"):
        parts.append(f"summary={row['summary_status']}")
    if category_id == "campaigns" and row.get("objective_type"):
        parts.append(f"objective={row['objective_type']}")
    if category_id == "ad_groups" and row.get("billable_event"):
        parts.append(f"event={row['billable_event']}")
    if category_id == "boards" and row.get("privacy"):
        parts.append(f"privacy={row['privacy']}")
    if category_id == "pins" and row.get("media_type"):
        parts.append(f"media={row['media_type']}")
    return " · ".join(parts) if parts else category_id.rstrip("s")

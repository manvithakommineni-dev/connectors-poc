"""
Meta Ads (Facebook + Instagram) connectivity and metadata retrieval service.

How Meta exposes metadata:
  Meta Marketing API uses the Facebook Graph API.

  Key endpoints:
    GET /act_{ad_account_id}                    → Ad account info
    GET /act_{ad_account_id}/campaigns          → Campaigns
    GET /act_{ad_account_id}/adsets             → Ad sets
    GET /act_{ad_account_id}/ads                → Ads (Facebook + Instagram)
    GET /act_{ad_account_id}/insights           → Performance metrics

  Meta concept equivalents:
    Salesforce SObject  → Campaign / AdSet / Ad / AdAccount
    Salesforce Field    → Graph API field on each object
    Database Table      → Campaign (top-level ad structure)

  Instagram ads are managed through the same Marketing API — use
  publisher_platform breakdown in insights to split Facebook vs Instagram.

  Authentication (live — no demo mode):
    Long-lived User Access Token or System User token with ads_read scope.
    Required: META_ACCESS_TOKEN, META_AD_ACCOUNT_ID

  Setup (free for own ad account, dev mode):
    1. Meta Developer account + Business app with Marketing API
    2. Generate access token with ads_read permission
    3. Link token to ad account in Business Manager
"""

import logging
from typing import Any

import requests
from core.config import settings

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.facebook.com"

# Official Marketing API object fields (Graph API v21.0 reference)
CAMPAIGN_FIELDS = [
    {"name": "id", "label": "Campaign ID", "type": "string", "description": "Unique campaign identifier"},
    {"name": "name", "label": "Name", "type": "string", "description": "Campaign name"},
    {"name": "status", "label": "Status", "type": "enum", "description": "ACTIVE, PAUSED, DELETED, ARCHIVED"},
    {"name": "effective_status", "label": "Effective Status", "type": "enum", "description": "Actual delivery status considering parent state"},
    {"name": "objective", "label": "Objective", "type": "enum", "description": "OUTCOME_LEADS, OUTCOME_SALES, OUTCOME_TRAFFIC, etc."},
    {"name": "buying_type", "label": "Buying Type", "type": "enum", "description": "AUCTION or RESERVED"},
    {"name": "daily_budget", "label": "Daily Budget", "type": "integer", "description": "Daily budget in account currency (cents)"},
    {"name": "lifetime_budget", "label": "Lifetime Budget", "type": "integer", "description": "Lifetime budget in account currency (cents)"},
    {"name": "budget_remaining", "label": "Budget Remaining", "type": "integer", "description": "Remaining budget"},
    {"name": "spend_cap", "label": "Spend Cap", "type": "integer", "description": "Campaign spending limit"},
    {"name": "bid_strategy", "label": "Bid Strategy", "type": "enum", "description": "LOWEST_COST_WITHOUT_CAP, COST_CAP, etc."},
    {"name": "start_time", "label": "Start Time", "type": "datetime", "description": "Campaign start time"},
    {"name": "stop_time", "label": "Stop Time", "type": "datetime", "description": "Campaign stop time"},
    {"name": "created_time", "label": "Created Time", "type": "datetime", "description": "When campaign was created"},
    {"name": "updated_time", "label": "Updated Time", "type": "datetime", "description": "Last update timestamp"},
    {"name": "special_ad_categories", "label": "Special Ad Categories", "type": "array", "description": "CREDIT, EMPLOYMENT, HOUSING, etc."},
    {"name": "account_id", "label": "Account ID", "type": "string", "description": "Parent ad account ID"},
]

ADSET_FIELDS = [
    {"name": "id", "label": "Ad Set ID", "type": "string", "description": "Unique ad set identifier"},
    {"name": "name", "label": "Name", "type": "string", "description": "Ad set name"},
    {"name": "status", "label": "Status", "type": "enum", "description": "ACTIVE, PAUSED, DELETED, ARCHIVED"},
    {"name": "effective_status", "label": "Effective Status", "type": "enum", "description": "Actual delivery status"},
    {"name": "campaign_id", "label": "Campaign ID", "type": "string", "description": "Parent campaign ID"},
    {"name": "daily_budget", "label": "Daily Budget", "type": "integer", "description": "Daily budget in cents"},
    {"name": "lifetime_budget", "label": "Lifetime Budget", "type": "integer", "description": "Lifetime budget in cents"},
    {"name": "billing_event", "label": "Billing Event", "type": "enum", "description": "IMPRESSIONS, LINK_CLICKS, etc."},
    {"name": "optimization_goal", "label": "Optimization Goal", "type": "enum", "description": "REACH, LINK_CLICKS, CONVERSIONS, etc."},
    {"name": "bid_amount", "label": "Bid Amount", "type": "integer", "description": "Bid in account currency"},
    {"name": "bid_strategy", "label": "Bid Strategy", "type": "enum", "description": "Bidding strategy type"},
    {"name": "targeting", "label": "Targeting", "type": "object", "description": "Audience targeting spec (geo, age, interests)"},
    {"name": "start_time", "label": "Start Time", "type": "datetime", "description": "Ad set start time"},
    {"name": "end_time", "label": "End Time", "type": "datetime", "description": "Ad set end time"},
    {"name": "created_time", "label": "Created Time", "type": "datetime", "description": "Creation timestamp"},
    {"name": "updated_time", "label": "Updated Time", "type": "datetime", "description": "Last update timestamp"},
    {"name": "destination_type", "label": "Destination Type", "type": "enum", "description": "WEBSITE, APP, MESSENGER, etc."},
    {"name": "promoted_object", "label": "Promoted Object", "type": "object", "description": "Pixel, page, or app being promoted"},
]

AD_FIELDS = [
    {"name": "id", "label": "Ad ID", "type": "string", "description": "Unique ad identifier"},
    {"name": "name", "label": "Name", "type": "string", "description": "Ad name"},
    {"name": "status", "label": "Status", "type": "enum", "description": "ACTIVE, PAUSED, DELETED, ARCHIVED"},
    {"name": "effective_status", "label": "Effective Status", "type": "enum", "description": "Actual delivery status"},
    {"name": "adset_id", "label": "Ad Set ID", "type": "string", "description": "Parent ad set ID"},
    {"name": "campaign_id", "label": "Campaign ID", "type": "string", "description": "Parent campaign ID"},
    {"name": "creative", "label": "Creative", "type": "object", "description": "Ad creative object (image, video, text)"},
    {"name": "tracking_specs", "label": "Tracking Specs", "type": "array", "description": "Conversion tracking configuration"},
    {"name": "conversion_specs", "label": "Conversion Specs", "type": "array", "description": "Conversion event specs"},
    {"name": "created_time", "label": "Created Time", "type": "datetime", "description": "Creation timestamp"},
    {"name": "updated_time", "label": "Updated Time", "type": "datetime", "description": "Last update timestamp"},
    {"name": "preview_shareable_link", "label": "Preview Link", "type": "string", "description": "Shareable ad preview URL"},
]

INSIGHTS_METRICS = [
    {"name": "impressions", "label": "Impressions", "type": "integer", "description": "Times ad was on screen"},
    {"name": "clicks", "label": "Clicks", "type": "integer", "description": "Total clicks on ad"},
    {"name": "spend", "label": "Spend", "type": "float", "description": "Amount spent in account currency"},
    {"name": "reach", "label": "Reach", "type": "integer", "description": "Unique people who saw the ad"},
    {"name": "frequency", "label": "Frequency", "type": "float", "description": "Average impressions per person"},
    {"name": "cpm", "label": "CPM", "type": "float", "description": "Cost per 1,000 impressions"},
    {"name": "cpc", "label": "CPC", "type": "float", "description": "Cost per click"},
    {"name": "ctr", "label": "CTR", "type": "float", "description": "Click-through rate"},
    {"name": "cpp", "label": "CPP", "type": "float", "description": "Cost per 1,000 people reached"},
    {"name": "actions", "label": "Actions", "type": "array", "description": "Conversion actions (purchase, lead, etc.)"},
    {"name": "conversions", "label": "Conversions", "type": "array", "description": "Conversion events"},
    {"name": "cost_per_action_type", "label": "Cost Per Action", "type": "array", "description": "Cost broken down by action type"},
    {"name": "purchase_roas", "label": "Purchase ROAS", "type": "array", "description": "Return on ad spend for purchases"},
    {"name": "video_p25_watched_actions", "label": "Video 25% Watched", "type": "array", "description": "Video views at 25%"},
    {"name": "video_p50_watched_actions", "label": "Video 50% Watched", "type": "array", "description": "Video views at 50%"},
    {"name": "inline_link_clicks", "label": "Link Clicks", "type": "integer", "description": "Clicks on links in ad"},
    {"name": "inline_link_click_ctr", "label": "Link CTR", "type": "float", "description": "Link click-through rate"},
    {"name": "unique_clicks", "label": "Unique Clicks", "type": "integer", "description": "Unique people who clicked"},
    {"name": "unique_ctr", "label": "Unique CTR", "type": "float", "description": "Unique click-through rate"},
]

INSIGHTS_BREAKDOWNS = [
    {"name": "publisher_platform", "label": "Publisher Platform", "type": "breakdown", "description": "facebook, instagram, audience_network, messenger"},
    {"name": "platform_position", "label": "Platform Position", "type": "breakdown", "description": "feed, story, reels, search, etc."},
    {"name": "age", "label": "Age", "type": "breakdown", "description": "Age bracket"},
    {"name": "gender", "label": "Gender", "type": "breakdown", "description": "male, female, unknown"},
    {"name": "country", "label": "Country", "type": "breakdown", "description": "Country code"},
    {"name": "region", "label": "Region", "type": "breakdown", "description": "Region/state"},
    {"name": "device_platform", "label": "Device Platform", "type": "breakdown", "description": "mobile, desktop"},
    {"name": "impression_device", "label": "Impression Device", "type": "breakdown", "description": "Device type for impression"},
    {"name": "product_id", "label": "Product ID", "type": "breakdown", "description": "Product in catalog ad"},
]

METADATA_CATEGORIES = [
    {"id": "account", "label": "Ad Account", "description": "Live ad account details from Graph API"},
    {"id": "campaigns", "label": "Campaigns", "description": "Live campaigns in the ad account"},
    {"id": "adsets", "label": "Ad Sets", "description": "Live ad sets (targeting + budget level)"},
    {"id": "ads", "label": "Ads", "description": "Live ads — Facebook and Instagram creatives"},
    {"id": "campaign_fields", "label": "Campaign Fields", "description": "Queryable fields on Campaign object"},
    {"id": "adset_fields", "label": "Ad Set Fields", "description": "Queryable fields on AdSet object"},
    {"id": "ad_fields", "label": "Ad Fields", "description": "Queryable fields on Ad object"},
    {"id": "insights_metrics", "label": "Insights Metrics", "description": "Performance metrics from Insights API"},
    {"id": "insights_breakdowns", "label": "Insights Breakdowns", "description": "Segmentation dimensions (incl. Instagram vs Facebook)"},
]

FIELD_CATALOG: dict[str, list] = {
    "campaign_fields": CAMPAIGN_FIELDS,
    "adset_fields": ADSET_FIELDS,
    "ad_fields": AD_FIELDS,
    "insights_metrics": INSIGHTS_METRICS,
    "insights_breakdowns": INSIGHTS_BREAKDOWNS,
}

LIST_EDGES = {
    "campaigns": "campaigns",
    "adsets": "adsets",
    "ads": "ads",
}

LIST_FIELDS = {
    "campaigns": "id,name,status,effective_status,objective,daily_budget,lifetime_budget,created_time,updated_time",
    "adsets": "id,name,status,effective_status,campaign_id,daily_budget,optimization_goal,created_time",
    "ads": "id,name,status,effective_status,adset_id,campaign_id,created_time",
}


def _api_version() -> str:
    return settings.META_API_VERSION or "v21.0"


def _check_config() -> None:
    if not settings.META_ACCESS_TOKEN:
        raise ConnectionError(
            "META_ACCESS_TOKEN is not set in .env. "
            "Generate a token with ads_read scope from Meta Graph API Explorer or Business Manager System User."
        )
    if not settings.META_AD_ACCOUNT_ID:
        raise ConnectionError(
            "META_AD_ACCOUNT_ID is not set in .env. "
            "Find it in Meta Business Manager → Ad Accounts (format: act_123456789 or 123456789)."
        )


def _ad_account_id() -> str:
    aid = settings.META_AD_ACCOUNT_ID.strip()
    if not aid.startswith("act_"):
        aid = f"act_{aid}"
    return aid


def _graph_get(path: str, params: dict | None = None) -> dict:
    _check_config()
    params = dict(params or {})
    params["access_token"] = settings.META_ACCESS_TOKEN
    url = f"{GRAPH_BASE}/{_api_version()}/{path.lstrip('/')}"
    resp = requests.get(url, params=params, timeout=30)
    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"Meta API returned non-JSON [{resp.status_code}]: {resp.text[:300]}")

    if "error" in data:
        err = data["error"]
        code = err.get("code", 0)
        msg = err.get("message", str(err))
        subcode = err.get("error_subcode", "")
        full = f"{msg} (code {code}, subcode {subcode})".strip()
        if code in (190, 102, 463):
            raise ConnectionError(f"Meta authentication failed: {full}")
        if code in (10, 200, 294):
            raise PermissionError(
                f"Meta access denied: {full}. Ensure token has ads_read and is linked to this ad account."
            )
        raise RuntimeError(f"Meta API error: {full}")

    return data


def test_connection() -> dict:
    _check_config()
    fields = (
        "id,account_id,name,account_status,currency,timezone_name,amount_spent,"
        "balance,business_name,age,min_daily_budget,disable_reason,funding_source_details"
    )
    acct = _graph_get(_ad_account_id(), {"fields": fields})

    campaigns = _graph_get(f"{_ad_account_id()}/campaigns", {"fields": "id", "limit": 1})
    campaign_count = len(campaigns.get("data", []))
    if campaigns.get("paging", {}).get("next"):
        campaign_count = "1+"

    return {
        "connected": True,
        "mode": "live",
        "ad_account_id": acct.get("account_id") or acct.get("id"),
        "ad_account_name": acct.get("name", ""),
        "account_status": acct.get("account_status"),
        "currency": acct.get("currency", ""),
        "timezone": acct.get("timezone_name", ""),
        "amount_spent": acct.get("amount_spent", "0"),
        "business_name": acct.get("business_name", ""),
        "campaigns_sample": campaign_count,
        "platforms": "Facebook + Instagram (via Marketing API)",
        "auth_method": "Access Token (ads_read)",
        "api_version": _api_version(),
    }


def list_categories() -> list[dict]:
    _check_config()
    counts: dict[str, Any] = {}
    for cat_id in FIELD_CATALOG:
        counts[cat_id] = len(FIELD_CATALOG[cat_id])

    for cat_id, edge in LIST_EDGES.items():
        try:
            data = _graph_get(f"{_ad_account_id()}/{edge}", {"fields": "id", "limit": 100})
            items = data.get("data", [])
            counts[cat_id] = len(items)
            if data.get("paging", {}).get("next") and len(items) == 100:
                counts[cat_id] = f"{len(items)}+"
        except Exception:
            counts[cat_id] = 0

    counts["account"] = 1

    return [{**cat, "items_count": counts.get(cat["id"], 0)} for cat in METADATA_CATEGORIES]


def list_items(category_id: str) -> dict:
    _check_config()

    if category_id == "account":
        fields = (
            "id,account_id,name,account_status,currency,timezone_name,amount_spent,"
            "balance,business_name,created_time,age,funding_source_details"
        )
        acct = _graph_get(_ad_account_id(), {"fields": fields})
        return {
            "category": category_id,
            "total": 1,
            "items": [
                {
                    "name": acct.get("account_id") or acct.get("id", ""),
                    "label": acct.get("name", "Ad Account"),
                    "description": f"{acct.get('currency', '')} · status {acct.get('account_status', '')}",
                    "raw": acct,
                }
            ],
            "mode": "live",
        }

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
        return {"category": category_id, "total": len(items), "items": items, "mode": "live"}

    if category_id in LIST_EDGES:
        edge = LIST_EDGES[category_id]
        fields = LIST_FIELDS[category_id]
        data = _graph_get(f"{_ad_account_id()}/{edge}", {"fields": fields, "limit": 100})
        items = [
            {
                "name": row.get("id", ""),
                "label": row.get("name", row.get("id", "")),
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
    _check_config()

    if category_id in FIELD_CATALOG:
        for f in FIELD_CATALOG[category_id]:
            if f["name"] == item_id:
                return {**f, "category": category_id, "mode": "live"}
        raise LookupError(f"Field '{item_id}' not found in '{category_id}'.")

    if category_id == "account":
        result = list_items("account")
        return {**result["items"][0], "category": category_id, "mode": "live"}

    if category_id in LIST_EDGES:
        fields = LIST_FIELDS[category_id]
        obj = _graph_get(item_id, {"fields": fields})
        return {
            "name": obj.get("id", item_id),
            "label": obj.get("name", item_id),
            "category": category_id,
            "fields": obj,
            "mode": "live",
        }

    raise LookupError(f"Cannot get detail for category '{category_id}'.")


def _summarize_row(row: dict, category_id: str) -> str:
    parts = []
    if row.get("status"):
        parts.append(f"status={row['status']}")
    if row.get("effective_status"):
        parts.append(f"effective={row['effective_status']}")
    if category_id == "campaigns" and row.get("objective"):
        parts.append(f"objective={row['objective']}")
    if category_id == "adsets" and row.get("optimization_goal"):
        parts.append(f"goal={row['optimization_goal']}")
    return " · ".join(parts) if parts else category_id.rstrip("s")

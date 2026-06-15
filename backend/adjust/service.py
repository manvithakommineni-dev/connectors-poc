"""
Adjust connectivity and metadata retrieval service.

How Adjust exposes metadata:
  Adjust Report Service API (RS API) provides filter catalogs and event definitions
  used when building reports and dashboards.

  Key endpoints:
    GET /reports-service/filters_data?required_filters=apps,overview_metrics,...
    GET /reports-service/events

  Adjust concept equivalents:
    Salesforce SObject  → App / Metric / Dimension / Event
    Salesforce Field    → Metric id / Dimension id / Event slug
    Database Table      → App (top-level attribution entity)

  Authentication (live — no demo mode):
    API Token from Adjust dashboard → Account settings → My profile → API Token
    Required: ADJUST_API_TOKEN

  Free tier:
    Adjust Base plan — 1,500 attributions/month for 12 months (signup at adjust.com)
"""

import logging
from typing import Any

import requests

from core.config import settings

logger = logging.getLogger(__name__)

RS_API_BASE = "https://automate.adjust.com/reports-service"

# Category id → filters_data key (None = use /events endpoint)
FILTER_CATEGORIES: dict[str, str | None] = {
    "apps": "apps",
    "overview_metrics": "overview_metrics",
    "event_metrics": "event_metrics",
    "cost_metrics": "cost_metrics",
    "cohort_metrics": "cohort_metrics",
    "skad_metrics": "skad_metrics",
    "dimensions": "dimensions",
    "networks": "networks",
    "countries": "countries",
    "events": None,
}

METADATA_CATEGORIES = [
    {
        "id": "apps",
        "label": "Apps",
        "description": "Mobile apps registered in your Adjust account (app tokens)",
    },
    {
        "id": "events",
        "label": "Events",
        "description": "In-app events with slugs and tokens for report queries",
    },
    {
        "id": "overview_metrics",
        "label": "Overview Metrics",
        "description": "Core KPI metrics (installs, sessions, retention, etc.)",
    },
    {
        "id": "event_metrics",
        "label": "Event Metrics",
        "description": "Metrics duplicated per tracked in-app event",
    },
    {
        "id": "cost_metrics",
        "label": "Cost Metrics",
        "description": "Ad spend and cost-related metrics",
    },
    {
        "id": "cohort_metrics",
        "label": "Cohort Metrics",
        "description": "Cohort-based retention and LTV metrics",
    },
    {
        "id": "skad_metrics",
        "label": "SKAd Metrics",
        "description": "SKAdNetwork attribution metrics (iOS)",
    },
    {
        "id": "dimensions",
        "label": "Dimensions",
        "description": "Report breakdown dimensions (channel, campaign, country, etc.)",
    },
    {
        "id": "networks",
        "label": "Networks",
        "description": "Ad networks and media sources",
    },
    {
        "id": "countries",
        "label": "Countries",
        "description": "Country codes available for filtering reports",
    },
]


def _check_config() -> None:
    if not settings.ADJUST_API_TOKEN:
        raise ConnectionError(
            "ADJUST_API_TOKEN is not set in .env. "
            "Copy your API Token from Adjust → Account settings → My profile → API Token."
        )


def _headers() -> dict:
    _check_config()
    return {"Authorization": f"Bearer {settings.ADJUST_API_TOKEN}"}


def _request(method: str, path: str, params: dict | None = None) -> Any:
    url = f"{RS_API_BASE}/{path.lstrip('/')}"
    resp = requests.request(method, url, headers=_headers(), params=params, timeout=30)

    if resp.status_code == 204:
        return [] if path.rstrip("/") == "events" else {}

    if resp.status_code == 401:
        raise ConnectionError(
            "Adjust authentication failed (401). Check ADJUST_API_TOKEN in .env."
        )
    if resp.status_code == 403:
        raise PermissionError(
            "Adjust access denied (403). Your token may lack permission for this resource."
        )
    if resp.status_code == 429:
        raise RuntimeError("Adjust rate limit exceeded (429). Retry later.")
    if resp.status_code >= 400:
        detail = resp.text[:300] if resp.text else resp.reason
        raise RuntimeError(f"Adjust API error [{resp.status_code}]: {detail}")

    try:
        return resp.json()
    except Exception:
        raise RuntimeError(f"Adjust API returned non-JSON [{resp.status_code}]: {resp.text[:300]}")


def _fetch_filters(filter_key: str) -> list[dict]:
    data = _request("GET", "filters_data", {"required_filters": filter_key})
    items = data.get(filter_key, [])
    return items if isinstance(items, list) else []


def _fetch_events() -> list[dict]:
    data = _request("GET", "events", {"tokens_mapping": "true"})
    return data if isinstance(data, list) else []


def _filter_item_to_row(row: dict, category_id: str) -> dict:
    desc_parts = []
    if row.get("section"):
        desc_parts.append(f"section={row['section']}")
    if row.get("formatting"):
        desc_parts.append(f"format={row['formatting']}")
    if category_id == "events" and row.get("app_token"):
        tokens = row["app_token"]
        if isinstance(tokens, list) and tokens:
            desc_parts.append(f"apps={len(tokens)}")
    if category_id == "events" and row.get("is_skad_event"):
        desc_parts.append("SKAd")

    return {
        "name": row.get("id", ""),
        "label": row.get("name") or row.get("short_name") or row.get("id", ""),
        "description": " · ".join(desc_parts) if desc_parts else category_id,
        "raw": row,
    }


def test_connection() -> dict:
    _check_config()
    apps = _fetch_filters("apps")
    events = _fetch_events()

    return {
        "connected": True,
        "mode": "live",
        "apps_count": len(apps),
        "events_count": len(events),
        "sample_app": apps[0].get("name") if apps else None,
        "auth_method": "API Token (Bearer)",
        "api_base": RS_API_BASE,
        "plan_note": "Free Base plan: 1,500 attributions/month (12 months)",
    }


def list_categories() -> list[dict]:
    _check_config()
    counts: dict[str, Any] = {}

    for cat_id, filter_key in FILTER_CATEGORIES.items():
        try:
            if filter_key is None:
                counts[cat_id] = len(_fetch_events())
            else:
                counts[cat_id] = len(_fetch_filters(filter_key))
        except Exception as exc:
            logger.warning("Adjust category count failed for %s: %s", cat_id, exc)
            counts[cat_id] = 0

    return [{**cat, "items_count": counts.get(cat["id"], 0)} for cat in METADATA_CATEGORIES]


def list_items(category_id: str) -> dict:
    _check_config()

    if category_id not in FILTER_CATEGORIES:
        raise LookupError(
            f"Category '{category_id}' not found. Available: {[c['id'] for c in METADATA_CATEGORIES]}"
        )

    filter_key = FILTER_CATEGORIES[category_id]
    if filter_key is None:
        rows = _fetch_events()
    else:
        rows = _fetch_filters(filter_key)

    items = [_filter_item_to_row(row, category_id) for row in rows]
    return {"category": category_id, "total": len(items), "items": items, "mode": "live"}


def get_item_detail(category_id: str, item_id: str) -> dict:
    _check_config()

    if category_id not in FILTER_CATEGORIES:
        raise LookupError(f"Category '{category_id}' not found.")

    result = list_items(category_id)
    for item in result["items"]:
        if item["name"] == item_id:
            return {**item, "category": category_id, "mode": "live", "fields": item.get("raw", {})}

    raise LookupError(f"Item '{item_id}' not found in category '{category_id}'.")

"""
Adobe Analytics 2.0 API connectivity and metadata retrieval.

Analytics 2.0 API (analytics.adobe.io):
    GET /{companyId}/dimensions?rsid=...     → Reportable dimensions
    GET /{companyId}/metrics?rsid=...       → Reportable metrics
    GET /{companyId}/reportsuites/...       → Report suite metadata
    POST /{companyId}/reports               → Run reports (metrics + dimensions)

  Authentication (requires paid Adobe Analytics license for live data):
    1. Adobe Developer Console → project → Adobe Analytics API
    2. OAuth Server-to-Server credentials (Client ID + Client Secret)
    3. Adobe Admin Console → product profile with report suite access
    Required for live: ADOBE_CLIENT_ID, ADOBE_CLIENT_SECRET,
                       ADOBE_GLOBAL_COMPANY_ID, ADOBE_REPORT_SUITE_ID
    Optional: ADOBE_ACCESS_TOKEN (auto-fetched via client credentials if empty)

  Demo mode (no credentials):
    Returns real Adobe Analytics 2.0 field/component schema catalogs.
"""

import logging
from typing import Any

import requests
from core.config import settings

logger = logging.getLogger(__name__)

API_BASE = "https://analytics.adobe.io/api"
IMS_TOKEN_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
DEFAULT_OAUTH_SCOPE = (
    "openid,AdobeID,read_organizations,additional_info.projectedProductContext,"
    "additional_info.roles,adobeio_api,read_client_creds,manage_client_creds"
)

DIMENSION_FIELDS = [
    {"name": "id", "label": "Dimension ID", "type": "string", "description": "API identifier (e.g. variables/page)"},
    {"name": "title", "label": "Title", "type": "string", "description": "Display name in Analysis Workspace"},
    {"name": "name", "label": "Name", "type": "string", "description": "Internal dimension name"},
    {"name": "type", "label": "Type", "type": "enum", "description": "Dimension type (string, time, etc.)"},
    {"name": "category", "label": "Category", "type": "string", "description": "Component category grouping"},
    {"name": "support", "label": "Support", "type": "enum", "description": "Supported, Deprecated, etc."},
    {"name": "segmentable", "label": "Segmentable", "type": "boolean", "description": "Can be used in segments"},
    {"name": "reportable", "label": "Reportable", "type": "boolean", "description": "Can be used in reports"},
    {"name": "pathable", "label": "Pathable", "type": "boolean", "description": "Supports pathing reports"},
    {"name": "dataGroup", "label": "Data Group", "type": "string", "description": "Standard vs custom classification"},
]

METRIC_FIELDS = [
    {"name": "id", "label": "Metric ID", "type": "string", "description": "API identifier (e.g. metrics/pageviews)"},
    {"name": "title", "label": "Title", "type": "string", "description": "Display name in Analysis Workspace"},
    {"name": "name", "label": "Name", "type": "string", "description": "Internal metric name"},
    {"name": "type", "label": "Type", "type": "enum", "description": "int, decimal, percent, currency, time"},
    {"name": "category", "label": "Category", "type": "string", "description": "Component category grouping"},
    {"name": "support", "label": "Support", "type": "enum", "description": "Supported, Deprecated, etc."},
    {"name": "precision", "label": "Precision", "type": "integer", "description": "Decimal precision for display"},
    {"name": "segmentable", "label": "Segmentable", "type": "boolean", "description": "Can be used in segments"},
    {"name": "polarity", "label": "Polarity", "type": "enum", "description": "positive or negative (higher is better?)"},
    {"name": "allocation", "label": "Allocation", "type": "boolean", "description": "Supports allocation models"},
]

SEGMENT_FIELDS = [
    {"name": "id", "label": "Segment ID", "type": "string", "description": "Unique segment identifier"},
    {"name": "name", "label": "Name", "type": "string", "description": "Segment display name"},
    {"name": "description", "label": "Description", "type": "string", "description": "Segment definition summary"},
    {"name": "owner", "label": "Owner", "type": "object", "description": "Segment owner user info"},
    {"name": "rsid", "label": "Report Suite", "type": "string", "description": "Associated report suite ID"},
    {"name": "definition", "label": "Definition", "type": "object", "description": "Segment rule container JSON"},
    {"name": "approved", "label": "Approved", "type": "boolean", "description": "Approved for sharing"},
    {"name": "favorite", "label": "Favorite", "type": "boolean", "description": "Marked as favorite"},
]

REPORT_FIELDS = [
    {"name": "rsid", "label": "Report Suite ID", "type": "string", "description": "Report suite for the request"},
    {"name": "dimension", "label": "Dimension", "type": "string", "description": "Breakdown dimension ID"},
    {"name": "metricContainer", "label": "Metric Container", "type": "object", "description": "Metrics and filters for the report"},
    {"name": "globalFilters", "label": "Global Filters", "type": "array", "description": "Date range and segment filters"},
    {"name": "settings", "label": "Settings", "type": "object", "description": "Limit, page, sort, currency settings"},
    {"name": "summaryData", "label": "Summary Data", "type": "object", "description": "Totals row in response"},
    {"name": "rows", "label": "Rows", "type": "array", "description": "Dimension breakdown rows"},
]

# Demo catalog — common Adobe Analytics components (Analytics 2.0 API IDs)
DEMO_DIMENSIONS = [
    {"id": "variables/page", "title": "Page", "category": "Traffic", "type": "string"},
    {"id": "variables/geocountry", "title": "Country", "category": "Geo", "type": "string"},
    {"id": "variables/geocity", "title": "City", "category": "Geo", "type": "string"},
    {"id": "variables/mobiledevicetype", "title": "Mobile Device Type", "category": "Mobile", "type": "string"},
    {"id": "variables/browser", "title": "Browser", "category": "Technology", "type": "string"},
    {"id": "variables/operatingsystem", "title": "Operating System", "category": "Technology", "type": "string"},
    {"id": "variables/referrer", "title": "Referrer", "category": "Traffic", "type": "string"},
    {"id": "variables/campaign", "title": "Campaign", "category": "Marketing", "type": "string"},
    {"id": "variables/evar1", "title": "Custom eVar 1", "category": "Conversion", "type": "string"},
    {"id": "variables/prop1", "title": "Custom prop 1", "category": "Traffic", "type": "string"},
    {"id": "variables/product", "title": "Product", "category": "Commerce", "type": "string"},
    {"id": "variables/trackingcode", "title": "Tracking Code", "category": "Marketing", "type": "string"},
    {"id": "variables/day", "title": "Day", "category": "Time", "type": "time"},
    {"id": "variables/hour", "title": "Hour", "category": "Time", "type": "time"},
    {"id": "variables/entrypage", "title": "Entry Page", "category": "Traffic", "type": "string"},
    {"id": "variables/exitpage", "title": "Exit Page", "category": "Traffic", "type": "string"},
]

DEMO_METRICS = [
    {"id": "metrics/pageviews", "title": "Page Views", "type": "int", "category": "Traffic"},
    {"id": "metrics/visits", "title": "Visits", "type": "int", "category": "Traffic"},
    {"id": "metrics/visitors", "title": "Unique Visitors", "type": "int", "category": "Traffic"},
    {"id": "metrics/bouncerate", "title": "Bounce Rate", "type": "percent", "category": "Traffic"},
    {"id": "metrics/averagetimespentonpage", "title": "Time Spent on Page", "type": "time", "category": "Traffic"},
    {"id": "metrics/orders", "title": "Orders", "type": "int", "category": "Commerce"},
    {"id": "metrics/revenue", "title": "Revenue", "type": "currency", "category": "Commerce"},
    {"id": "metrics/units", "title": "Units", "type": "int", "category": "Commerce"},
    {"id": "metrics/cartadditions", "title": "Cart Additions", "type": "int", "category": "Commerce"},
    {"id": "metrics/cartremovals", "title": "Cart Removals", "type": "int", "category": "Commerce"},
    {"id": "metrics/event1", "title": "Custom Event 1", "type": "int", "category": "Conversion"},
    {"id": "metrics/entries", "title": "Entries", "type": "int", "category": "Traffic"},
    {"id": "metrics/exits", "title": "Exits", "type": "int", "category": "Traffic"},
    {"id": "metrics/occurrences", "title": "Occurrences", "type": "int", "category": "Traffic"},
]

DEMO_SEGMENTS = [
    {"id": "s1000001", "name": "All Visits", "description": "All visitors to the site"},
    {"id": "s1000002", "name": "Mobile Visits", "description": "Visits from mobile devices"},
    {"id": "s1000003", "name": "Paid Search", "description": "Traffic from paid search campaigns"},
    {"id": "s1000004", "name": "Purchasers", "description": "Visitors who placed an order"},
]

METADATA_CATEGORIES = [
    {"id": "report_suite", "label": "Report Suite", "description": "Report suite metadata for your rsid"},
    {"id": "dimensions", "label": "Dimensions", "description": "Reportable dimensions (page, geo, campaign, eVars, props)"},
    {"id": "metrics", "label": "Metrics", "description": "Reportable metrics (pageviews, visits, revenue, events)"},
    {"id": "segments", "label": "Segments", "description": "Audience segments for filtering reports"},
    {"id": "dimension_fields", "label": "Dimension Fields", "description": "Fields on Dimension API objects"},
    {"id": "metric_fields", "label": "Metric Fields", "description": "Fields on Metric API objects"},
    {"id": "segment_fields", "label": "Segment Fields", "description": "Fields on Segment API objects"},
    {"id": "report_fields", "label": "Report Fields", "description": "Reporting API request/response structure"},
]

FIELD_CATALOG: dict[str, list] = {
    "dimension_fields": DIMENSION_FIELDS,
    "metric_fields": METRIC_FIELDS,
    "segment_fields": SEGMENT_FIELDS,
    "report_fields": REPORT_FIELDS,
}


def _is_demo_mode() -> bool:
    return not (
        settings.ADOBE_CLIENT_ID.strip()
        and settings.ADOBE_CLIENT_SECRET.strip()
        and settings.ADOBE_GLOBAL_COMPANY_ID.strip()
        and settings.ADOBE_REPORT_SUITE_ID.strip()
    )


def _check_live_config() -> None:
    if not settings.ADOBE_CLIENT_ID.strip():
        raise ConnectionError(
            "ADOBE_CLIENT_ID is not set in .env. "
            "Create OAuth Server-to-Server credentials in Adobe Developer Console."
        )
    if not settings.ADOBE_CLIENT_SECRET.strip():
        raise ConnectionError("ADOBE_CLIENT_SECRET is not set in .env.")
    if not settings.ADOBE_GLOBAL_COMPANY_ID.strip():
        raise ConnectionError(
            "ADOBE_GLOBAL_COMPANY_ID is not set in .env. "
            "Find it in Adobe Analytics → Admin → Company Settings → Company ID."
        )
    if not settings.ADOBE_REPORT_SUITE_ID.strip():
        raise ConnectionError(
            "ADOBE_REPORT_SUITE_ID is not set in .env. "
            "Your report suite ID (rsid), e.g. examplersid."
        )


def _company_base() -> str:
    return f"{API_BASE}/{settings.ADOBE_GLOBAL_COMPANY_ID.strip()}"


def _rsid() -> str:
    return settings.ADOBE_REPORT_SUITE_ID.strip()


def _get_access_token() -> str:
    explicit = settings.ADOBE_ACCESS_TOKEN.strip()
    if explicit:
        return explicit

    scope = settings.ADOBE_OAUTH_SCOPE.strip() or DEFAULT_OAUTH_SCOPE
    resp = requests.post(
        IMS_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": settings.ADOBE_CLIENT_ID.strip(),
            "client_secret": settings.ADOBE_CLIENT_SECRET.strip(),
            "scope": scope,
        },
        timeout=30,
    )
    try:
        data = resp.json()
    except Exception:
        raise ConnectionError(f"Adobe IMS token error [{resp.status_code}]: {resp.text[:300]}")

    if resp.status_code != 200 or "access_token" not in data:
        err = data.get("error_description") or data.get("error") or resp.text[:300]
        raise ConnectionError(f"Adobe IMS authentication failed: {err}")

    return data["access_token"]


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_access_token()}",
        "x-api-key": settings.ADOBE_CLIENT_ID.strip(),
        "x-proxy-global-company-id": settings.ADOBE_GLOBAL_COMPANY_ID.strip(),
        "Accept": "application/json",
    }


def _api_get(path: str, params: dict | None = None) -> Any:
    _check_live_config()
    url = f"{_company_base()}/{path.lstrip('/')}"
    resp = requests.get(url, headers=_headers(), params=params or {}, timeout=60)
    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"Adobe Analytics API returned non-JSON [{resp.status_code}]: {resp.text[:300]}")

    if resp.status_code == 401:
        raise ConnectionError(
            "Adobe Analytics authentication failed (401). Check ADOBE_CLIENT_ID, "
            "ADOBE_CLIENT_SECRET, and ADOBE_ACCESS_TOKEN."
        )
    if resp.status_code == 403:
        msg = data.get("errorDescription") or data.get("message") or str(data)
        raise PermissionError(
            f"Adobe Analytics access denied: {msg}. "
            "Ensure your org has an Analytics license and the API client has report suite permissions."
        )
    if resp.status_code >= 400:
        msg = data.get("errorDescription") or data.get("message") or str(data)
        raise RuntimeError(f"Adobe Analytics API error [{resp.status_code}]: {msg}")

    return data


def _normalize_dimension(d: dict) -> dict:
    return {
        "name": d.get("id", ""),
        "label": d.get("title", d.get("name", d.get("id", ""))),
        "description": f"{d.get('category', '')} · {d.get('type', '')}".strip(" · "),
        "category": d.get("category", ""),
        "type": d.get("type", ""),
        "segmentable": d.get("segmentable"),
        "reportable": d.get("reportable"),
        "raw": d,
    }


def _normalize_metric(m: dict) -> dict:
    return {
        "name": m.get("id", ""),
        "label": m.get("title", m.get("name", m.get("id", ""))),
        "description": f"{m.get('category', '')} · {m.get('type', '')}".strip(" · "),
        "category": m.get("category", ""),
        "type": m.get("type", ""),
        "raw": m,
    }


def _normalize_segment(s: dict) -> dict:
    return {
        "name": s.get("id", ""),
        "label": s.get("name", s.get("id", "")),
        "description": s.get("description", ""),
        "raw": s,
    }


def test_connection() -> dict:
    if _is_demo_mode():
        total_fields = sum(len(v) for v in FIELD_CATALOG.values())
        return {
            "connected": True,
            "mode": "demo",
            "message": (
                "Demo Mode — showing Adobe Analytics 2.0 API schema. "
                "Set ADOBE_CLIENT_ID, ADOBE_CLIENT_SECRET, ADOBE_GLOBAL_COMPANY_ID, "
                "and ADOBE_REPORT_SUITE_ID in .env for live data (requires Analytics license)."
            ),
            "categories_count": len(METADATA_CATEGORIES),
            "total_fields": total_fields,
            "api_version": "2.0",
            "auth_method": "OAuth Server-to-Server (Adobe IMS)",
        }

    _check_live_config()
    rsid = _rsid()
    suite = _api_get(f"reportsuites/collections/suites/{rsid}")
    dims = _api_get("dimensions", {"rsid": rsid, "locale": "en_US", "limit": 5})
    dim_list = dims if isinstance(dims, list) else dims.get("content", [])
    metrics = _api_get("metrics", {"rsid": rsid, "locale": "en_US", "limit": 5})
    metric_list = metrics if isinstance(metrics, list) else metrics.get("content", [])

    return {
        "connected": True,
        "mode": "live",
        "report_suite_id": rsid,
        "report_suite_name": suite.get("name", suite.get("siteTitle", "")),
        "company_id": settings.ADOBE_GLOBAL_COMPANY_ID.strip(),
        "dimensions_sample": len(dim_list) if isinstance(dim_list, list) else "1+",
        "metrics_sample": len(metric_list) if isinstance(metric_list, list) else "1+",
        "auth_method": "OAuth Server-to-Server (Adobe IMS)",
        "api_version": "2.0",
        "api_host": "analytics.adobe.io",
    }


def list_categories() -> list[dict]:
    counts: dict[str, Any] = {cat_id: len(fields) for cat_id, fields in FIELD_CATALOG.items()}

    if _is_demo_mode():
        counts["report_suite"] = 1
        counts["dimensions"] = len(DEMO_DIMENSIONS)
        counts["metrics"] = len(DEMO_METRICS)
        counts["segments"] = len(DEMO_SEGMENTS)
        return [{**cat, "items_count": counts.get(cat["id"], 0)} for cat in METADATA_CATEGORIES]

    _check_live_config()
    rsid = _rsid()

    counts["report_suite"] = 1
    for cat_id, endpoint in (("dimensions", "dimensions"), ("metrics", "metrics"), ("segments", "segments")):
        try:
            data = _api_get(endpoint, {"rsid": rsid, "locale": "en_US", "limit": 100})
            items = data if isinstance(data, list) else data.get("content", [])
            counts[cat_id] = len(items)
            if isinstance(data, dict) and data.get("totalElements", 0) > len(items):
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
        if category_id == "report_suite":
            return {
                "category": category_id,
                "total": 1,
                "items": [
                    {
                        "name": "examplersid",
                        "label": "Example Report Suite (Demo)",
                        "description": "Demo report suite — set ADOBE_REPORT_SUITE_ID for your rsid",
                    }
                ],
                "mode": "demo",
            }
        if category_id == "dimensions":
            items = [
                {
                    "name": d["id"],
                    "label": d["title"],
                    "description": f"{d.get('category', '')} · {d.get('type', '')}",
                }
                for d in DEMO_DIMENSIONS
            ]
            return {"category": category_id, "total": len(items), "items": items, "mode": "demo"}
        if category_id == "metrics":
            items = [
                {
                    "name": m["id"],
                    "label": m["title"],
                    "description": f"{m.get('category', '')} · {m.get('type', '')}",
                }
                for m in DEMO_METRICS
            ]
            return {"category": category_id, "total": len(items), "items": items, "mode": "demo"}
        if category_id == "segments":
            items = [
                {
                    "name": s["id"],
                    "label": s["name"],
                    "description": s.get("description", ""),
                }
                for s in DEMO_SEGMENTS
            ]
            return {"category": category_id, "total": len(items), "items": items, "mode": "demo"}
        raise LookupError(
            f"Category '{category_id}' not found. Available: {[c['id'] for c in METADATA_CATEGORIES]}"
        )

    _check_live_config()
    rsid = _rsid()

    if category_id == "report_suite":
        suite = _api_get(f"reportsuites/collections/suites/{rsid}")
        return {
            "category": category_id,
            "total": 1,
            "items": [
                {
                    "name": rsid,
                    "label": suite.get("name", suite.get("siteTitle", rsid)),
                    "description": suite.get("timezone", "") or suite.get("currency", ""),
                    "raw": suite,
                }
            ],
            "mode": "live",
        }

    if category_id == "dimensions":
        data = _api_get("dimensions", {"rsid": rsid, "locale": "en_US", "limit": 100})
        rows = data if isinstance(data, list) else data.get("content", [])
        items = [_normalize_dimension(d) for d in rows]
        return {"category": category_id, "total": len(items), "items": items, "mode": "live"}

    if category_id == "metrics":
        data = _api_get("metrics", {"rsid": rsid, "locale": "en_US", "limit": 100})
        rows = data if isinstance(data, list) else data.get("content", [])
        items = [_normalize_metric(m) for m in rows]
        return {"category": category_id, "total": len(items), "items": items, "mode": "live"}

    if category_id == "segments":
        try:
            data = _api_get("segments", {"rsid": rsid, "locale": "en_US", "limit": 50})
            rows = data if isinstance(data, list) else data.get("content", [])
            items = [_normalize_segment(s) for s in rows]
            return {"category": category_id, "total": len(items), "items": items, "mode": "live"}
        except Exception:
            return {"category": category_id, "total": 0, "items": [], "mode": "live"}

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
        for pool, cat in (
            (DEMO_DIMENSIONS, "dimensions"),
            (DEMO_METRICS, "metrics"),
            (DEMO_SEGMENTS, "segments"),
        ):
            if category_id == cat:
                for row in pool:
                    key = row.get("id") or row.get("name")
                    if key == item_id:
                        return {
                            "name": key,
                            "label": row.get("title") or row.get("name", key),
                            "description": row.get("description", ""),
                            "category": category_id,
                            "fields": row,
                            "mode": "demo",
                        }
        if category_id == "report_suite" and item_id == "examplersid":
            return {
                "name": "examplersid",
                "label": "Example Report Suite (Demo)",
                "category": category_id,
                "fields": {"rsid": "examplersid", "timezone": "GMT", "currency": "USD"},
                "mode": "demo",
            }
        raise LookupError("Live object detail requires Adobe Analytics credentials in .env.")

    _check_live_config()
    rsid = _rsid()

    if category_id == "report_suite":
        suite = _api_get(f"reportsuites/collections/suites/{rsid}")
        return {
            "name": rsid,
            "label": suite.get("name", rsid),
            "category": category_id,
            "fields": suite,
            "mode": "live",
        }

    if category_id == "dimensions":
        obj = _api_get(f"dimensions/{item_id}", {"rsid": rsid, "locale": "en_US"})
        return {
            "name": item_id,
            "label": obj.get("title", item_id),
            "category": category_id,
            "fields": obj,
            "mode": "live",
        }

    if category_id == "metrics":
        obj = _api_get(f"metrics/{item_id}", {"rsid": rsid, "locale": "en_US"})
        return {
            "name": item_id,
            "label": obj.get("title", item_id),
            "category": category_id,
            "fields": obj,
            "mode": "live",
        }

    if category_id == "segments":
        obj = _api_get(f"segments/{item_id}", {"rsid": rsid, "locale": "en_US"})
        return {
            "name": item_id,
            "label": obj.get("name", item_id),
            "category": category_id,
            "fields": obj,
            "mode": "live",
        }

    raise LookupError(f"Cannot get detail for category '{category_id}'.")

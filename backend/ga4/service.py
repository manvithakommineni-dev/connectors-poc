"""
Google Analytics 4 (GA4) connectivity and metadata retrieval service.

How GA4 exposes metadata:
  GA4 uses two Google APIs for metadata:

  1. Google Analytics Data API — Metadata endpoint
     GET https://analyticsdata.googleapis.com/v1beta/properties/{propertyId}/metadata
     Returns all queryable dimensions and metrics for a property.

  2. Google Analytics Admin API — Property configuration
     GET .../properties/{propertyId}                          → property info
     GET .../properties/{propertyId}/customDimensions       → custom dimensions
     GET .../properties/{propertyId}/customMetrics          → custom metrics
     GET .../properties/{propertyId}/dataStreams            → web/app data streams

  GA4 concept equivalents:
    Salesforce SObject  → GA4 Dimension / Metric / Event
    Salesforce Field    → GA4 Dimension apiName / Metric apiName
    Database Table      → GA4 Event (grouped by eventName dimension)

  Authentication (FREE — no payment required):
    1. Create GA4 property at https://analytics.google.com
    2. Google Cloud project → enable Analytics Data API + Analytics Admin API
    3. Create service account → download JSON key
    4. Add service account email to GA4 Admin → Property Access Management → Viewer
    Required env vars: GA4_PROPERTY_ID, GA4_SERVICE_ACCOUNT_FILE
"""

import logging
import os
from functools import lru_cache

import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

from core.config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
DATA_API_BASE = "https://analyticsdata.googleapis.com/v1beta"
ADMIN_API_BASE = "https://analyticsadmin.googleapis.com/v1beta"

METADATA_CATEGORIES = [
    {
        "id": "dimensions",
        "label": "Dimensions",
        "description": "Attributes that describe user sessions and events (country, device, page, event name)",
    },
    {
        "id": "metrics",
        "label": "Metrics",
        "description": "Quantitative measurements (activeUsers, sessions, conversions, revenue)",
    },
    {
        "id": "custom_dimensions",
        "label": "Custom Dimensions",
        "description": "User-defined dimensions configured in GA4 Admin",
    },
    {
        "id": "custom_metrics",
        "label": "Custom Metrics",
        "description": "User-defined metrics configured in GA4 Admin",
    },
    {
        "id": "data_streams",
        "label": "Data Streams",
        "description": "Web, iOS, and Android data collection streams for this property",
    },
]


def _property_path() -> str:
    pid = settings.GA4_PROPERTY_ID.strip()
    if pid.startswith("properties/"):
        return pid
    return f"properties/{pid}"


def _property_id_numeric() -> str:
    return _property_path().replace("properties/", "")


def _check_config() -> None:
    if not settings.GA4_PROPERTY_ID:
        raise ConnectionError(
            "GA4_PROPERTY_ID is not set in .env. "
            "Find it in GA4 → Admin → Property Settings (numeric ID)."
        )
    if not settings.GA4_SERVICE_ACCOUNT_FILE:
        raise ConnectionError(
            "GA4_SERVICE_ACCOUNT_FILE is not set in .env. "
            "Download a service account JSON key from Google Cloud Console."
        )
    if not os.path.isfile(settings.GA4_SERVICE_ACCOUNT_FILE):
        raise ConnectionError(
            f"Service account file not found: {settings.GA4_SERVICE_ACCOUNT_FILE}"
        )


def _get_access_token() -> str:
    _check_config()
    creds = service_account.Credentials.from_service_account_file(
        settings.GA4_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds.token


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_access_token()}",
        "Content-Type": "application/json",
    }


def _get(url: str) -> dict:
    resp = requests.get(url, headers=_headers(), timeout=30)
    if resp.status_code == 401:
        raise ConnectionError(
            "GA4 authentication failed. Check service account JSON and that the "
            "service account email is added to GA4 Property Access with Viewer role."
        )
    if resp.status_code == 403:
        raise PermissionError(
            f"GA4 access denied [{url}]. Ensure Analytics Data API and "
            "Analytics Admin API are enabled in Google Cloud, and the service "
            "account has Viewer access on the GA4 property."
        )
    if resp.status_code == 404:
        raise LookupError(
            f"GA4 property not found. Check GA4_PROPERTY_ID={settings.GA4_PROPERTY_ID}"
        )
    if not resp.ok:
        raise RuntimeError(f"GA4 API error [{resp.status_code}]: {resp.text[:400]}")
    return resp.json()


@lru_cache(maxsize=1)
def _fetch_metadata() -> dict:
    url = f"{DATA_API_BASE}/{_property_path()}/metadata"
    return _get(url)


def _normalize_dimension(d: dict) -> dict:
    return {
        "name": d.get("apiName", ""),
        "label": d.get("uiName", d.get("apiName", "")),
        "description": d.get("description", ""),
        "category": d.get("category", ""),
        "custom_definition": d.get("customDefinition", False),
        "deprecated": bool(d.get("deprecatedApiNames")),
    }


def _normalize_metric(m: dict) -> dict:
    return {
        "name": m.get("apiName", ""),
        "label": m.get("uiName", m.get("apiName", "")),
        "description": m.get("description", ""),
        "type": m.get("type", ""),
        "expression": m.get("expression", ""),
        "custom_definition": m.get("customDefinition", False),
        "deprecated": bool(m.get("deprecatedApiNames")),
    }


def test_connection() -> dict:
    _check_config()
    prop = _get(f"{ADMIN_API_BASE}/{_property_path()}")
    metadata = _fetch_metadata()
    dimensions = metadata.get("dimensions", [])
    metrics = metadata.get("metrics", [])

    return {
        "connected": True,
        "mode": "live",
        "property_id": _property_id_numeric(),
        "property_name": prop.get("displayName", ""),
        "time_zone": prop.get("timeZone", ""),
        "currency_code": prop.get("currencyCode", ""),
        "industry_category": prop.get("industryCategory", ""),
        "service_level": prop.get("serviceLevel", ""),
        "dimensions_count": len(dimensions),
        "metrics_count": len(metrics),
        "auth_method": "Service Account (Google Cloud JSON key)",
    }


def list_categories() -> list[dict]:
    _check_config()
    metadata = _fetch_metadata()
    custom_dims = _list_custom_dimensions_raw()
    custom_metrics = _list_custom_metrics_raw()
    streams = _list_data_streams_raw()

    counts = {
        "dimensions": len(metadata.get("dimensions", [])),
        "metrics": len(metadata.get("metrics", [])),
        "custom_dimensions": len(custom_dims),
        "custom_metrics": len(custom_metrics),
        "data_streams": len(streams),
    }

    return [
        {**cat, "items_count": counts.get(cat["id"], 0)}
        for cat in METADATA_CATEGORIES
    ]


def list_items(category_id: str) -> dict:
    _check_config()
    if category_id == "dimensions":
        items = [_normalize_dimension(d) for d in _fetch_metadata().get("dimensions", [])]
    elif category_id == "metrics":
        items = [_normalize_metric(m) for m in _fetch_metadata().get("metrics", [])]
    elif category_id == "custom_dimensions":
        items = [_normalize_custom_dimension(d) for d in _list_custom_dimensions_raw()]
    elif category_id == "custom_metrics":
        items = [_normalize_custom_metric(m) for m in _list_custom_metrics_raw()]
    elif category_id == "data_streams":
        items = [_normalize_data_stream(s) for s in _list_data_streams_raw()]
    else:
        raise LookupError(
            f"Category '{category_id}' not found. "
            f"Available: {[c['id'] for c in METADATA_CATEGORIES]}"
        )

    return {
        "category": category_id,
        "total": len(items),
        "items": items,
        "mode": "live",
    }


def get_item_detail(category_id: str, item_name: str) -> dict:
    result = list_items(category_id)
    for item in result["items"]:
        if item["name"] == item_name:
            return {**item, "category": category_id, "mode": "live"}
    raise LookupError(f"Item '{item_name}' not found in category '{category_id}'.")


def _list_custom_dimensions_raw() -> list:
    url = f"{ADMIN_API_BASE}/{_property_path()}/customDimensions"
    data = _get(url)
    return data.get("customDimensions", [])


def _list_custom_metrics_raw() -> list:
    url = f"{ADMIN_API_BASE}/{_property_path()}/customMetrics"
    data = _get(url)
    return data.get("customMetrics", [])


def _list_data_streams_raw() -> list:
    url = f"{ADMIN_API_BASE}/{_property_path()}/dataStreams"
    data = _get(url)
    return data.get("dataStreams", [])


def _normalize_custom_dimension(d: dict) -> dict:
    return {
        "name": d.get("parameterName", d.get("name", "").split("/")[-1]),
        "label": d.get("displayName", ""),
        "description": d.get("description", ""),
        "scope": d.get("scope", ""),
        "disallow_ads_personalization": d.get("disallowAdsPersonalization", False),
        "resource_name": d.get("name", ""),
    }


def _normalize_custom_metric(m: dict) -> dict:
    return {
        "name": m.get("parameterName", m.get("name", "").split("/")[-1]),
        "label": m.get("displayName", ""),
        "description": m.get("description", ""),
        "scope": m.get("scope", ""),
        "measurement_unit": m.get("measurementUnit", ""),
        "resource_name": m.get("name", ""),
    }


def _normalize_data_stream(s: dict) -> dict:
    stream_type = s.get("type", "")
    web = s.get("webStreamData", {})
    app = s.get("androidAppStreamData") or s.get("iosAppStreamData") or {}
    return {
        "name": s.get("name", "").split("/")[-1],
        "label": s.get("displayName", ""),
        "description": f"{stream_type} data stream",
        "type": stream_type,
        "stream_id": s.get("name", "").split("/")[-1],
        "measurement_id": web.get("measurementId", ""),
        "default_uri": web.get("defaultUri", ""),
        "firebase_app_id": app.get("firebaseAppId", ""),
        "resource_name": s.get("name", ""),
    }

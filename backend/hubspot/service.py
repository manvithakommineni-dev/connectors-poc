"""
HubSpot connectivity and metadata retrieval service.

Authentication strategy:
  Personal Access Key (Bearer token) stored in HS_ACCESS_TOKEN env variable.
  This is the simplest auth — a single long-lived token scoped to one account.

Key APIs used:
  GET https://api.hubapi.com/account-info/v3/details         → portal/account info
  GET https://api.hubapi.com/crm/v3/schemas                  → all custom object schemas
  GET https://api.hubapi.com/crm/v3/properties/{objectType}  → properties (fields) for an object
  GET https://api.hubapi.com/crm/v3/objects/{objectType}     → sample records
"""

import requests
import logging
from core.config import settings

logger = logging.getLogger(__name__)

HUBSPOT_BASE = "https://api.hubapi.com"

STANDARD_OBJECTS = [
    "contacts",
    "companies",
    "deals",
    "tickets",
    "products",
    "line_items",
    "quotes",
    "calls",
    "emails",
    "meetings",
    "notes",
    "tasks",
]


def _headers() -> dict:
    """Return authorization headers using the Personal Access Key."""
    return {
        "Authorization": f"Bearer {settings.HS_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def _get(path: str, params: dict = None) -> dict:
    """Make an authenticated GET request to HubSpot API."""
    url = f"{HUBSPOT_BASE}{path}"
    resp = requests.get(url, headers=_headers(), params=params or {})
    if resp.status_code == 401:
        raise ConnectionError(
            "HubSpot authentication failed. Check HS_ACCESS_TOKEN in your .env file."
        )
    if resp.status_code == 403:
        raise PermissionError(
            f"HubSpot access denied for {path}. The token may lack required scopes."
        )
    if not resp.ok:
        raise RuntimeError(
            f"HubSpot API error [{resp.status_code}] on {path}: {resp.text[:300]}"
        )
    return resp.json()


def test_connection() -> dict:
    """Return HubSpot portal info to confirm connectivity."""
    data = _get("/account-info/v3/details")
    return {
        "connected": True,
        "portal_id": data.get("portalId"),
        "account_type": data.get("accountType"),
        "time_zone": data.get("timeZone"),
        "company_currency": data.get("companyCurrency"),
        "ui_domain": data.get("uiDomain"),
        "data_hosting_location": data.get("dataHostingLocation"),
        "auth_method": "Personal Access Key (Bearer Token)",
    }


def get_all_object_types() -> list[dict]:
    """
    Return all object types: standard built-in objects + any custom schemas.
    Standard objects are hardcoded (HubSpot doesn't have a single 'list all' endpoint for them).
    Custom schemas come from /crm/v3/schemas.
    """
    result = []

    # Standard objects
    for name in STANDARD_OBJECTS:
        result.append(
            {
                "name": name,
                "label": name.replace("_", " ").title(),
                "object_type_id": name,
                "type": "standard",
            }
        )

    # Custom objects
    try:
        schemas_data = _get("/crm/v3/schemas")
        for schema in schemas_data.get("results", []):
            result.append(
                {
                    "name": schema.get("name"),
                    "label": schema.get("labels", {}).get("singular", schema.get("name")),
                    "object_type_id": schema.get("objectTypeId"),
                    "type": "custom",
                }
            )
    except Exception as e:
        logger.warning("Could not fetch custom schemas: %s", e)

    return result


def get_object_properties(object_type: str) -> dict:
    """
    Retrieve all properties (fields) for a HubSpot object type.
    Equivalent to Salesforce's describe/fields endpoint.
    """
    data = _get(f"/crm/v3/properties/{object_type}")
    properties = []
    for prop in data.get("results", []):
        properties.append(
            {
                "name": prop.get("name"),
                "label": prop.get("label"),
                "type": prop.get("type"),
                "field_type": prop.get("fieldType"),
                "description": prop.get("description", ""),
                "group_name": prop.get("groupName"),
                "options": (
                    [o.get("value") for o in prop.get("options", [])]
                    if prop.get("options")
                    else []
                ),
                "created_at": prop.get("createdAt"),
                "updated_at": prop.get("updatedAt"),
                "calculated": prop.get("calculated", False),
                "external_options": prop.get("externalOptions", False),
                "hidden": prop.get("hidden", False),
                "hubspot_defined": prop.get("hubspotDefined", False),
                "show_currency_symbol": prop.get("showCurrencySymbol", False),
                "modification_metadata": prop.get("modificationMetadata", {}),
                "form_field": prop.get("formField", False),
            }
        )
    return {
        "object_type": object_type,
        "properties_count": len(properties),
        "properties": properties,
    }


def get_object_schema(object_type: str) -> dict:
    """
    Full schema for a custom object (includes associations, properties, labels).
    For standard objects, falls back to properties only.
    """
    # Try custom schema first
    try:
        schemas_data = _get("/crm/v3/schemas")
        for schema in schemas_data.get("results", []):
            if schema.get("name") == object_type or schema.get("objectTypeId") == object_type:
                props = get_object_properties(object_type)
                return {
                    "name": schema.get("name"),
                    "object_type_id": schema.get("objectTypeId"),
                    "labels": schema.get("labels", {}),
                    "primary_display_property": schema.get("primaryDisplayProperty"),
                    "secondary_display_properties": schema.get("secondaryDisplayProperties", []),
                    "associations": schema.get("associations", []),
                    "type": "custom",
                    **props,
                }
    except Exception:
        pass

    # Standard object — return properties
    props = get_object_properties(object_type)
    return {
        "name": object_type,
        "type": "standard",
        **props,
    }


def get_object_sample_data(object_type: str, limit: int = 5) -> dict:
    """Fetch sample CRM records for a given object type."""
    # Get first 10 property names to include in the response
    try:
        props_data = get_object_properties(object_type)
        prop_names = [p["name"] for p in props_data["properties"][:10]]
    except Exception:
        prop_names = []

    params = {"limit": limit}
    if prop_names:
        params["properties"] = ",".join(prop_names)

    data = _get(f"/crm/v3/objects/{object_type}", params=params)
    return {
        "object_type": object_type,
        "total": data.get("total", 0),
        "records": data.get("results", []),
        "paging": data.get("paging"),
    }

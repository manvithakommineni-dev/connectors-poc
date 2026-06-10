"""
SAP connectivity and metadata retrieval service.

Authentication strategy:
  API Key header (APIKey: <key>) — used with SAP Business Accelerator Hub sandbox.
  Basic Auth (username + password) — used with on-premise SAP or SAP BTP systems.

How SAP exposes metadata:
  SAP uses OData (Open Data Protocol). Every OData service exposes a $metadata endpoint
  that returns an EDMX XML document describing:
    - EntityTypes  → equivalent to database tables / Salesforce SObjects
    - Properties   → equivalent to columns / fields
    - Key fields   → primary key columns
    - NavigationProperties → relationships / foreign keys
    - EntitySets   → the queryable collections (EntityType + container binding)

Sandbox setup (free, no SAP license needed):
  1. Go to https://api.sap.com and create a free account
  2. Log in → click your avatar (top right) → "Settings" → "Show API Key"
  3. Copy the API Key → set SAP_API_KEY in backend/.env
  4. The sandbox base URL is: https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap

Supported SAP OData services (pre-configured for sandbox):
  API_BUSINESS_PARTNER       → Business Partners (customers, vendors, contacts)
  API_SALES_ORDER_SRV        → Sales Orders
  API_PRODUCT_SRV            → Products / Materials
  API_PURCHASEORDER_PROCESS_SRV → Purchase Orders
  API_SUPPLIER_SRV           → Suppliers
  API_CUSTOMERRETURN_SRV     → Customer Returns
"""

import xml.etree.ElementTree as ET
import requests
import logging
from core.config import settings
from typing import Optional

logger = logging.getLogger(__name__)

# SAP Business Accelerator Hub sandbox base URL
SAP_SANDBOX_BASE = "https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap"

# Well-known SAP S/4HANA OData services available in the sandbox
KNOWN_SERVICES = [
    {
        "name": "API_BUSINESS_PARTNER",
        "label": "Business Partner",
        "description": "Master data for business partners (customers, vendors, contacts)",
    },
    {
        "name": "API_SALES_ORDER_SRV",
        "label": "Sales Orders",
        "description": "Sales order headers, items, schedules, and partners",
    },
    {
        "name": "API_PRODUCT_SRV",
        "label": "Products / Materials",
        "description": "Product master data including plant, storage, and valuation",
    },
    {
        "name": "API_PURCHASEORDER_PROCESS_SRV",
        "label": "Purchase Orders",
        "description": "Purchase order process with items, account assignment, and scheduling",
    },
    {
        "name": "API_SUPPLIER_SRV",
        "label": "Suppliers",
        "description": "Supplier master data including purchasing organisation data",
    },
    {
        "name": "API_ODATA_SAP_FINANCIAL_SRV",
        "label": "Financial Data",
        "description": "General ledger accounts and financial posting data",
    },
]

# EDMX XML namespaces used in SAP OData metadata responses
NS = {
    "edmx": "http://schemas.microsoft.com/ado/2007/06/edmx",
    "edm": "http://schemas.microsoft.com/ado/2008/09/edm",
    "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
}


def _headers() -> dict:
    """Build request headers based on configured auth type."""
    headers = {"Accept": "application/xml"}
    if settings.SAP_AUTH_TYPE == "apikey" and settings.SAP_API_KEY:
        headers["APIKey"] = settings.SAP_API_KEY
    return headers


def _auth() -> Optional[tuple]:
    """Return (username, password) tuple for Basic Auth, or None."""
    if settings.SAP_AUTH_TYPE == "basic" and settings.SAP_USERNAME and settings.SAP_PASSWORD:
        return (settings.SAP_USERNAME, settings.SAP_PASSWORD)
    return None


def _base_url() -> str:
    """Return the configured SAP base URL (custom or default sandbox)."""
    return (settings.SAP_BASE_URL.rstrip("/") if settings.SAP_BASE_URL else SAP_SANDBOX_BASE)


def _fetch_metadata_xml(service_name: str) -> str:
    """
    Fetch the raw EDMX XML from the SAP OData $metadata endpoint.
    Raises ConnectionError / RuntimeError on failure.
    """
    url = f"{_base_url()}/{service_name}/$metadata"
    logger.info("Fetching SAP metadata from: %s", url)

    try:
        resp = requests.get(url, headers=_headers(), auth=_auth(), timeout=30)
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(f"Cannot reach SAP system at {_base_url()}: {e}")
    except requests.exceptions.Timeout:
        raise ConnectionError(f"SAP request timed out for service '{service_name}'")

    if resp.status_code == 401:
        raise ConnectionError(
            "SAP authentication failed. Check SAP_API_KEY (or SAP_USERNAME/SAP_PASSWORD) in .env"
        )
    if resp.status_code == 403:
        raise PermissionError(
            f"SAP access denied for service '{service_name}'. Verify API key permissions."
        )
    if resp.status_code == 404:
        raise LookupError(
            f"SAP OData service '{service_name}' not found. "
            "Check the service name or use /api/v1/sap/services to list available ones."
        )
    if not resp.ok:
        raise RuntimeError(
            f"SAP API error [{resp.status_code}] for service '{service_name}': {resp.text[:500]}"
        )
    return resp.text


def _parse_metadata(xml_text: str) -> dict:
    """
    Parse EDMX XML and extract:
      - entity_types  : list of EntityType objects (tables) with key fields + all properties
      - entity_sets   : list of EntitySet names (the queryable collections)
      - namespace     : schema namespace
      - total_entities: count of entity types
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse SAP EDMX XML: {e}")

    # Locate Schema element (may have or lack namespace)
    schema = root.find(".//{http://schemas.microsoft.com/ado/2008/09/edm}Schema")
    if schema is None:
        # Try without namespace (some SAP services omit it)
        schema = root.find(".//Schema")
    if schema is None:
        raise ValueError("Could not find Schema element in SAP EDMX metadata")

    namespace = schema.get("Namespace", "")

    # ---- Parse EntityTypes ----
    entity_types = []
    for et in schema.findall("{http://schemas.microsoft.com/ado/2008/09/edm}EntityType"):
        et_name = et.get("Name", "")

        # Key fields
        key_refs = []
        key_el = et.find("{http://schemas.microsoft.com/ado/2008/09/edm}Key")
        if key_el is not None:
            for pr in key_el.findall("{http://schemas.microsoft.com/ado/2008/09/edm}PropertyRef"):
                key_refs.append(pr.get("Name", ""))

        # Properties (fields)
        properties = []
        for prop in et.findall("{http://schemas.microsoft.com/ado/2008/09/edm}Property"):
            raw_type = prop.get("Type", "")
            # strip namespace prefix e.g. "Edm.String" → "String"
            simple_type = raw_type.split(".")[-1] if "." in raw_type else raw_type
            properties.append(
                {
                    "name": prop.get("Name", ""),
                    "type": raw_type,
                    "simple_type": simple_type,
                    "nullable": prop.get("Nullable", "true").lower() != "false",
                    "max_length": prop.get("MaxLength"),
                    "precision": prop.get("Precision"),
                    "scale": prop.get("Scale"),
                    "is_key": prop.get("Name", "") in key_refs,
                    "label": prop.get(
                        "{http://www.sap.com/Protocols/SAPData}label",
                        prop.get("Name", ""),
                    ),
                    "creatable": prop.get(
                        "{http://www.sap.com/Protocols/SAPData}creatable", "true"
                    ),
                    "updatable": prop.get(
                        "{http://www.sap.com/Protocols/SAPData}updatable", "true"
                    ),
                    "filterable": prop.get(
                        "{http://www.sap.com/Protocols/SAPData}filterable", "true"
                    ),
                    "sortable": prop.get(
                        "{http://www.sap.com/Protocols/SAPData}sortable", "true"
                    ),
                }
            )

        # Navigation properties (relationships)
        nav_props = []
        for nav in et.findall("{http://schemas.microsoft.com/ado/2008/09/edm}NavigationProperty"):
            nav_props.append(
                {
                    "name": nav.get("Name", ""),
                    "relationship": nav.get("Relationship", ""),
                    "from_role": nav.get("FromRole", ""),
                    "to_role": nav.get("ToRole", ""),
                }
            )

        entity_types.append(
            {
                "name": et_name,
                "key_fields": key_refs,
                "fields_count": len(properties),
                "fields": properties,
                "navigation_properties": nav_props,
                "nav_properties_count": len(nav_props),
            }
        )

    # ---- Parse EntitySets (the actual queryable collections) ----
    entity_sets = []
    container = schema.find("{http://schemas.microsoft.com/ado/2008/09/edm}EntityContainer")
    if container is not None:
        for es in container.findall("{http://schemas.microsoft.com/ado/2008/09/edm}EntitySet"):
            et_type = es.get("EntityType", "").replace(f"{namespace}.", "")
            entity_sets.append(
                {
                    "name": es.get("Name", ""),
                    "entity_type": et_type,
                }
            )

    # Build a lookup map: EntitySet name → EntityType name
    set_to_type = {es["name"]: es["entity_type"] for es in entity_sets}
    type_to_set = {es["entity_type"]: es["name"] for es in entity_sets}

    # Attach entity_set_name to each entity_type for convenience
    for et in entity_types:
        et["entity_set_name"] = type_to_set.get(et["name"], "")

    return {
        "namespace": namespace,
        "entity_types": entity_types,
        "entity_sets": entity_sets,
        "total_entity_types": len(entity_types),
        "total_entity_sets": len(entity_sets),
    }


# ─────────────────────────────────────────────
# Public service functions
# ─────────────────────────────────────────────

def test_connection() -> dict:
    """
    Test SAP connectivity by fetching metadata for the first known service.
    Returns config summary and connectivity status.
    """
    base = _base_url()
    auth_type = settings.SAP_AUTH_TYPE or "apikey"

    # Try to fetch metadata for the business partner service as a health check
    try:
        xml_text = _fetch_metadata_xml("API_BUSINESS_PARTNER")
        parsed = _parse_metadata(xml_text)
        return {
            "connected": True,
            "base_url": base,
            "auth_type": auth_type,
            "test_service": "API_BUSINESS_PARTNER",
            "entity_types_found": parsed["total_entity_types"],
            "entity_sets_found": parsed["total_entity_sets"],
            "namespace": parsed["namespace"],
        }
    except Exception as e:
        raise ConnectionError(f"SAP connection test failed: {e}")


def list_services() -> list[dict]:
    """Return the list of pre-configured SAP OData services."""
    return KNOWN_SERVICES


def get_service_metadata(service_name: str) -> dict:
    """
    Full metadata for a SAP OData service:
    entity types, entity sets, fields, key fields, navigation properties.
    """
    xml_text = _fetch_metadata_xml(service_name)
    parsed = _parse_metadata(xml_text)
    parsed["service_name"] = service_name
    return parsed


def get_service_entities(service_name: str) -> dict:
    """
    Lightweight list of entity types for a service (no field details).
    Useful for populating the left-panel object list in the UI.
    """
    xml_text = _fetch_metadata_xml(service_name)
    parsed = _parse_metadata(xml_text)

    entities_summary = [
        {
            "name": et["name"],
            "entity_set_name": et["entity_set_name"],
            "fields_count": et["fields_count"],
            "key_fields": et["key_fields"],
            "nav_properties_count": et["nav_properties_count"],
        }
        for et in parsed["entity_types"]
    ]

    return {
        "service_name": service_name,
        "namespace": parsed["namespace"],
        "total": len(entities_summary),
        "entities": entities_summary,
    }


def get_entity_fields(service_name: str, entity_name: str) -> dict:
    """
    Fields (properties) for a specific EntityType within a SAP OData service.
    entity_name can be either the EntityType name or the EntitySet name.
    """
    xml_text = _fetch_metadata_xml(service_name)
    parsed = _parse_metadata(xml_text)

    # Allow lookup by EntitySet name OR EntityType name
    set_to_type = {es["entity_set_name"]: es["name"] for es in parsed["entity_types"]}
    resolved_name = set_to_type.get(entity_name, entity_name)

    for et in parsed["entity_types"]:
        if et["name"] == resolved_name:
            return {
                "service_name": service_name,
                "entity_type": et["name"],
                "entity_set": et["entity_set_name"],
                "key_fields": et["key_fields"],
                "fields_count": et["fields_count"],
                "fields": et["fields"],
                "navigation_properties": et["navigation_properties"],
            }

    raise LookupError(
        f"Entity '{entity_name}' not found in service '{service_name}'. "
        f"Available: {[e['name'] for e in parsed['entity_types'][:10]]}"
    )

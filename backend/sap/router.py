from fastapi import APIRouter, HTTPException, Query
from sap.service import (
    test_connection,
    list_services,
    get_service_metadata,
    get_service_entities,
    get_entity_fields,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sap", tags=["SAP"])


def _handle(fn, *args, **kwargs):
    """Unified error handler — maps service exceptions to HTTP status codes."""
    try:
        return fn(*args, **kwargs)
    except ConnectionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SAP error: {str(e)}")


@router.get("/connect")
def connect():
    """
    Test SAP OData connectivity.
    Fetches metadata from API_BUSINESS_PARTNER service as a health check.
    Returns base URL, auth type, and entity count from the test service.

    Setup:
      1. Go to https://api.sap.com → sign up (free)
      2. Log in → avatar → Settings → Show API Key
      3. Add SAP_API_KEY=<your_key> to backend/.env
    """
    return _handle(test_connection)


@router.get("/services")
def services():
    """
    List all pre-configured SAP OData services.
    Each service is an independent OData endpoint with its own set of entity types.

    These services are available on the SAP Business Accelerator Hub sandbox
    (https://sandbox.api.sap.com) with a free API key.
    """
    result = list_services()
    return {"total": len(result), "services": result}


@router.get("/services/{service_name}/metadata")
def service_metadata(service_name: str):
    """
    Full EDMX metadata for a SAP OData service.
    Returns all EntityTypes (tables), EntitySets, and their complete field definitions.

    This is the equivalent of Salesforce's global describe or HubSpot's schemas endpoint.
    """
    return _handle(get_service_metadata, service_name)


@router.get("/services/{service_name}/entities")
def service_entities(service_name: str):
    """
    Lightweight list of EntityTypes in a SAP OData service.
    Returns entity names, field counts, key fields — no full field details.
    Use this to populate the object list in the UI.
    """
    return _handle(get_service_entities, service_name)


@router.get("/services/{service_name}/entities/{entity_name}/fields")
def entity_fields(service_name: str, entity_name: str):
    """
    All fields (Properties) for a specific EntityType in a SAP OData service.

    entity_name can be:
      - The EntityType name  (e.g. A_BusinessPartnerType)
      - The EntitySet name   (e.g. A_BusinessPartner)

    Returns: key fields, field name/type/nullable/length, SAP-specific attributes
    (filterable, sortable, creatable, updatable), and navigation properties (relationships).
    """
    return _handle(get_entity_fields, service_name, entity_name)

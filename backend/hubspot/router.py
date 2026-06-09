from fastapi import APIRouter, HTTPException, Query
from hubspot.service import (
    test_connection,
    get_all_object_types,
    get_object_properties,
    get_object_schema,
    get_object_sample_data,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hubspot", tags=["HubSpot"])


def _handle(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ConnectionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HubSpot error: {str(e)}")


@router.get("/connect")
def connect():
    """
    Test HubSpot connectivity.
    Returns portal/account info using the Personal Access Key from .env.
    """
    return _handle(test_connection)


@router.get("/objects")
def list_objects():
    """
    List all HubSpot object types.
    Returns standard built-in objects (contacts, deals, companies, etc.)
    plus any custom object schemas defined in the portal.
    """
    return _handle(lambda: {"objects": get_all_object_types(), "total": len(get_all_object_types())})


@router.get("/objects/{object_type}/properties")
def object_properties(object_type: str):
    """
    List all properties (fields) for a HubSpot object type.
    Equivalent to Salesforce's fields/describe endpoint.

    Standard types: contacts, companies, deals, tickets, products,
                    line_items, quotes, calls, emails, meetings, notes, tasks
    """
    return _handle(get_object_properties, object_type)


@router.get("/objects/{object_type}/schema")
def object_schema(object_type: str):
    """
    Full schema for a HubSpot object: properties, labels, associations (for custom objects).
    """
    return _handle(get_object_schema, object_type)


@router.get("/objects/{object_type}/sample")
def object_sample(
    object_type: str,
    limit: int = Query(5, ge=1, le=50, description="Number of records to return"),
):
    """
    Fetch sample CRM records for a given object type.
    """
    return _handle(get_object_sample_data, object_type, limit)

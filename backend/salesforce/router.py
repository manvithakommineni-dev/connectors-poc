from fastapi import APIRouter, HTTPException, Query
from salesforce.service import (
    get_salesforce_connection,
    get_all_objects,
    get_object_metadata,
    get_object_sample_data,
    test_connection,
)
from simple_salesforce.exceptions import SalesforceAuthenticationFailed
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/salesforce", tags=["Salesforce"])


def _get_sf():
    try:
        return get_salesforce_connection()
    except SalesforceAuthenticationFailed as e:
        raise HTTPException(status_code=401, detail=f"Salesforce authentication failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not connect to Salesforce: {str(e)}")


@router.get("/ping")
def ping():
    """Health check — confirm backend is alive."""
    return {"status": "ok", "connector": "salesforce"}


@router.get("/connect")
def connect():
    """
    Test Salesforce connectivity.
    Returns org info: instance URL, API version, total object count.
    """
    sf = _get_sf()
    return test_connection(sf)


@router.get("/objects")
def list_objects(
    queryable_only: bool = Query(True, description="Return only queryable objects"),
    custom_only: bool = Query(False, description="Return only custom objects"),
):
    """
    List all SObjects (tables) in the Salesforce org.
    Optionally filter to queryable-only or custom-only.
    """
    sf = _get_sf()
    objects = get_all_objects(sf)

    if queryable_only:
        objects = [o for o in objects if o["queryable"]]
    if custom_only:
        objects = [o for o in objects if o["custom"]]

    return {
        "total": len(objects),
        "objects": objects,
    }


@router.get("/objects/{object_name}/metadata")
def object_metadata(object_name: str):
    """
    Retrieve full metadata for a Salesforce object:
    fields (name, type, length, nillable, etc.), child relationships, record types.
    """
    sf = _get_sf()
    try:
        return get_object_metadata(sf, object_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Object '{object_name}' not found or error: {str(e)}")


@router.get("/objects/{object_name}/sample")
def object_sample_data(
    object_name: str,
    limit: int = Query(5, ge=1, le=50, description="Number of sample rows"),
):
    """
    Fetch sample rows from a Salesforce object using SOQL.
    """
    sf = _get_sf()
    try:
        return get_object_sample_data(sf, object_name, limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not query '{object_name}': {str(e)}")


@router.get("/objects/{object_name}/fields")
def object_fields(object_name: str):
    """
    Return just the fields list for a Salesforce object (lightweight version of /metadata).
    """
    sf = _get_sf()
    try:
        meta = get_object_metadata(sf, object_name)
        return {
            "object": object_name,
            "fields_count": meta["fields_count"],
            "fields": meta["fields"],
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

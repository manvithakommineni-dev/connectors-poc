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
    except ConnectionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not connect to Salesforce: {str(e)}")


@router.get("/ping")
def ping():
    """Health check — confirm backend is alive."""
    return {"status": "ok", "connector": "salesforce"}


@router.get("/setup-guide")
def setup_guide():
    """
    Returns the exact steps needed to make the Salesforce credentials work
    for OAuth Username-Password flow (required for newer Salesforce orgs).
    """
    return {
        "title": "Salesforce Connected App Setup — Required Steps",
        "steps": [
            {
                "step": 1,
                "where": "Salesforce org → Setup → Identity → OAuth and OpenID Connect Settings",
                "action": "Enable 'Allow OAuth Username-Password Flows'",
                "note": "Newer orgs (Spring 2023+) have this DISABLED by default.",
            },
            {
                "step": 2,
                "where": "Setup → App Manager → [Your Connected App] → Edit",
                "action": "Enable 'Enable OAuth Username-Password Flows' checkbox",
                "note": "Must be enabled at the Connected App level too.",
            },
            {
                "step": 3,
                "where": "My Settings → Personal → Reset My Security Token",
                "action": "Reset and get a new security token (emailed to you)",
                "note": "Token resets whenever you change the password. Update SF_SECURITY_TOKEN in .env",
            },
            {
                "step": 4,
                "where": "backend/.env",
                "action": "Confirm SF_USERNAME, SF_PASSWORD, SF_SECURITY_TOKEN, SF_CONSUMER_KEY, SF_CONSUMER_SECRET are correct",
                "note": "Password in .env must NOT include the security token — the code appends it automatically.",
            },
        ],
        "env_keys_needed": [
            "SF_USERNAME", "SF_PASSWORD", "SF_SECURITY_TOKEN",
            "SF_CONSUMER_KEY", "SF_CONSUMER_SECRET", "SF_INSTANCE_URL",
        ],
        "docs": "https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_username_password_flow.htm",
    }


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

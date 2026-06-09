from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from salesforce.service import (
    get_salesforce_connection,
    get_all_objects,
    get_object_metadata,
    get_object_sample_data,
    test_connection,
    get_auth_url,
    exchange_code_for_token,
    store_token,
    get_stored_token,
    clear_token,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/salesforce", tags=["Salesforce"])


def _get_sf():
    try:
        return get_salesforce_connection()
    except ConnectionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Salesforce error: {str(e)}")


# ── OAuth Flow ────────────────────────────────────────────────────────────────

@router.get("/auth")
def salesforce_login():
    """
    Step 1: Redirect the browser to Salesforce login page.
    Visit http://localhost:8000/api/v1/salesforce/auth in your browser.
    After login, Salesforce redirects back and the token is stored automatically.
    """
    url = get_auth_url()
    logger.info("Redirecting to Salesforce OAuth: %s", url)
    return RedirectResponse(url=url)


@router.get("/oauth/callback")
def oauth_callback(code: str = None, error: str = None, error_description: str = None):
    """
    Step 2: Salesforce redirects here after login with an authorization code.
    The code is exchanged for an access token automatically.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error} — {error_description}")
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received from Salesforce.")

    try:
        token_data = exchange_code_for_token(code)
        store_token(
            access_token=token_data["access_token"],
            instance_url=token_data["instance_url"],
            refresh_token=token_data.get("refresh_token", ""),
        )
        return HTMLResponse(content="""
        <html><body style="font-family:sans-serif;max-width:600px;margin:60px auto;text-align:center;">
            <h2 style="color:#2e7d32">✅ Salesforce Connected Successfully!</h2>
            <p>You are now authenticated. You can close this tab.</p>
            <p>Test the connection: <a href="/api/v1/salesforce/connect">/api/v1/salesforce/connect</a></p>
            <p>View all objects: <a href="/api/v1/salesforce/objects">/api/v1/salesforce/objects</a></p>
            <p>API docs: <a href="/docs">/docs</a></p>
        </body></html>
        """)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")


@router.get("/auth/status")
def auth_status():
    """Check if the backend is currently authenticated with Salesforce."""
    token = get_stored_token()
    if token:
        return {"authenticated": True, "instance_url": token["instance_url"]}
    return {
        "authenticated": False,
        "message": "Not authenticated. Visit http://localhost:8000/api/v1/salesforce/auth to log in.",
    }


@router.get("/auth/logout")
def logout():
    """Clear the stored Salesforce session."""
    clear_token()
    return {"message": "Logged out. Visit /api/v1/salesforce/auth to re-authenticate."}


# ── Metadata Endpoints ────────────────────────────────────────────────────────

@router.get("/connect")
def connect():
    """Test Salesforce connectivity. Returns org info."""
    sf = _get_sf()
    return test_connection(sf)


@router.get("/objects")
def list_objects(
    queryable_only: bool = Query(True, description="Return only queryable objects"),
    custom_only: bool = Query(False, description="Return only custom objects"),
):
    """List all SObjects (tables) in the Salesforce org."""
    sf = _get_sf()
    objects = get_all_objects(sf)
    if queryable_only:
        objects = [o for o in objects if o["queryable"]]
    if custom_only:
        objects = [o for o in objects if o["custom"]]
    return {"total": len(objects), "objects": objects}


@router.get("/objects/{object_name}/metadata")
def object_metadata(object_name: str):
    """Full metadata for a Salesforce object: fields, types, relationships."""
    sf = _get_sf()
    try:
        return get_object_metadata(sf, object_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Object '{object_name}' not found: {str(e)}")


@router.get("/objects/{object_name}/sample")
def object_sample_data(
    object_name: str,
    limit: int = Query(5, ge=1, le=50),
):
    """Fetch sample rows from a Salesforce object using SOQL."""
    sf = _get_sf()
    try:
        return get_object_sample_data(sf, object_name, limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not query '{object_name}': {str(e)}")


@router.get("/objects/{object_name}/fields")
def object_fields(object_name: str):
    """Return just the fields list for a Salesforce object."""
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

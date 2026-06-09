"""
Salesforce connectivity and metadata retrieval service.

Authentication strategy:
  PRIMARY: OAuth 2.0 Authorization Code flow (browser-based login — always works)
    Step 1: User visits /api/v1/salesforce/auth → redirected to Salesforce login
    Step 2: After login, Salesforce redirects to /api/v1/salesforce/oauth/callback
    Step 3: Backend exchanges code for access token and stores it in memory
    Step 4: All API calls use the stored token

  FALLBACK: OAuth 2.0 Client Credentials (if token already stored)
"""

import requests
import logging
import hashlib
import base64
import secrets
from simple_salesforce import Salesforce
from core.config import settings

logger = logging.getLogger(__name__)

# In-memory token store (cleared on server restart)
_token_store: dict = {}
_pkce_store: dict = {}  # stores code_verifier for PKCE flow


def store_token(access_token: str, instance_url: str, refresh_token: str = "") -> None:
    _token_store["access_token"] = access_token
    _token_store["instance_url"] = instance_url
    _token_store["refresh_token"] = refresh_token
    logger.info("Salesforce token stored. Instance: %s", instance_url)


def get_stored_token() -> dict | None:
    if _token_store.get("access_token"):
        return _token_store.copy()
    return None


def clear_token() -> None:
    _token_store.clear()


def _generate_pkce() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge."""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("utf-8")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("utf-8")).digest()
    ).rstrip(b"=").decode("utf-8")
    return code_verifier, code_challenge


def get_auth_url() -> str:
    """Build the Salesforce OAuth Authorization URL for browser redirect (with PKCE)."""
    base = settings.SF_INSTANCE_URL.rstrip("/") if settings.SF_INSTANCE_URL else f"https://{settings.SF_DOMAIN}.salesforce.com"
    code_verifier, code_challenge = _generate_pkce()
    _pkce_store["code_verifier"] = code_verifier
    return (
        f"{base}/services/oauth2/authorize"
        f"?response_type=code"
        f"&client_id={settings.SF_CONSUMER_KEY}"
        f"&redirect_uri={settings.SF_OAUTH_CALLBACK_URL}"
        f"&scope=api"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )


def exchange_code_for_token(code: str) -> dict:
    """Exchange OAuth authorization code for access token."""
    base = settings.SF_INSTANCE_URL.rstrip("/") if settings.SF_INSTANCE_URL else f"https://{settings.SF_DOMAIN}.salesforce.com"
    token_url = f"{base}/services/oauth2/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.SF_CONSUMER_KEY,
        "client_secret": settings.SF_CONSUMER_SECRET,
        "redirect_uri": settings.SF_OAUTH_CALLBACK_URL,
        "code_verifier": _pkce_store.get("code_verifier", ""),
    }
    resp = requests.post(token_url, data=payload)
    if resp.status_code != 200:
        err = resp.json()
        raise ConnectionError(
            f"Token exchange failed [{resp.status_code}]: {err.get('error')}: {err.get('error_description')}"
        )
    return resp.json()


def refresh_access_token() -> str:
    """Use refresh token to get a new access token."""
    refresh_token = _token_store.get("refresh_token")
    if not refresh_token:
        raise ConnectionError("No refresh token stored. Please re-authenticate via /api/v1/salesforce/auth")
    base = settings.SF_INSTANCE_URL.rstrip("/") if settings.SF_INSTANCE_URL else f"https://{settings.SF_DOMAIN}.salesforce.com"
    token_url = f"{base}/services/oauth2/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.SF_CONSUMER_KEY,
        "client_secret": settings.SF_CONSUMER_SECRET,
    }
    resp = requests.post(token_url, data=payload)
    if resp.status_code != 200:
        raise ConnectionError("Token refresh failed. Please re-authenticate via /api/v1/salesforce/auth")
    data = resp.json()
    _token_store["access_token"] = data["access_token"]
    return data["access_token"]


def get_salesforce_connection() -> Salesforce:
    """
    Return an authenticated Salesforce connection.
    Requires prior OAuth login via /api/v1/salesforce/auth endpoint.
    """
    token = get_stored_token()
    if not token:
        raise ConnectionError(
            "Not authenticated. Please visit http://localhost:8000/api/v1/salesforce/auth "
            "in your browser to log in with Salesforce."
        )
    try:
        sf = Salesforce(
            instance_url=token["instance_url"],
            session_id=token["access_token"],
        )
        # Quick check to verify token is still valid
        sf.describe()
        return sf
    except Exception:
        # Try refreshing the token once
        try:
            new_token = refresh_access_token()
            return Salesforce(
                instance_url=token["instance_url"],
                session_id=new_token,
            )
        except Exception:
            clear_token()
            raise ConnectionError(
                "Session expired. Please visit http://localhost:8000/api/v1/salesforce/auth "
                "in your browser to re-authenticate."
            )


def get_all_objects(sf: Salesforce) -> list[dict]:
    """Retrieve all SObjects (tables) from the Salesforce org."""
    describe = sf.describe()
    objects = []
    for obj in describe["sobjects"]:
        objects.append(
            {
                "name": obj["name"],
                "label": obj["label"],
                "label_plural": obj["labelPlural"],
                "queryable": obj["queryable"],
                "createable": obj["createable"],
                "updateable": obj["updateable"],
                "deletable": obj["deletable"],
                "custom": obj["custom"],
                "key_prefix": obj.get("keyPrefix"),
            }
        )
    return objects


def get_object_metadata(sf: Salesforce, object_name: str) -> dict:
    """Full metadata for a specific SObject: fields, child relationships, record types."""
    obj_describe = getattr(sf, object_name).describe()

    fields = []
    for field in obj_describe["fields"]:
        fields.append(
            {
                "name": field["name"],
                "label": field["label"],
                "type": field["type"],
                "length": field.get("length"),
                "precision": field.get("precision"),
                "scale": field.get("scale"),
                "nillable": field["nillable"],
                "unique": field["unique"],
                "custom": field["custom"],
                "default_value": field.get("defaultValue"),
                "picklist_values": (
                    [p["value"] for p in field.get("picklistValues", [])]
                    if field["type"] in ("picklist", "multipicklist")
                    else []
                ),
                "reference_to": field.get("referenceTo", []),
                "relationship_name": field.get("relationshipName"),
                "createable": field["createable"],
                "updateable": field["updateable"],
                "filterable": field["filterable"],
                "sortable": field["sortable"],
                "groupable": field["groupable"],
            }
        )

    child_relationships = []
    for rel in obj_describe.get("childRelationships", []):
        child_relationships.append(
            {
                "child_sobject": rel["childSObject"],
                "field": rel["field"],
                "relationship_name": rel.get("relationshipName"),
                "cascade_delete": rel["cascadeDelete"],
            }
        )

    record_types = [
        {
            "id": rt["recordTypeId"],
            "name": rt["name"],
            "developer_name": rt["developerName"],
        }
        for rt in obj_describe.get("recordTypeInfos", [])
        if not rt.get("master", False)
    ]

    return {
        "name": obj_describe["name"],
        "label": obj_describe["label"],
        "label_plural": obj_describe["labelPlural"],
        "custom": obj_describe["custom"],
        "fields": fields,
        "child_relationships": child_relationships,
        "record_types": record_types,
        "fields_count": len(fields),
    }


def get_object_sample_data(sf: Salesforce, object_name: str, limit: int = 5) -> dict:
    """Run a SOQL query to fetch sample rows from a Salesforce object."""
    obj_describe = getattr(sf, object_name).describe()
    queryable_fields = [
        f["name"]
        for f in obj_describe["fields"]
        if f["type"] not in ("address", "location") and f.get("filterable", True)
    ][:20]

    soql = f"SELECT {', '.join(queryable_fields)} FROM {object_name} LIMIT {limit}"
    result = sf.query(soql)
    return {
        "object": object_name,
        "total_size": result["totalSize"],
        "records": result["records"],
        "soql": soql,
    }


def test_connection(sf: Salesforce) -> dict:
    """Return basic org info to confirm connection is alive."""
    org_info = sf.describe()
    token = get_stored_token()
    return {
        "connected": True,
        "instance_url": str(token.get("instance_url", "")) if token else "",
        "api_version": str(sf.sf_version),
        "org_objects_count": int(len(org_info["sobjects"])),
        "username": str(settings.SF_USERNAME),
        "auth_method": "OAuth Authorization Code",
    }

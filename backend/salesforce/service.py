"""
Salesforce connectivity and metadata retrieval service.

Authentication strategy (tries in order):
  1. OAuth 2.0 Username-Password flow (if SF_CONSUMER_KEY is set) — recommended
  2. simple_salesforce built-in login (username + password + security_token)
     Requires "Allow OAuth Username-Password Flows" enabled in org:
     Setup → Identity → OAuth and OpenID Connect Settings

Credentials needed in backend/.env:
  SF_USERNAME, SF_PASSWORD, SF_SECURITY_TOKEN
  SF_CONSUMER_KEY, SF_CONSUMER_SECRET  (optional but recommended)
  SF_DOMAIN = login   (use 'test' for sandbox)
"""

import requests
import logging
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceAuthenticationFailed
from core.config import settings

logger = logging.getLogger(__name__)

SALESFORCE_TOKEN_URL = "https://{domain}.salesforce.com/services/oauth2/token"


def _oauth_password_flow() -> Salesforce:
    """OAuth 2.0 Username-Password grant — requires Connected App credentials."""
    # Use org-specific My Domain URL if provided (required for External Client Apps)
    if settings.SF_INSTANCE_URL:
        token_url = f"{settings.SF_INSTANCE_URL.rstrip('/')}/services/oauth2/token"
    else:
        token_url = SALESFORCE_TOKEN_URL.format(domain=settings.SF_DOMAIN)

    payload = {
        "grant_type": "password",
        "client_id": settings.SF_CONSUMER_KEY,
        "client_secret": settings.SF_CONSUMER_SECRET,
        "username": settings.SF_USERNAME,
        "password": settings.SF_PASSWORD + settings.SF_SECURITY_TOKEN,
    }
    resp = requests.post(token_url, data=payload)
    if resp.status_code != 200:
        err = resp.json()
        raise ConnectionError(
            f"Salesforce OAuth failed [{resp.status_code}]: "
            f"{err.get('error')}: {err.get('error_description')}"
        )
    token_data = resp.json()
    return Salesforce(
        instance_url=token_data["instance_url"],
        session_id=token_data["access_token"],
    )


def _simple_login() -> Salesforce:
    """simple_salesforce built-in login — works when Username-Password flows enabled in org."""
    return Salesforce(
        username=settings.SF_USERNAME,
        password=settings.SF_PASSWORD,
        security_token=settings.SF_SECURITY_TOKEN,
        domain=settings.SF_DOMAIN,
    )


def get_salesforce_connection() -> Salesforce:
    """
    Connect to Salesforce.
    Strategy (tries in order until one works):
      1. OAuth 2.0 password flow via My Domain URL (if consumer key + instance_url set)
      2. OAuth 2.0 password flow via login.salesforce.com
      3. simple_salesforce direct username/password/token login
    """
    errors: list[str] = []

    if settings.SF_CONSUMER_KEY and settings.SF_CONSUMER_SECRET:
        # Attempt 1 — My Domain token endpoint (if instance URL is set)
        if settings.SF_INSTANCE_URL:
            try:
                logger.info("Attempt 1: OAuth via My Domain URL")
                return _oauth_password_flow()
            except Exception as e:
                logger.warning("OAuth (My Domain) failed: %s — trying standard login URL", e)
                errors.append(f"OAuth/MyDomain: {e}")

        # Attempt 2 — standard login.salesforce.com token endpoint
        try:
            logger.info("Attempt 2: OAuth via login.salesforce.com")
            payload = {
                "grant_type": "password",
                "client_id": settings.SF_CONSUMER_KEY,
                "client_secret": settings.SF_CONSUMER_SECRET,
                "username": settings.SF_USERNAME,
                "password": settings.SF_PASSWORD + settings.SF_SECURITY_TOKEN,
            }
            token_url = f"https://{settings.SF_DOMAIN}.salesforce.com/services/oauth2/token"
            resp = requests.post(token_url, data=payload)
            if resp.status_code == 200:
                td = resp.json()
                return Salesforce(instance_url=td["instance_url"], session_id=td["access_token"])
            err = resp.json()
            raise ConnectionError(f"{err.get('error')}: {err.get('error_description')}")
        except Exception as e:
            logger.warning("OAuth (standard) failed: %s — falling back to simple_salesforce", e)
            errors.append(f"OAuth/Standard: {e}")

    # Attempt 3 — simple_salesforce direct login
    try:
        logger.info("Attempt 3: simple_salesforce username/password login")
        return _simple_login()
    except Exception as e:
        errors.append(f"SimpleLogin: {e}")

    soap_disabled = any("SOAP API login" in str(err) or "SOAP" in str(err) for err in errors)
    invalid_grant = any("invalid_grant" in str(err) for err in errors)

    hint = ""
    if invalid_grant:
        hint = (
            " | LIKELY FIX: In Salesforce org → Setup → Identity → "
            "'OAuth and OpenID Connect Settings' → enable 'Allow OAuth Username-Password Flows'. "
            "Also in App Manager → your Connected App → Edit → enable same. "
            "Also verify your password/security token are current."
        )
    elif soap_disabled:
        hint = (
            " | SOAP login is disabled in this org. "
            "Enable 'Allow OAuth Username-Password Flows' in Setup → Identity → "
            "OAuth and OpenID Connect Settings."
        )

    raise ConnectionError(
        "All Salesforce authentication methods failed.\n"
        + "\n".join(errors)
        + hint
    )


def get_all_objects(sf: Salesforce) -> list[dict]:
    """
    Retrieve all SObjects (tables) from the Salesforce org.
    Returns name, label, queryable, createable, updateable flags per object.
    """
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
    """
    Full metadata for a specific SObject:
    - All fields: name, type, length, nillable, relationships, picklist values
    - Child relationships (reverse lookups)
    - Record types
    """
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
    """
    Run a SOQL query to fetch sample rows from a Salesforce object.
    Skips compound fields (address, location) which can't be directly queried.
    """
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
    return {
        "connected": True,
        "instance_url": sf.base_url,
        "api_version": sf.api_version,
        "org_objects_count": len(org_info["sobjects"]),
        "username": settings.SF_USERNAME,
    }

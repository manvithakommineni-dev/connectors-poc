"""
Salesforce connectivity and metadata retrieval service.

Authentication method: Username + Password + Security Token (simplest for POC).
Uses simple-salesforce library which wraps the Salesforce REST API.

To get a Security Token: Salesforce > My Settings > Personal > Reset My Security Token
"""

from simple_salesforce import Salesforce, SalesforceLogin
from simple_salesforce.exceptions import SalesforceAuthenticationFailed
from core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_salesforce_connection() -> Salesforce:
    """
    Establish connection to Salesforce using Username-Password OAuth flow.
    Raises SalesforceAuthenticationFailed if credentials are wrong.
    """
    sf = Salesforce(
        username=settings.SF_USERNAME,
        password=settings.SF_PASSWORD,
        security_token=settings.SF_SECURITY_TOKEN,
        domain=settings.SF_DOMAIN,  # 'login' for prod, 'test' for sandbox
    )
    return sf


def get_all_objects(sf: Salesforce) -> list[dict]:
    """
    Retrieve all SObjects (tables) from Salesforce.
    Returns a list with name, label, queryable, createable, updateable flags.
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
    Retrieve full metadata for a specific SObject:
    - All fields with type, length, nillable, etc.
    - Relationships (lookups/master-detail)
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
        {"id": rt["recordTypeId"], "name": rt["name"], "developer_name": rt["developerName"]}
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
    Only queries fields that are not compound (no address/location fields).
    """
    obj_describe = getattr(sf, object_name).describe()
    queryable_fields = [
        f["name"]
        for f in obj_describe["fields"]
        if f["type"] not in ("address", "location")
    ][:20]  # cap at 20 fields for sample

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

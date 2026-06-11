"""
ServiceNow connectivity and metadata retrieval service.

How ServiceNow exposes metadata:
  ServiceNow uses its own Table API and the sys_dictionary/sys_db_object system tables.
  Every table's schema (columns, types, labels) lives in sys_dictionary.
  All table definitions live in sys_db_object.

  Key API endpoints:
    List tables  : GET /api/now/table/sys_db_object
    Table fields : GET /api/now/table/sys_dictionary?sysparm_query=name={table}^elementISNOTEMPTY
    Table data   : GET /api/now/table/{table_name}

  ServiceNow concept equivalents:
    Salesforce SObject    → ServiceNow Table       (e.g. incident, change_request)
    Salesforce Field      → ServiceNow Column      (sys_dictionary element)
    Salesforce Picklist   → ServiceNow Choice      (sys_choice)
    SAP EntityType        → ServiceNow Table
    Workday Business Obj  → ServiceNow Table

  Key built-in tables (every ServiceNow instance has these):
    ITSM    : incident, change_request, problem, sc_request, sc_req_item, task
    CMDB    : cmdb_ci, cmdb_ci_server, cmdb_ci_appl, cmdb_ci_database
    Users   : sys_user, sys_user_group, sys_user_role, sys_user_has_role
    Catalog : sc_cat_item, sc_category, sc_cart
    Workflow: wf_workflow, approval_approver
    HR      : sn_hr_core_case, sn_hr_core_document

Authentication:
  Basic Auth: SN_USERNAME + SN_PASSWORD
  Instance URL: https://devXXXXX.service-now.com  (your personal developer instance)

Demo Mode:
  If SN_INSTANCE_URL is empty, returns built-in real ServiceNow table/field schema.
  Same tables that exist on every ServiceNow instance.

Setup (free Personal Developer Instance):
  1. Go to  https://developer.servicenow.com
  2. Sign up free  →  click "Start Building"  →  request a Personal Developer Instance
  3. Your instance URL:  https://devXXXXX.service-now.com
  4. Username: admin   Password: set during activation
  5. Add SN_INSTANCE_URL, SN_USERNAME, SN_PASSWORD to backend/.env
"""

import requests
import logging
from requests.auth import HTTPBasicAuth
from core.config import settings

logger = logging.getLogger(__name__)

# ServiceNow Table API and Dictionary paths
SN_TABLE_API = "/api/now/table"
SN_DICT_TABLE = "sys_dictionary"
SN_OBJ_TABLE = "sys_db_object"

# ─────────────────────────────────────────────────────────────────────────────
# Built-in demo — real ServiceNow schema for the most common tables
# ─────────────────────────────────────────────────────────────────────────────
DEMO_CATEGORIES = [
    {
        "id": "itsm",
        "label": "IT Service Management",
        "description": "Incident, Change, Problem, Service Request management",
        "tables": [
            {
                "name": "incident",
                "label": "Incident",
                "category": "itsm",
                "description": "IT incidents reported by users or monitoring systems",
                "is_extendable": True,
                "fields": [
                    {"name": "sys_id", "label": "Sys ID", "type": "GUID", "mandatory": True, "is_key": True, "max_length": 32, "reference": None, "description": "Unique system identifier"},
                    {"name": "number", "label": "Number", "type": "string", "mandatory": True, "is_key": False, "max_length": 40, "reference": None, "description": "Auto-generated incident number (e.g. INC0010001)"},
                    {"name": "short_description", "label": "Short Description", "type": "string", "mandatory": True, "is_key": False, "max_length": 160, "reference": None, "description": "Brief summary of the incident"},
                    {"name": "description", "label": "Description", "type": "string", "mandatory": False, "is_key": False, "max_length": 4000, "reference": None, "description": "Full description and details"},
                    {"name": "state", "label": "State", "type": "integer", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "1=New, 2=In Progress, 3=On Hold, 6=Resolved, 7=Closed"},
                    {"name": "priority", "label": "Priority", "type": "integer", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "1=Critical, 2=High, 3=Moderate, 4=Low, 5=Planning"},
                    {"name": "urgency", "label": "Urgency", "type": "integer", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "1=High, 2=Medium, 3=Low"},
                    {"name": "impact", "label": "Impact", "type": "integer", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "1=High, 2=Medium, 3=Low"},
                    {"name": "category", "label": "Category", "type": "string", "mandatory": False, "is_key": False, "max_length": 40, "reference": None, "description": "Incident category (Software, Hardware, Network, etc.)"},
                    {"name": "caller_id", "label": "Caller", "type": "reference", "mandatory": True, "is_key": False, "max_length": 32, "reference": "sys_user", "description": "User who reported the incident"},
                    {"name": "assigned_to", "label": "Assigned To", "type": "reference", "mandatory": False, "is_key": False, "max_length": 32, "reference": "sys_user", "description": "Agent handling the incident"},
                    {"name": "assignment_group", "label": "Assignment Group", "type": "reference", "mandatory": False, "is_key": False, "max_length": 32, "reference": "sys_user_group", "description": "Support group assigned to the incident"},
                    {"name": "opened_at", "label": "Opened", "type": "glide_date_time", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "Date and time the incident was opened"},
                    {"name": "resolved_at", "label": "Resolved", "type": "glide_date_time", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Date and time the incident was resolved"},
                    {"name": "closed_at", "label": "Closed", "type": "glide_date_time", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Date and time the incident was closed"},
                    {"name": "resolved_by", "label": "Resolved By", "type": "reference", "mandatory": False, "is_key": False, "max_length": 32, "reference": "sys_user", "description": "Agent who resolved the incident"},
                    {"name": "close_code", "label": "Close Code", "type": "string", "mandatory": False, "is_key": False, "max_length": 40, "reference": None, "description": "Resolution code when closing"},
                    {"name": "close_notes", "label": "Close Notes", "type": "string", "mandatory": False, "is_key": False, "max_length": 4000, "reference": None, "description": "Resolution notes"},
                    {"name": "sys_created_on", "label": "Created", "type": "glide_date_time", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Record creation timestamp"},
                    {"name": "sys_updated_on", "label": "Updated", "type": "glide_date_time", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Last update timestamp"},
                ]
            },
            {
                "name": "change_request",
                "label": "Change Request",
                "category": "itsm",
                "description": "IT change requests (Normal, Standard, Emergency)",
                "is_extendable": True,
                "fields": [
                    {"name": "sys_id", "label": "Sys ID", "type": "GUID", "mandatory": True, "is_key": True, "max_length": 32, "reference": None, "description": "Unique system identifier"},
                    {"name": "number", "label": "Number", "type": "string", "mandatory": True, "is_key": False, "max_length": 40, "reference": None, "description": "Auto-generated change number (e.g. CHG0010001)"},
                    {"name": "short_description", "label": "Short Description", "type": "string", "mandatory": True, "is_key": False, "max_length": 160, "reference": None, "description": "Summary of the change"},
                    {"name": "description", "label": "Description", "type": "string", "mandatory": False, "is_key": False, "max_length": 4000, "reference": None, "description": "Detailed description of the change"},
                    {"name": "type", "label": "Type", "type": "string", "mandatory": True, "is_key": False, "max_length": 40, "reference": None, "description": "normal, standard, emergency"},
                    {"name": "state", "label": "State", "type": "integer", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "-5=New, -4=Assess, -3=Authorize, -2=Scheduled, -1=Implement, 0=Review, 3=Closed"},
                    {"name": "priority", "label": "Priority", "type": "integer", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "1=Critical, 2=High, 3=Moderate, 4=Low"},
                    {"name": "risk", "label": "Risk", "type": "integer", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "1=High, 2=Moderate, 3=Low, 4=Very Low"},
                    {"name": "requested_by", "label": "Requested By", "type": "reference", "mandatory": True, "is_key": False, "max_length": 32, "reference": "sys_user", "description": "User who requested the change"},
                    {"name": "assigned_to", "label": "Assigned To", "type": "reference", "mandatory": False, "is_key": False, "max_length": 32, "reference": "sys_user", "description": "Agent assigned to implement"},
                    {"name": "start_date", "label": "Planned Start", "type": "glide_date_time", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Planned implementation start"},
                    {"name": "end_date", "label": "Planned End", "type": "glide_date_time", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Planned implementation end"},
                    {"name": "sys_created_on", "label": "Created", "type": "glide_date_time", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Record creation timestamp"},
                ]
            },
            {
                "name": "problem",
                "label": "Problem",
                "category": "itsm",
                "description": "Root cause investigations for recurring incidents",
                "is_extendable": False,
                "fields": [
                    {"name": "sys_id", "label": "Sys ID", "type": "GUID", "mandatory": True, "is_key": True, "max_length": 32, "reference": None, "description": "Unique system identifier"},
                    {"name": "number", "label": "Number", "type": "string", "mandatory": True, "is_key": False, "max_length": 40, "reference": None, "description": "Auto-generated problem number (e.g. PRB0010001)"},
                    {"name": "short_description", "label": "Short Description", "type": "string", "mandatory": True, "is_key": False, "max_length": 160, "reference": None, "description": "Summary of the problem"},
                    {"name": "state", "label": "State", "type": "integer", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "1=Open, 2=Known Error, 3=Pending Change, 4=Closed/Resolved"},
                    {"name": "priority", "label": "Priority", "type": "integer", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "1=Critical, 2=High, 3=Moderate, 4=Low"},
                    {"name": "assigned_to", "label": "Assigned To", "type": "reference", "mandatory": False, "is_key": False, "max_length": 32, "reference": "sys_user", "description": "Problem manager assigned"},
                    {"name": "cause_notes", "label": "Cause Notes", "type": "string", "mandatory": False, "is_key": False, "max_length": 4000, "reference": None, "description": "Root cause analysis notes"},
                    {"name": "fix_notes", "label": "Fix Notes", "type": "string", "mandatory": False, "is_key": False, "max_length": 4000, "reference": None, "description": "Workaround or permanent fix notes"},
                    {"name": "sys_created_on", "label": "Created", "type": "glide_date_time", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Record creation timestamp"},
                ]
            },
            {
                "name": "sc_request",
                "label": "Service Request",
                "category": "itsm",
                "description": "Service catalog requests submitted by users",
                "is_extendable": False,
                "fields": [
                    {"name": "sys_id", "label": "Sys ID", "type": "GUID", "mandatory": True, "is_key": True, "max_length": 32, "reference": None, "description": "Unique system identifier"},
                    {"name": "number", "label": "Number", "type": "string", "mandatory": True, "is_key": False, "max_length": 40, "reference": None, "description": "Auto-generated request number (e.g. REQ0010001)"},
                    {"name": "requested_for", "label": "Requested For", "type": "reference", "mandatory": True, "is_key": False, "max_length": 32, "reference": "sys_user", "description": "User the request is for"},
                    {"name": "state", "label": "State", "type": "integer", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "1=Draft, 2=Submitted, 3=In Process, 4=Closed Complete, 5=Closed Incomplete"},
                    {"name": "price", "label": "Price", "type": "currency", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Total price of the request"},
                    {"name": "opened_at", "label": "Opened", "type": "glide_date_time", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "Date and time the request was opened"},
                    {"name": "sys_created_on", "label": "Created", "type": "glide_date_time", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Record creation timestamp"},
                ]
            },
        ]
    },
    {
        "id": "cmdb",
        "label": "Configuration Management (CMDB)",
        "description": "Configuration Items: Servers, Applications, Databases, Network devices",
        "tables": [
            {
                "name": "cmdb_ci",
                "label": "Configuration Item",
                "category": "cmdb",
                "description": "Base class for all configuration items in the CMDB",
                "is_extendable": True,
                "fields": [
                    {"name": "sys_id", "label": "Sys ID", "type": "GUID", "mandatory": True, "is_key": True, "max_length": 32, "reference": None, "description": "Unique system identifier"},
                    {"name": "name", "label": "Name", "type": "string", "mandatory": True, "is_key": False, "max_length": 255, "reference": None, "description": "CI name"},
                    {"name": "sys_class_name", "label": "Class", "type": "string", "mandatory": True, "is_key": False, "max_length": 80, "reference": None, "description": "CI class (cmdb_ci_server, cmdb_ci_appl, etc.)"},
                    {"name": "operational_status", "label": "Operational Status", "type": "integer", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "1=Operational, 2=Non-Operational, 3=Repair In Progress"},
                    {"name": "install_status", "label": "Install Status", "type": "integer", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "1=Installed, 2=On Order, 3=In Maintenance, 6=Retired"},
                    {"name": "assigned_to", "label": "Managed By", "type": "reference", "mandatory": False, "is_key": False, "max_length": 32, "reference": "sys_user", "description": "Person responsible for the CI"},
                    {"name": "department", "label": "Department", "type": "reference", "mandatory": False, "is_key": False, "max_length": 32, "reference": "cmn_department", "description": "Owning department"},
                    {"name": "location", "label": "Location", "type": "reference", "mandatory": False, "is_key": False, "max_length": 32, "reference": "cmn_location", "description": "Physical location of the CI"},
                    {"name": "sys_created_on", "label": "Created", "type": "glide_date_time", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Record creation timestamp"},
                ]
            },
            {
                "name": "cmdb_ci_server",
                "label": "Server",
                "category": "cmdb",
                "description": "Physical and virtual servers (extends cmdb_ci)",
                "is_extendable": True,
                "fields": [
                    {"name": "sys_id", "label": "Sys ID", "type": "GUID", "mandatory": True, "is_key": True, "max_length": 32, "reference": None, "description": "Unique system identifier"},
                    {"name": "name", "label": "Name", "type": "string", "mandatory": True, "is_key": False, "max_length": 255, "reference": None, "description": "Server hostname"},
                    {"name": "ip_address", "label": "IP Address", "type": "string", "mandatory": False, "is_key": False, "max_length": 255, "reference": None, "description": "Primary IP address"},
                    {"name": "fqdn", "label": "FQDN", "type": "string", "mandatory": False, "is_key": False, "max_length": 255, "reference": None, "description": "Fully Qualified Domain Name"},
                    {"name": "os", "label": "OS", "type": "string", "mandatory": False, "is_key": False, "max_length": 100, "reference": None, "description": "Operating system name"},
                    {"name": "os_version", "label": "OS Version", "type": "string", "mandatory": False, "is_key": False, "max_length": 100, "reference": None, "description": "OS version"},
                    {"name": "cpu_count", "label": "CPU Count", "type": "integer", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Number of CPUs"},
                    {"name": "ram", "label": "RAM (MB)", "type": "integer", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Total RAM in megabytes"},
                    {"name": "disk_space", "label": "Disk Space (GB)", "type": "decimal", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Total disk space in GB"},
                    {"name": "virtual", "label": "Virtual", "type": "boolean", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Whether the server is virtual"},
                ]
            },
        ]
    },
    {
        "id": "users",
        "label": "Users & Access",
        "description": "Users, Groups, Roles, Access Control",
        "tables": [
            {
                "name": "sys_user",
                "label": "User",
                "category": "users",
                "description": "All users in the ServiceNow instance",
                "is_extendable": False,
                "fields": [
                    {"name": "sys_id", "label": "Sys ID", "type": "GUID", "mandatory": True, "is_key": True, "max_length": 32, "reference": None, "description": "Unique system identifier"},
                    {"name": "user_name", "label": "User ID", "type": "string", "mandatory": True, "is_key": False, "max_length": 100, "reference": None, "description": "Login username"},
                    {"name": "first_name", "label": "First Name", "type": "string", "mandatory": False, "is_key": False, "max_length": 50, "reference": None, "description": "First name"},
                    {"name": "last_name", "label": "Last Name", "type": "string", "mandatory": True, "is_key": False, "max_length": 50, "reference": None, "description": "Last name"},
                    {"name": "email", "label": "Email", "type": "email", "mandatory": False, "is_key": False, "max_length": 100, "reference": None, "description": "Email address"},
                    {"name": "phone", "label": "Phone", "type": "phone_number", "mandatory": False, "is_key": False, "max_length": 40, "reference": None, "description": "Phone number"},
                    {"name": "department", "label": "Department", "type": "reference", "mandatory": False, "is_key": False, "max_length": 32, "reference": "cmn_department", "description": "User's department"},
                    {"name": "manager", "label": "Manager", "type": "reference", "mandatory": False, "is_key": False, "max_length": 32, "reference": "sys_user", "description": "User's manager"},
                    {"name": "active", "label": "Active", "type": "boolean", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "Whether the user account is active"},
                    {"name": "title", "label": "Title", "type": "string", "mandatory": False, "is_key": False, "max_length": 50, "reference": None, "description": "Job title"},
                    {"name": "location", "label": "Location", "type": "reference", "mandatory": False, "is_key": False, "max_length": 32, "reference": "cmn_location", "description": "Work location"},
                ]
            },
            {
                "name": "sys_user_group",
                "label": "Group",
                "category": "users",
                "description": "User groups for assignment and access control",
                "is_extendable": False,
                "fields": [
                    {"name": "sys_id", "label": "Sys ID", "type": "GUID", "mandatory": True, "is_key": True, "max_length": 32, "reference": None, "description": "Unique system identifier"},
                    {"name": "name", "label": "Name", "type": "string", "mandatory": True, "is_key": False, "max_length": 80, "reference": None, "description": "Group name"},
                    {"name": "description", "label": "Description", "type": "string", "mandatory": False, "is_key": False, "max_length": 1000, "reference": None, "description": "Group description"},
                    {"name": "manager", "label": "Manager", "type": "reference", "mandatory": False, "is_key": False, "max_length": 32, "reference": "sys_user", "description": "Group manager"},
                    {"name": "active", "label": "Active", "type": "boolean", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "Whether the group is active"},
                    {"name": "email", "label": "Email", "type": "email", "mandatory": False, "is_key": False, "max_length": 100, "reference": None, "description": "Group email address"},
                    {"name": "type", "label": "Type", "type": "string", "mandatory": False, "is_key": False, "max_length": 40, "reference": None, "description": "Group type"},
                ]
            },
        ]
    },
    {
        "id": "catalog",
        "label": "Service Catalog",
        "description": "Catalog Items, Categories, Orders",
        "tables": [
            {
                "name": "sc_cat_item",
                "label": "Catalog Item",
                "category": "catalog",
                "description": "Items available in the ServiceNow service catalog",
                "is_extendable": True,
                "fields": [
                    {"name": "sys_id", "label": "Sys ID", "type": "GUID", "mandatory": True, "is_key": True, "max_length": 32, "reference": None, "description": "Unique system identifier"},
                    {"name": "name", "label": "Name", "type": "string", "mandatory": True, "is_key": False, "max_length": 255, "reference": None, "description": "Catalog item name"},
                    {"name": "short_description", "label": "Short Description", "type": "string", "mandatory": False, "is_key": False, "max_length": 160, "reference": None, "description": "Brief description shown in catalog"},
                    {"name": "description", "label": "Description", "type": "string", "mandatory": False, "is_key": False, "max_length": 8000, "reference": None, "description": "Full item description"},
                    {"name": "category", "label": "Category", "type": "reference", "mandatory": False, "is_key": False, "max_length": 32, "reference": "sc_category", "description": "Catalog category"},
                    {"name": "price", "label": "Price", "type": "currency", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Item price"},
                    {"name": "active", "label": "Active", "type": "boolean", "mandatory": True, "is_key": False, "max_length": None, "reference": None, "description": "Whether item is visible in catalog"},
                    {"name": "availability", "label": "Availability", "type": "integer", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "1=On Desktop, 2=On Mobile, 3=Both"},
                    {"name": "sys_created_on", "label": "Created", "type": "glide_date_time", "mandatory": False, "is_key": False, "max_length": None, "reference": None, "description": "Record creation timestamp"},
                ]
            },
        ]
    },
]

_ALL_TABLES: dict = {t["name"]: t for cat in DEMO_CATEGORIES for t in cat["tables"]}
_CATEGORY_MAP: dict = {c["id"]: c for c in DEMO_CATEGORIES}


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def _is_demo_mode() -> bool:
    return not bool(settings.SN_INSTANCE_URL)


def _base() -> str:
    return settings.SN_INSTANCE_URL.rstrip("/")


def _auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(settings.SN_USERNAME, settings.SN_PASSWORD)


def _get(path: str, params: dict = None) -> dict:
    url = f"{_base()}{path}"
    resp = requests.get(
        url,
        auth=_auth(),
        params=params,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=30,
    )
    if resp.status_code == 401:
        raise ConnectionError(
            "ServiceNow authentication failed. Check SN_USERNAME and SN_PASSWORD in .env"
        )
    if resp.status_code == 403:
        raise PermissionError(f"ServiceNow access denied: {path}")
    if resp.status_code == 404:
        raise LookupError(f"ServiceNow resource not found: {path}")
    if not resp.ok:
        raise RuntimeError(f"ServiceNow API error [{resp.status_code}]: {resp.text[:400]}")
    return resp.json()


# ──────────────────────────────────────────────────────────
# Public service functions
# ──────────────────────────────────────────────────────────

def test_connection() -> dict:
    if _is_demo_mode():
        total_tables = sum(len(c["tables"]) for c in DEMO_CATEGORIES)
        total_fields = sum(len(t["fields"]) for c in DEMO_CATEGORIES for t in c["tables"])
        return {
            "connected": True,
            "mode": "demo",
            "message": (
                "Running in Demo Mode — showing real ServiceNow table/field schema. "
                "Set SN_INSTANCE_URL, SN_USERNAME, SN_PASSWORD in .env to connect "
                "to your Personal Developer Instance."
            ),
            "categories_count": len(DEMO_CATEGORIES),
            "total_tables": total_tables,
            "total_fields": total_fields,
        }

    # Live: hit the sys_db_object table to verify connectivity
    data = _get(
        f"{SN_TABLE_API}/{SN_OBJ_TABLE}",
        params={"sysparm_limit": 1, "sysparm_fields": "name,label"}
    )
    return {
        "connected": True,
        "mode": "live",
        "instance_url": _base(),
        "result_count": len(data.get("result", [])),
    }


def list_categories() -> list[dict]:
    """Categories group tables. In demo mode returns predefined categories.
       In live mode returns the top application scopes from sys_scope."""
    if _is_demo_mode():
        return [
            {
                "id": c["id"],
                "label": c["label"],
                "description": c["description"],
                "tables_count": len(c["tables"]),
            }
            for c in DEMO_CATEGORIES
        ]

    # Live: return predefined categories (ServiceNow doesn't expose them the same way)
    return [
        {"id": c["id"], "label": c["label"], "description": c["description"], "tables_count": 0}
        for c in DEMO_CATEGORIES
    ]


def list_tables(category_id: str = None, search: str = None, limit: int = 100) -> dict:
    """List tables. In live mode queries sys_db_object."""
    if _is_demo_mode():
        if category_id:
            if category_id not in _CATEGORY_MAP:
                raise LookupError(f"Category '{category_id}' not found.")
            tables = _CATEGORY_MAP[category_id]["tables"]
        else:
            tables = [t for c in DEMO_CATEGORIES for t in c["tables"]]

        if search:
            s = search.lower()
            tables = [t for t in tables if s in t["name"].lower() or s in t["label"].lower()]

        return {
            "total": len(tables),
            "tables": [
                {
                    "name": t["name"],
                    "label": t["label"],
                    "category": t["category"],
                    "description": t["description"],
                    "is_extendable": t["is_extendable"],
                    "fields_count": len(t["fields"]),
                }
                for t in tables
            ],
            "mode": "demo",
        }

    # Live: query sys_db_object
    params = {
        "sysparm_limit": limit,
        "sysparm_fields": "name,label,is_extendable,super_class.name,sys_scope.name",
        "sysparm_query": "nameISNOTEMPTY^labelISNOTEMPTY",
    }
    if search:
        params["sysparm_query"] += f"^nameLIKE{search}^ORlabelLIKE{search}"

    data = _get(f"{SN_TABLE_API}/{SN_OBJ_TABLE}", params=params)
    results = data.get("result", [])
    tables = [
        {
            "name": r.get("name", ""),
            "label": r.get("label", r.get("name", "")),
            "category": r.get("sys_scope.name", ""),
            "description": "",
            "is_extendable": r.get("is_extendable", False),
            "fields_count": None,
        }
        for r in results
        if r.get("name")
    ]
    return {"total": len(tables), "tables": tables, "mode": "live"}


def get_table_fields(table_name: str) -> dict:
    """Get all fields/columns for a ServiceNow table via sys_dictionary."""
    if _is_demo_mode():
        if table_name not in _ALL_TABLES:
            raise LookupError(
                f"Table '{table_name}' not found in demo data. "
                f"Available: {list(_ALL_TABLES.keys())}"
            )
        t = _ALL_TABLES[table_name]
        return {
            "table_name": table_name,
            "table_label": t["label"],
            "description": t["description"],
            "is_extendable": t["is_extendable"],
            "fields_count": len(t["fields"]),
            "fields": t["fields"],
            "mode": "demo",
        }

    # Live: query sys_dictionary for the table's columns
    params = {
        "sysparm_query": f"name={table_name}^elementISNOTEMPTY^internal_typeINstring,integer,boolean,glide_date_time,reference,email,currency,decimal,GUID,phone_number,float,long",
        "sysparm_fields": "element,column_label,internal_type,mandatory,max_length,reference,comments",
        "sysparm_limit": 500,
    }
    data = _get(f"{SN_TABLE_API}/{SN_DICT_TABLE}", params=params)
    results = data.get("result", [])

    fields = []
    for r in results:
        ref_val = r.get("reference", {})
        ref_name = None
        if isinstance(ref_val, dict):
            ref_name = ref_val.get("value") or ref_val.get("display_value")
        elif isinstance(ref_val, str):
            ref_name = ref_val or None

        fields.append({
            "name": r.get("element", ""),
            "label": r.get("column_label", r.get("element", "")),
            "type": r.get("internal_type", "string"),
            "mandatory": r.get("mandatory", "false") in (True, "true"),
            "is_key": r.get("element", "") == "sys_id",
            "max_length": int(r["max_length"]) if r.get("max_length") and r["max_length"].isdigit() else None,
            "reference": ref_name,
            "description": r.get("comments", ""),
        })

    # get table label from sys_db_object
    obj_data = _get(
        f"{SN_TABLE_API}/{SN_OBJ_TABLE}",
        params={"sysparm_query": f"name={table_name}", "sysparm_fields": "label,is_extendable", "sysparm_limit": 1}
    )
    obj_result = obj_data.get("result", [{}])
    obj_info = obj_result[0] if obj_result else {}

    return {
        "table_name": table_name,
        "table_label": obj_info.get("label", table_name),
        "description": "",
        "is_extendable": obj_info.get("is_extendable", False),
        "fields_count": len(fields),
        "fields": fields,
        "mode": "live",
    }

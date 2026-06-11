from fastapi import APIRouter, HTTPException
from netsuite.service import (
    test_connection,
    list_modules,
    get_module_records,
    get_record_fields,
    get_all_records,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/netsuite", tags=["NetSuite"])


def _handle(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ConnectionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NetSuite error: {str(e)}")


@router.get("/connect")
def connect():
    """
    Test NetSuite connectivity.

    Live Mode (free 30-day trial):
      1. Go to https://www.netsuite.com  →  Free Trial / Get Started
      2. After login, go to Setup > Integration > Manage Integrations → New
      3. Enable OAuth 2.0 → get Client ID and Client Secret
      4. Your Account ID is in your URL: https://ACCOUNTID.app.netsuite.com
      5. Set NS_ACCOUNT_ID, NS_CLIENT_ID, NS_CLIENT_SECRET in backend/.env

    Demo Mode (no credentials needed):
      Returns built-in schema: 7 modules, 13 record types, 130+ fields.
    """
    return _handle(test_connection)


@router.get("/modules")
def modules():
    """
    List NetSuite functional modules.
    Accounting, Customers & CRM, Vendors & Purchasing, Inventory,
    Sales Transactions, Employees & HR, Projects.
    """
    result = _handle(list_modules)
    return {"total": len(result), "modules": result}


@router.get("/modules/{module_id}/records")
def module_records(module_id: str):
    """
    List all record types (tables) in a NetSuite module.
    Example module IDs: accounting, customers, vendors, inventory, sales, employees, projects
    """
    return _handle(get_module_records, module_id)


@router.get("/records")
def all_records():
    """Flat list of all NetSuite record types across all modules."""
    return _handle(get_all_records)


@router.get("/records/{record_type}/fields")
def record_fields(record_type: str):
    """
    Full metadata for a NetSuite record type via the REST Metadata Catalog.
    Returns all fields with type, nullable, readOnly, and referenceType.

    Equivalent to:
      SAP:         /services/{service}/entities/{entity}/fields
      Salesforce:  /sobjects/{object}/describe
      Oracle:      /resources/{resource}/describe
      ServiceNow:  /tables/{table}/fields

    Example record types (demo + any live account):
      account, journalEntry, customer, contact, opportunity,
      vendor, purchaseOrder, inventoryItem, salesOrder, invoice,
      employee, department, job
    """
    return _handle(get_record_fields, record_type)

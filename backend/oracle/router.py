from fastapi import APIRouter, HTTPException
from oracle.service import (
    test_connection,
    list_modules,
    get_module_resources,
    get_resource_describe,
    get_all_resources,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/oracle", tags=["Oracle Fusion ERP"])


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
        raise HTTPException(status_code=500, detail=f"Oracle error: {str(e)}")


@router.get("/connect")
def connect():
    """
    Test Oracle Fusion ERP connectivity.

    Demo Mode (no credentials needed):
      Returns built-in Oracle ERP schema with real module/resource structure.
      Covers: Financials, Procurement, Order Management, HCM, Projects, Supply Chain.

    Live Mode (real Oracle Cloud):
      Set ORACLE_BASE_URL, ORACLE_USERNAME, ORACLE_PASSWORD in backend/.env
      Base URL format: https://your-instance.fa.oc.oraclecloud.com
    """
    return _handle(test_connection)


@router.get("/modules")
def modules():
    """
    List Oracle ERP modules.
    In demo mode: Financials, Procurement, Order Management, HCM, Projects, Supply Chain.
    In live mode: top-level resource groups from Oracle Fusion REST API.
    """
    result = _handle(list_modules)
    return {"total": len(result), "modules": result}


@router.get("/modules/{module_id}/resources")
def module_resources(module_id: str):
    """
    List all resources (tables/business objects) within an Oracle ERP module.
    Equivalent to SAP's entity list or Salesforce's object list per area.
    """
    return _handle(get_module_resources, module_id)


@router.get("/resources")
def all_resources():
    """
    Flat list of ALL Oracle ERP resources across all modules.
    Use this for a global search or overview.
    """
    return _handle(get_all_resources)


@router.get("/resources/{resource_name}/describe")
def resource_describe(resource_name: str):
    """
    Full metadata for an Oracle Fusion ERP resource.
    Returns all attributes (fields) with type, required, queryable, updatable flags,
    plus child resources (nested/related sub-tables).

    Example resource names (demo mode):
      invoices, receivablesInvoices, generalLedgerJournals,
      purchaseOrders, suppliers, salesOrders, customers,
      workers, departments, projects, inventoryItems
    """
    return _handle(get_resource_describe, resource_name)

from fastapi import APIRouter, HTTPException, Query
from servicenow.service import (
    test_connection,
    list_categories,
    list_tables,
    get_table_fields,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/servicenow", tags=["ServiceNow"])


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
        raise HTTPException(status_code=500, detail=f"ServiceNow error: {str(e)}")


@router.get("/connect")
def connect():
    """
    Test ServiceNow connectivity.

    Live Mode (free Personal Developer Instance):
      1. Sign up at https://developer.servicenow.com
      2. Click 'Start Building' → request a Personal Developer Instance
      3. Set SN_INSTANCE_URL, SN_USERNAME, SN_PASSWORD in backend/.env

    Demo Mode (no credentials needed):
      Returns built-in schema: 4 categories, 11 tables, 100+ fields.
    """
    return _handle(test_connection)


@router.get("/categories")
def categories():
    """
    List ServiceNow table categories.
    Demo: IT Service Management, CMDB, Users & Access, Service Catalog.
    Live: Same categories (used for navigation grouping).
    """
    result = _handle(list_categories)
    return {"total": len(result), "categories": result}


@router.get("/tables")
def tables(
    category: str = Query(None, description="Filter by category ID"),
    search: str = Query(None, description="Search tables by name or label"),
    limit: int = Query(100, description="Max results (live mode only)"),
):
    """
    List ServiceNow tables.
    In demo mode: returns well-known built-in tables.
    In live mode: queries sys_db_object for all tables in your instance.

    Example category IDs: itsm, cmdb, users, catalog
    """
    return _handle(list_tables, category, search, limit)


@router.get("/tables/{table_name}/fields")
def table_fields(table_name: str):
    """
    Get all fields (columns) for a ServiceNow table via sys_dictionary.
    Returns field name, label, type, mandatory, max_length, reference table.

    Equivalent to:
      SAP:        /services/{service}/entities/{entity}/fields
      Salesforce: /sobjects/{object}/describe
      Oracle:     /resources/{resource}/describe

    Example table names (demo + any live instance):
      incident, change_request, problem, sc_request,
      cmdb_ci, cmdb_ci_server,
      sys_user, sys_user_group,
      sc_cat_item
    """
    return _handle(get_table_fields, table_name)

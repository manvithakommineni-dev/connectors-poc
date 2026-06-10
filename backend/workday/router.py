from fastapi import APIRouter, HTTPException
from workday.service import (
    test_connection,
    list_modules,
    get_module_objects,
    get_object_describe,
    get_all_objects,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workday", tags=["Workday"])


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
        raise HTTPException(status_code=500, detail=f"Workday error: {str(e)}")


@router.get("/connect")
def connect():
    """
    Test Workday connectivity.

    Demo Mode (no credentials needed):
      Returns built-in Workday schema: 6 modules, 13 objects, 100+ fields.
      Modules: Human Resources, Payroll, Recruiting, Benefits, Time & Absence, Learning.

    Live Mode (real Workday tenant):
      Set WORKDAY_TENANT, WORKDAY_CLIENT_ID, WORKDAY_CLIENT_SECRET in backend/.env.
      Register an API Client in Workday: Security > OAuth 2.0 Clients Allowed.
    """
    return _handle(test_connection)


@router.get("/modules")
def modules():
    """
    List Workday functional modules.
    Demo: Human Resources, Payroll, Recruiting, Benefits, Time & Absence, Learning.
    """
    result = _handle(list_modules)
    return {"total": len(result), "modules": result}


@router.get("/modules/{module_id}/objects")
def module_objects(module_id: str):
    """
    List all business objects (tables) within a Workday module.
    Example module IDs: humanResources, payroll, recruiting, benefits, timeAndAbsence, learning
    """
    return _handle(get_module_objects, module_id)


@router.get("/objects")
def all_objects():
    """
    Flat list of ALL Workday business objects across all modules.
    """
    return _handle(get_all_objects)


@router.get("/objects/{object_name}/describe")
def object_describe(object_name: str):
    """
    Full metadata for a Workday business object.
    Returns all fields with type, required, filterable flags, and related resources.

    Example object names:
      workers, organizations, jobProfiles, locations,
      payGroups, payrollResults, jobRequisitions, jobApplications,
      benefitPlans, timeOffTypes, absenceRequests, learningCourses
    """
    return _handle(get_object_describe, object_name)

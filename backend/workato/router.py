from fastapi import APIRouter, HTTPException, Query

from workato.service import (
    test_connection,
    list_categories,
    list_items,
    get_item_detail,
    get_job_detail,
    get_setup_guide,
)

router = APIRouter(prefix="/workato", tags=["Workato"])


def _handle(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connect")
def connect():
    """Test Workato Developer API connectivity."""
    return _handle(test_connection)


@router.get("/setup-guide")
def setup_guide():
    """Steps to create a Workato trial workspace and API client token."""
    return get_setup_guide()


@router.get("/categories")
def categories():
    """List Workato metadata categories (connections, recipes, job runs)."""
    return _handle(list_categories)


@router.get("/items")
def items(category: str):
    """List connections, recipes, or recent job runs from live Workato API."""
    return _handle(list_items, category)


@router.get("/items/{item_id}")
def item_detail(item_id: str, category: str):
    """Detail for a connection, recipe, or job run (includes step input/output for jobs)."""
    return _handle(get_item_detail, category, item_id)


@router.get("/recipes/{recipe_id}/jobs/{job_id}")
def job_detail(recipe_id: str, job_id: str):
    """Full job with step lines — live input/output data from a recipe test run."""
    return _handle(get_job_detail, recipe_id, job_id)

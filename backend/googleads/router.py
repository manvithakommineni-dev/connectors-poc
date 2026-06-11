from fastapi import APIRouter, HTTPException
from googleads.service import (
    test_connection,
    list_categories,
    list_resources,
    get_resource_fields,
)

router = APIRouter(prefix="/googleads", tags=["Google Ads"])


def _handle(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connect")
def connect():
    """Test Google Ads connectivity and return account/mode info."""
    return _handle(test_connection)


@router.get("/categories")
def categories():
    """
    List resource categories (Campaigns, Ad Groups, Ads, Performance, Account).
    Equivalent to 'module' or 'namespace' in other connectors.
    """
    return _handle(list_categories)


@router.get("/resources")
def resources(category: str = None):
    """
    List all Google Ads resources (like tables).
    Optionally filter by category id.
    """
    return _handle(list_resources, category)


@router.get("/resources/{resource_name}/fields")
def resource_fields(resource_name: str):
    """
    Retrieve all fields (attributes, metrics, segments) for a given resource.
    This is the core metadata endpoint — equivalent to DESCRIBE TABLE.
    """
    return _handle(get_resource_fields, resource_name)

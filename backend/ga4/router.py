from fastapi import APIRouter, HTTPException
from ga4.service import (
    test_connection,
    list_categories,
    list_items,
    get_item_detail,
)

router = APIRouter(prefix="/ga4", tags=["Google Analytics 4"])


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
    """Test GA4 connectivity using service account credentials."""
    return _handle(test_connection)


@router.get("/categories")
def categories():
    """List metadata categories (dimensions, metrics, custom definitions, data streams)."""
    return _handle(list_categories)


@router.get("/items")
def items(category: str):
    """List all items in a category from live GA4 APIs."""
    return _handle(list_items, category)


@router.get("/items/{item_name}")
def item_detail(item_name: str, category: str):
    """Get detail for a single dimension, metric, or custom definition."""
    return _handle(get_item_detail, category, item_name)

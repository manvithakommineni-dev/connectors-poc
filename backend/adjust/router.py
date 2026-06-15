from fastapi import APIRouter, HTTPException

from adjust.service import (
    test_connection,
    list_categories,
    list_items,
    get_item_detail,
)

router = APIRouter(prefix="/adjust", tags=["Adjust"])


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
    """Test Adjust Report Service API connectivity using API token."""
    return _handle(test_connection)


@router.get("/categories")
def categories():
    """List metadata categories (apps, events, metrics, dimensions)."""
    return _handle(list_categories)


@router.get("/items")
def items(category: str):
    """List live filter items or events for a category."""
    return _handle(list_items, category)


@router.get("/items/{item_id}")
def item_detail(item_id: str, category: str):
    """Get detail for an app, metric, dimension, or event."""
    return _handle(get_item_detail, category, item_id)

from fastapi import APIRouter, HTTPException
from instagram.service import (
    test_connection,
    list_categories,
    list_items,
    get_item_detail,
)

router = APIRouter(prefix="/instagram", tags=["Instagram"])


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
    """Test Instagram Graph API connectivity."""
    return _handle(test_connection)


@router.get("/categories")
def categories():
    """List metadata categories (account, media, stories, field catalogs)."""
    return _handle(list_categories)


@router.get("/items")
def items(category: str):
    """List live objects or field catalog for a category."""
    return _handle(list_items, category)


@router.get("/items/{item_id}")
def item_detail(item_id: str, category: str):
    """Get detail for an account, media item, story, or field definition."""
    return _handle(get_item_detail, category, item_id)

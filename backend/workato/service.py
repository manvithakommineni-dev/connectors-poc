"""
Workato connectivity and live data retrieval service.

Workato is an iPaaS — it connects TO other apps (Salesforce, GA4, HubSpot, etc.).
This module uses the Workato Developer API to list connections, recipes, and
job step input/output so you can cross-check data against direct connector calls.

Authentication:
  Bearer token from Workspace admin → API clients → create client → copy token.
  Set WORKATO_API_TOKEN and WORKATO_API_BASE_URL in .env.

Trial / sandbox base URL: https://app.trial.workato.com/api/
Production US:            https://www.workato.com/api/
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_TRIAL_BASE = "https://app.trial.workato.com/api"
DEFAULT_US_BASE = "https://www.workato.com/api"

METADATA_CATEGORIES = [
    {
        "id": "connections",
        "label": "Connections",
        "description": "Apps linked in Workato (Salesforce, GA4, HubSpot, etc.)",
    },
    {
        "id": "recipes",
        "label": "Recipes",
        "description": "Automation recipes and their linked applications",
    },
    {
        "id": "job_runs",
        "label": "Job Runs",
        "description": "Recent recipe executions with step input/output (live data)",
    },
]

SETUP_GUIDE = {
    "title": "Workato Trial + API Client Setup",
    "docs": "https://docs.workato.com/workato-api",
    "trial_url": "https://www.workato.com/pricing/",
    "env_keys_needed": ["WORKATO_API_TOKEN", "WORKATO_API_BASE_URL"],
    "steps": [
        {
            "step": 1,
            "action": "Request a Workato trial or developer workspace",
            "where": "https://www.workato.com → Get a trial / Contact sales",
            "note": "Workato does not have a public self-serve free tier like GA4. Request trial access — you may get app.trial.workato.com or www.workato.com.",
        },
        {
            "step": 2,
            "action": "In Workato UI, connect your source apps (e.g. Salesforce, GA4)",
            "where": "Workato → Projects → Connections → Create connection",
            "note": "Use the same dev credentials you use in this POC so you can compare live data.",
        },
        {
            "step": 3,
            "action": "Create a test recipe that reads from your source (e.g. Salesforce → Search records)",
            "where": "Workato → Recipes → Create recipe → Test → Run",
            "note": "Job step output is what you'll compare against your direct connector responses.",
        },
        {
            "step": 4,
            "action": "Create an API client role with required endpoint permissions",
            "where": "Workspace admin → API clients → Client roles → New role",
            "note": "Enable: GET /api/users/me, GET /api/connections, GET /api/recipes, GET /api/recipes/:id/jobs, GET /api/recipes/:id/jobs/:job_id",
        },
        {
            "step": 5,
            "action": "Create API client and copy the Bearer token",
            "where": "Workspace admin → API clients → New API client → select role + projects",
            "note": "Assign the project(s) where your connections and recipes live.",
        },
        {
            "step": 6,
            "action": "Paste token and base URL into backend/.env and restart uvicorn",
            "where": "backend/.env",
            "note": "Trial: WORKATO_API_BASE_URL=https://app.trial.workato.com/api — Production US: https://www.workato.com/api",
        },
    ],
}


def _api_base() -> str:
    base = (settings.WORKATO_API_BASE_URL or DEFAULT_TRIAL_BASE).rstrip("/")
    return base


def _headers() -> dict[str, str]:
    token = settings.WORKATO_API_TOKEN.strip()
    if not token:
        raise ConnectionError(
            "WORKATO_API_TOKEN is not set. Create an API client in Workato Workspace admin "
            "and add the token to backend/.env"
        )
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _request(method: str, path: str, **kwargs: Any) -> Any:
    url = f"{_api_base()}/{path.lstrip('/')}"
    try:
        resp = requests.request(method, url, headers=_headers(), timeout=45, **kwargs)
    except requests.RequestException as exc:
        raise ConnectionError(f"Could not reach Workato API at {url}: {exc}") from exc

    if resp.status_code == 401:
        raise ConnectionError(
            "Workato API returned 401 Unauthorized. Check WORKATO_API_TOKEN and that the "
            "API client role has permission for this endpoint."
        )
    if resp.status_code == 403:
        raise PermissionError(
            "Workato API returned 403 Forbidden. Ensure the API client is scoped to the "
            "correct project and the client role includes this endpoint."
        )
    if resp.status_code == 404:
        raise LookupError(resp.text or "Resource not found")
    if resp.status_code >= 400:
        raise RuntimeError(f"Workato API error {resp.status_code}: {resp.text[:500]}")

    if not resp.content:
        return {}
    return resp.json()


def get_setup_guide() -> dict[str, Any]:
    return SETUP_GUIDE


def test_connection() -> dict[str, Any]:
    workspace: dict[str, Any] | None = None
    connections_count = 0
    recipes_count = 0

    try:
        workspace = _request("GET", "users/me")
    except (ConnectionError, PermissionError, RuntimeError) as exc:
        logger.warning("Workato /users/me unavailable: %s", exc)

    try:
        connections = _list_connections_raw()
        connections_count = len(connections)
    except Exception as exc:
        logger.warning("Workato connections list failed: %s", exc)
        if workspace is None:
            raise ConnectionError(str(exc)) from exc

    try:
        recipes = _list_recipes_raw()
        recipes_count = len(recipes)
    except Exception as exc:
        logger.warning("Workato recipes list failed: %s", exc)

    if workspace is None and connections_count == 0 and recipes_count == 0:
        raise ConnectionError(
            "Could not reach Workato workspace. Verify WORKATO_API_TOKEN and "
            "WORKATO_API_BASE_URL match your Workato data center (trial vs production)."
        )

    return {
        "connected": True,
        "mode": "live",
        "api_base": _api_base(),
        "workspace_name": (workspace or {}).get("name") or (workspace or {}).get("company_name"),
        "workspace_email": (workspace or {}).get("email"),
        "plan": (workspace or {}).get("plan") or (workspace or {}).get("billing_plan"),
        "connections_count": connections_count,
        "recipes_count": recipes_count,
        "auth_method": "API client Bearer token",
        "note": (
            "Connect source apps in Workato UI, run recipe tests, then inspect job_runs "
            "here to compare data with direct connector calls."
        ),
    }


def list_categories() -> list[dict[str, Any]]:
    test_connection()
    counts = {
        "connections": len(_list_connections_raw()),
        "recipes": len(_list_recipes_raw()),
        "job_runs": len(_list_job_run_items(limit_recipes=15, jobs_per_recipe=2)),
    }
    return [
        {**cat, "items_count": counts.get(cat["id"], 0)}
        for cat in METADATA_CATEGORIES
    ]


def _list_connections_raw() -> list[dict[str, Any]]:
    data = _request("GET", "connections")
    if isinstance(data, list):
        return data
    return data.get("items", [])


def _list_recipes_raw() -> list[dict[str, Any]]:
    data = _request("GET", "recipes", params={"exclude_code": "true", "per_page": 100})
    if isinstance(data, list):
        return data
    return data.get("items", [])


def _connection_item(conn: dict[str, Any]) -> dict[str, Any]:
    app = conn.get("application") or conn.get("provider") or "unknown"
    name = conn.get("name") or f"Connection {conn.get('id')}"
    status = conn.get("authorization_status") or "unknown"
    return {
        "name": str(conn.get("id")),
        "label": name,
        "description": f"{app} · {status}",
        "application": app,
        "authorization_status": status,
        "raw": conn,
    }


def _recipe_item(recipe: dict[str, Any]) -> dict[str, Any]:
    apps = recipe.get("applications") or []
    running = recipe.get("running")
    status = "running" if running else "stopped"
    return {
        "name": str(recipe.get("id")),
        "label": recipe.get("name") or f"Recipe {recipe.get('id')}",
        "description": f"{', '.join(apps) if apps else 'no apps'} · {status}",
        "applications": apps,
        "running": running,
        "job_succeeded_count": recipe.get("job_succeeded_count", 0),
        "raw": {
            k: v for k, v in recipe.items() if k != "code"
        },
    }


def _list_job_run_items(limit_recipes: int = 15, jobs_per_recipe: int = 3) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    recipes = _list_recipes_raw()[:limit_recipes]
    for recipe in recipes:
        recipe_id = recipe.get("id")
        if not recipe_id:
            continue
        try:
            jobs_data = _request("GET", f"recipes/{recipe_id}/jobs")
        except Exception as exc:
            logger.debug("Skip jobs for recipe %s: %s", recipe_id, exc)
            continue
        for job in (jobs_data.get("items") or [])[:jobs_per_recipe]:
            job_id = job.get("id") or job.get("handle")
            if not job_id:
                continue
            composite = f"{recipe_id}:{job_id}"
            items.append(
                {
                    "name": composite,
                    "label": job.get("title") or str(job_id),
                    "description": (
                        f"recipe {recipe_id} · {job.get('status', 'unknown')} · "
                        f"{job.get('completed_at') or job.get('started_at') or ''}"
                    ),
                    "recipe_id": recipe_id,
                    "job_id": job_id,
                    "status": job.get("status"),
                    "raw": job,
                }
            )
    return items


def list_items(category: str) -> dict[str, Any]:
    if category == "connections":
        raw = _list_connections_raw()
        items = [_connection_item(c) for c in raw]
    elif category == "recipes":
        raw = _list_recipes_raw()
        items = [_recipe_item(r) for r in raw]
    elif category == "job_runs":
        items = _list_job_run_items()
    else:
        raise LookupError(f"Unknown category '{category}'")

    return {"category": category, "total": len(items), "items": items, "mode": "live"}


def get_item_detail(category: str, item_id: str) -> dict[str, Any]:
    if category == "connections":
        connections = _list_connections_raw()
        match = next((c for c in connections if str(c.get("id")) == item_id), None)
        if not match:
            raise LookupError(f"Connection '{item_id}' not found")
        return {
            "category": category,
            "mode": "live",
            "name": item_id,
            "label": match.get("name"),
            "description": match.get("application") or match.get("provider"),
            "fields": {
                "application": match.get("application") or match.get("provider"),
                "authorization_status": match.get("authorization_status"),
                "authorized_at": match.get("authorized_at"),
                "authorization_error": match.get("authorization_error"),
                "project_id": match.get("project_id"),
                "folder_id": match.get("folder_id"),
                "created_at": match.get("created_at"),
                "updated_at": match.get("updated_at"),
            },
            "raw": match,
        }

    if category == "recipes":
        recipe = _request("GET", f"recipes/{item_id}")
        recent_jobs: list[dict[str, Any]] = []
        try:
            jobs_data = _request("GET", f"recipes/{item_id}/jobs")
            recent_jobs = jobs_data.get("items") or []
        except Exception as exc:
            logger.warning("Could not load jobs for recipe %s: %s", item_id, exc)

        code = recipe.get("code")
        if isinstance(code, str) and len(code) > 2000:
            recipe = {**recipe, "code": code[:2000] + "… [truncated]"}

        return {
            "category": category,
            "mode": "live",
            "name": item_id,
            "label": recipe.get("name"),
            "description": recipe.get("description"),
            "fields": {
                "applications": recipe.get("applications"),
                "trigger_application": recipe.get("trigger_application"),
                "running": recipe.get("running"),
                "job_succeeded_count": recipe.get("job_succeeded_count"),
                "job_failed_count": recipe.get("job_failed_count"),
                "last_run_at": recipe.get("last_run_at"),
                "config": recipe.get("config"),
            },
            "recent_jobs": recent_jobs,
            "raw": recipe,
        }

    if category == "job_runs":
        if ":" not in item_id:
            raise LookupError("Job item id must be recipe_id:job_id")
        recipe_id, job_id = item_id.split(":", 1)
        job = get_job_detail(recipe_id, job_id)
        return {
            "category": category,
            "mode": "live",
            "name": item_id,
            "label": job.get("title") or job_id,
            "description": f"Status: {job.get('status')}",
            "fields": {
                "status": job.get("status"),
                "started_at": job.get("started_at"),
                "completed_at": job.get("completed_at"),
                "is_test": job.get("is_test"),
                "lines_count": len(job.get("lines") or []),
            },
            "lines": job.get("lines") or [],
            "raw": job,
        }

    raise LookupError(f"Unknown category '{category}'")


def get_job_detail(recipe_id: str, job_id: str) -> dict[str, Any]:
    return _request("GET", f"recipes/{recipe_id}/jobs/{job_id}")

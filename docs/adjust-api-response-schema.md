# Adjust Report Service API — Response Schema Documentation

Live-only connector. No demo mode — credentials required in `backend/.env`.

Adjust provides mobile app attribution metadata via the **Report Service (RS) API**. This connector reads filter catalogs and event definitions used when building reports.

**Docs:** https://dev.adjust.com/en/api/rs-api/

---

## Authentication

| Variable | Description |
|----------|-------------|
| `ADJUST_API_TOKEN` | Bearer token from Adjust dashboard → Account settings → My profile → API Token |

Header sent on every upstream call:

```
Authorization: Bearer {ADJUST_API_TOKEN}
```

---

## POC Endpoints

| Purpose | URL |
|---------|-----|
| Connect / test | `GET /api/v1/adjust/connect` |
| Categories | `GET /api/v1/adjust/categories` |
| List items | `GET /api/v1/adjust/items?category=apps` |
| Item detail | `GET /api/v1/adjust/items/{id}?category=apps` |

**Categories:** `apps`, `events`, `overview_metrics`, `event_metrics`, `cost_metrics`, `cohort_metrics`, `skad_metrics`, `dimensions`, `networks`, `countries`

---

## Adjust vs Salesforce terminology

| Salesforce | Adjust |
|------------|--------|
| SObject | App / Metric / Dimension / Event |
| Field | Metric `id`, dimension `id`, event slug |
| Describe | `filters_data` + `events` endpoints |
| Record | App token, event token, or metric row |

---

## Underlying Adjust RS API

| Resource | Endpoint |
|----------|----------|
| Filter catalogs | `GET https://automate.adjust.com/reports-service/filters_data?required_filters=apps,overview_metrics,...` |
| Events | `GET https://automate.adjust.com/reports-service/events?tokens_mapping=true` |

### filters_data response shape

```json
{
  "apps": [
    {
      "id": "abc123token",
      "name": "My iOS App",
      "short_name": "iOS",
      "section": "",
      "formatting": "string"
    }
  ],
  "overview_metrics": [
    {
      "id": "installs",
      "name": "Installs",
      "short_name": "Inst",
      "section": "Installs",
      "formatting": "integer"
    }
  ]
}
```

### events response shape

Array of event objects:

```json
[
  {
    "id": "purchase",
    "name": "Purchase event",
    "short_name": "PUR",
    "section": "Revenue",
    "formatting": "money",
    "description": "",
    "app_token": ["4zb92bmajmrd"],
    "tokens": ["abc123"],
    "is_skad_event": false,
    "app_token_x_event_tokens_mapping": {
      "4zb92bmajmrd": ["abc123"]
    }
  }
]
```

---

## Connect response (`GET /api/v1/adjust/connect`)

```json
{
  "connected": true,
  "mode": "live",
  "apps_count": 2,
  "events_count": 15,
  "sample_app": "My Android App",
  "auth_method": "API Token (Bearer)",
  "api_base": "https://automate.adjust.com/reports-service",
  "plan_note": "Free Base plan: 1,500 attributions/month (12 months)"
}
```

---

## Categories response (`GET /api/v1/adjust/categories`)

```json
[
  {
    "id": "apps",
    "label": "Apps",
    "description": "Mobile apps registered in your Adjust account (app tokens)",
    "items_count": 2
  }
]
```

---

## Items response (`GET /api/v1/adjust/items?category=overview_metrics`)

```json
{
  "category": "overview_metrics",
  "total": 42,
  "items": [
    {
      "name": "installs",
      "label": "Installs",
      "description": "section=Installs · format=integer",
      "raw": {
        "id": "installs",
        "name": "Installs",
        "short_name": "Inst",
        "section": "Installs",
        "formatting": "integer"
      }
    }
  ],
  "mode": "live"
}
```

---

## Item detail response (`GET /api/v1/adjust/items/{id}?category=events`)

```json
{
  "name": "purchase",
  "label": "Purchase event",
  "description": "section=Revenue · format=money · apps=1",
  "raw": { "...": "..." },
  "category": "events",
  "mode": "live",
  "fields": { "...": "..." }
}
```

---

## HTTP error mapping

| Upstream | POC status | Meaning |
|----------|------------|---------|
| 401 | 401 | Invalid or missing API token |
| 403 | 403 | Token lacks permission |
| 429 | 502 | Rate limit exceeded |
| 404 (item) | 404 | Unknown category or item id |
| Other 4xx/5xx | 502 | Adjust API error |

---

## Free account notes

- Sign up at https://www.adjust.com — **Base** plan includes 1,500 attributions/month for 12 months
- Add at least one mobile app (iOS/Android) and integrate the Adjust SDK for live attribution data
- API Token is per-user under **Account settings → My profile**
- Empty apps/events lists are valid if no app is configured yet — token still validates via `filters_data`

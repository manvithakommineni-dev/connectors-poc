# Google Analytics 4 (GA4) API — Response Schema Documentation

Live-only connector. No demo mode — credentials required in `backend/.env`.

---

## Authentication

| Variable | Description |
|----------|-------------|
| `GA4_PROPERTY_ID` | Numeric GA4 property ID (Admin → Property Settings) |
| `GA4_SERVICE_ACCOUNT_FILE` | Absolute path to Google Cloud service account JSON key |

**Setup (FREE):**
1. Create GA4 property at https://analytics.google.com
2. Google Cloud Console → enable **Google Analytics Data API** + **Google Analytics Admin API**
3. Create service account → download JSON key
4. GA4 → Admin → Property Access Management → add service account email as **Viewer**

---

## Endpoints

| Purpose | URL |
|---------|-----|
| Connect / test | `GET /api/v1/ga4/connect` |
| List categories | `GET /api/v1/ga4/categories` |
| List items by category | `GET /api/v1/ga4/items?category=dimensions` |
| Item detail | `GET /api/v1/ga4/items/{name}?category=dimensions` |

**Categories:** `dimensions`, `metrics`, `custom_dimensions`, `custom_metrics`, `data_streams`

---

## 1. GET /api/v1/ga4/connect

**Example Response**

```json
{
  "connected": true,
  "mode": "live",
  "property_id": "123456789",
  "property_name": "My Website",
  "time_zone": "Asia/Calcutta",
  "currency_code": "INR",
  "industry_category": "TECHNOLOGY",
  "service_level": "GOOGLE_ANALYTICS_STANDARD",
  "dimensions_count": 320,
  "metrics_count": 85,
  "auth_method": "Service Account (Google Cloud JSON key)"
}
```

| Key | Type | Description |
|-----|------|-------------|
| `connected` | boolean | `true` when credentials and property access are valid |
| `mode` | string | Always `"live"` |
| `property_id` | string | Numeric GA4 property ID |
| `property_name` | string | Display name from Admin API |
| `time_zone` | string | Property timezone (IANA) |
| `currency_code` | string | ISO 4217 currency |
| `dimensions_count` | integer | Total queryable dimensions from Metadata API |
| `metrics_count` | integer | Total queryable metrics from Metadata API |

---

## 2. GET /api/v1/ga4/categories

**Example Response**

```json
[
  {
    "id": "dimensions",
    "label": "Dimensions",
    "description": "Attributes that describe user sessions and events",
    "items_count": 320
  },
  {
    "id": "metrics",
    "label": "Metrics",
    "description": "Quantitative measurements",
    "items_count": 85
  }
]
```

---

## 3. GET /api/v1/ga4/items?category=dimensions

**Example Response**

```json
{
  "category": "dimensions",
  "total": 320,
  "mode": "live",
  "items": [
    {
      "name": "country",
      "label": "Country",
      "description": "The country from which the user activity originated.",
      "category": "GEO",
      "custom_definition": false,
      "deprecated": false
    }
  ]
}
```

### Dimension item fields

| Key | Type | Description |
|-----|------|-------------|
| `name` | string | API name used in GA4 Data API queries |
| `label` | string | Human-readable UI name |
| `description` | string | Field description |
| `category` | string | Group: GEO, TIME, USER, TRAFFIC_SOURCE, etc. |
| `custom_definition` | boolean | Whether this is a custom dimension |
| `deprecated` | boolean | Whether deprecated API names exist |

### Metric item fields

| Key | Type | Description |
|-----|------|-------------|
| `name` | string | API name (e.g. `activeUsers`, `sessions`) |
| `label` | string | Display name |
| `type` | string | TYPE_INTEGER, TYPE_FLOAT, TYPE_SECONDS, etc. |
| `expression` | string | Formula for calculated metrics |
| `custom_definition` | boolean | Custom metric flag |

---

## 4. Underlying Google APIs

| API | Endpoint | Purpose |
|-----|----------|---------|
| Data API | `GET /v1beta/properties/{id}/metadata` | Dimensions + metrics catalog |
| Admin API | `GET /v1beta/properties/{id}` | Property info |
| Admin API | `GET /v1beta/properties/{id}/customDimensions` | Custom dimensions |
| Admin API | `GET /v1beta/properties/{id}/customMetrics` | Custom metrics |
| Admin API | `GET /v1beta/properties/{id}/dataStreams` | Web/app streams |

**Docs:** https://developers.google.com/analytics/devguides/reporting/data/v1

---

## GA4 vs Salesforce terminology

| Salesforce | GA4 |
|------------|-----|
| SObject | Dimension / Metric / Event |
| Field | `apiName` (e.g. `country`, `activeUsers`) |
| Describe API | Metadata API `getMetadata` |
| Record | Report row from `runReport` |

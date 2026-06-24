# Google Ads API — Response Schema Documentation

This document describes every key-value pair returned by the Google Ads metadata endpoints exposed by this backend.

---

## Live connector overview

When `GADS_DEVELOPER_TOKEN` and OAuth credentials are configured, the connector runs in **live mode** and calls the real **Google Ads API v24** (`GoogleAdsFieldService`).

| Endpoint | Live behavior |
|----------|---------------|
| `/connect` | Probes live API — returns `customer_id` and connection status |
| `/categories` | Curated category list (5 groups) with static `resources_count` |
| `/resources` | Curated resource list (9 resources) with hand-authored descriptions and GAQL examples |
| `/resources/{name}/fields` | **Fully live** — fetches all fields for the resource from `GoogleAdsFieldService` (typically 50–200+ fields per resource) |

> **Hybrid design:** Categories and resource names are a curated navigation catalog. Field metadata is fetched live from Google so you always see the complete, up-to-date schema for your account's API version.

**Fallback:** If `GADS_DEVELOPER_TOKEN` is empty, all endpoints return built-in demo schema (same 9 resources, ~107 hand-authored fields).

---

## Background — How Google Ads Exposes Metadata

Google Ads uses:

1. **GAQL (Google Ads Query Language)** — SQL-like language to query resources and fields
2. **GoogleAdsFieldService** — metadata service describing every queryable field

**Key Google API endpoints (live mode):**

| Purpose | Endpoint |
|---------|----------|
| Field metadata search | `POST https://googleads.googleapis.com/v24/googleAdsFields:search` |
| List accessible accounts | `GET https://googleads.googleapis.com/v24/customers:listAccessibleCustomers` |
| Run GAQL query | `POST https://googleads.googleapis.com/v24/customers/{id}/googleAds:search` |

**Key concept mapping:**

| Traditional DB | Salesforce | GA4 | Google Ads |
|----------------|------------|-----|------------|
| Database / Schema | Org | Property | **Customer (Account)** |
| Schema / Domain | — | Category | **Category** (campaigns, adGroups, etc.) |
| Table | SObject | Business Object | **Resource** (`campaign`, `ad_group`) |
| Column / Field | Field | apiName | **Field** (`campaign.name`, `metrics.clicks`) |
| Row | Record | Report row | **GAQL query result row** |
| Performance data | — | Metric | **Metric** (`metrics.*`) |
| Group-by dimension | — | Segment | **Segment** (`segments.*`) |

**Field categories in Google Ads:**

| Category | Prefix | Purpose |
|----------|--------|---------|
| `ATTRIBUTE` | `campaign.name`, `ad_group.status` | Descriptive settings and entity properties |
| `METRIC` | `metrics.clicks`, `metrics.cost_micros` | Performance numbers |
| `SEGMENT` | `segments.date`, `segments.device` | Grouping dimensions for metrics |
| `RESOURCE` | Resource references | Related sub-resource links |

---

## Authentication & Setup

| Variable | Required | Description |
|----------|----------|-------------|
| `GADS_DEVELOPER_TOKEN` | Yes (live) | Developer token from Google Ads → Tools → API Center |
| `GADS_CLIENT_ID` | Yes (live) | OAuth 2.0 Client ID from Google Cloud Console |
| `GADS_CLIENT_SECRET` | Yes (live) | OAuth 2.0 Client Secret |
| `GADS_REFRESH_TOKEN` | Yes (live) | Long-lived refresh token from OAuth flow |
| `GADS_CUSTOMER_ID` | Yes (live) | Google Ads Customer ID (digits only, no dashes) |
| `GADS_LOGIN_CUSTOMER_ID` | MCC only | Manager (MCC) account ID — sent as `login-customer-id` header when accessing client accounts via an MCC developer token |

**Setup:**
1. Create a Google Cloud project and enable **Google Ads API**
2. Create OAuth 2.0 credentials (Desktop app) and run the OAuth flow to get a refresh token
3. Apply for a Developer Token in Google Ads → Tools → API Center (test token is free)
4. Set all env vars in `backend/.env`

**Authentication headers (live):**
- `Authorization: Bearer {access_token}` — from OAuth refresh
- `developer-token: {GADS_DEVELOPER_TOKEN}`
- `login-customer-id: {GADS_LOGIN_CUSTOMER_ID}` — only when using MCC access

---

## Endpoints

| Purpose | URL |
|---------|-----|
| Connect / test | `GET /api/v1/googleads/connect` |
| List categories | `GET /api/v1/googleads/categories` |
| List resources | `GET /api/v1/googleads/resources?category={id}` |
| Resource fields (live) | `GET /api/v1/googleads/resources/{resource_name}/fields` |

---

## Table of Contents

1. [GET /api/v1/googleads/connect](#1-get-apiv1googleadsconnect)
2. [GET /api/v1/googleads/categories](#2-get-apiv1googleadscategories)
3. [GET /api/v1/googleads/resources](#3-get-apiv1googleadsresources)
4. [GET /api/v1/googleads/resources/{resource_name}/fields](#4-get-apiv1googleadsresourcesresource_namefields)
5. [Field Data Type Reference](#5-field-data-type-reference)
6. [Field Category Reference](#6-field-category-reference)
7. [Category & Resource Reference](#7-category--resource-reference)
8. [GAQL Query Examples](#8-gaql-query-examples)
9. [Demo Mode Fallback](#9-demo-mode-fallback)

---

## 1. GET /api/v1/googleads/connect

Tests Google Ads connectivity. In **live mode** (credentials configured), probes `GoogleAdsFieldService` with `SELECT name, category WHERE name = 'campaign'`. In demo mode, returns a static schema summary.

### Live Mode Response (primary)

```json
{
  "connected": true,
  "mode": "live",
  "customer_id": "1234567890",
  "sample_resources": 1
}
```

| Key | Type | Description |
|-----|------|-------------|
| `connected` | `boolean` | Always `true` on success. `503` if OAuth or developer token fails. |
| `mode` | `string` | Always `"live"` when credentials are configured. |
| `customer_id` | `string` | Value from `GADS_CUSTOMER_ID` in `.env` (digits only). The Google Ads account used for GAQL queries. |
| `sample_resources` | `integer` | Records returned from the live probe query. `1` confirms `GoogleAdsFieldService` is reachable and the developer token is valid. |

---

## 2. GET /api/v1/googleads/categories

Lists five curated resource categories for UI navigation.

> Returns a **raw JSON array** (not wrapped in `{total, categories}`).

```json
[
  {
    "id": "campaigns",
    "label": "Campaigns",
    "description": "Campaign settings, budgets, targeting, bidding strategies",
    "resources_count": 2
  },
  {
    "id": "adGroups",
    "label": "Ad Groups",
    "description": "Ad Groups, Individual Ads, Keywords, Criteria",
    "resources_count": 2
  },
  {
    "id": "ads",
    "label": "Ads & Creatives",
    "description": "Individual ads, responsive search ads, display ads, performance",
    "resources_count": 1
  },
  {
    "id": "performance",
    "label": "Performance & Reports",
    "description": "Search terms, geographic performance, audience insights",
    "resources_count": 2
  },
  {
    "id": "account",
    "label": "Account",
    "description": "Customer account info, conversion actions, billing",
    "resources_count": 2
  }
]
```

| Key | Type | Description |
|-----|------|-------------|
| `id` | `string` | Category ID for `/resources?category={id}` — `campaigns`, `adGroups`, `ads`, `performance`, `account` |
| `label` | `string` | Human-readable category name |
| `description` | `string` | What resources this category covers |
| `resources_count` | `integer` | Number of curated resources in this category (static count from catalog) |

---

## 3. GET /api/v1/googleads/resources

Lists curated Google Ads resources — the entities used in GAQL `FROM` clauses.

**Query Parameter:** `category` (optional) — filter by category ID.

### Live Mode Response

```json
{
  "total": 2,
  "mode": "live",
  "resources": [
    {
      "name": "campaign",
      "label": "Campaign",
      "category": "campaigns",
      "description": "Top-level campaign resource. Controls budget, targeting, and bidding for a group of ads.",
      "fields_count": 20,
      "gaql_example": "SELECT campaign.id, campaign.name, campaign.status, metrics.clicks, metrics.impressions, metrics.cost_micros FROM campaign WHERE campaign.status = 'ENABLED'"
    }
  ]
}
```

### Top-Level Response

| Key | Type | Description |
|-----|------|-------------|
| `total` | `integer` | Count of resources returned (after category filter) |
| `mode` | `string` | `"live"` when credentials configured; `"demo"` otherwise |
| `resources` | `array<object>` | Curated resource list — see below |

### Each Resource Entry

| Key | Type | Description |
|-----|------|-------------|
| `name` | `string` | Resource name for `/resources/{name}/fields` and GAQL `FROM` clause (e.g. `campaign`, `ad_group`, `search_term_view`) |
| `label` | `string` | Display name (e.g. `"Campaign"`, `"Keywords / Criteria"`) |
| `category` | `string` | Parent category ID |
| `description` | `string` | Plain-English description of the resource |
| `fields_count` | `integer` | Field count from **curated catalog** in list view. Use `/fields` endpoint for the live total (usually much higher). |
| `gaql_example` | `string` | Ready-to-use GAQL query example |

---

## 4. GET /api/v1/googleads/resources/{resource_name}/fields

**Primary live metadata endpoint.** Fetches all fields for a resource from `GoogleAdsFieldService`:

```
SELECT name, category, data_type, filterable, selectable, sortable, is_repeated
WHERE name LIKE '{resource_name}.%'
```

**Path Parameter:** `resource_name` — e.g. `campaign`, `ad_group`, `customer`, `search_term_view`

### Live Mode Response

```json
{
  "name": "campaign",
  "label": "Campaign",
  "category": "",
  "description": "",
  "fields_count": 187,
  "mode": "live",
  "gaql_example": "SELECT campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type, campaign.bidding_strategy_type FROM campaign LIMIT 10",
  "fields": [
    {
      "name": "campaign.id",
      "label": "Id",
      "data_type": "INT64",
      "category": "ATTRIBUTE",
      "filterable": true,
      "selectable": true,
      "sortable": true,
      "is_repeated": false,
      "description": ""
    },
    {
      "name": "metrics.clicks",
      "label": "Clicks",
      "data_type": "INT64",
      "category": "METRIC",
      "filterable": true,
      "selectable": true,
      "sortable": true,
      "is_repeated": false,
      "description": ""
    },
    {
      "name": "segments.date",
      "label": "Date",
      "data_type": "STRING",
      "category": "SEGMENT",
      "filterable": true,
      "selectable": true,
      "sortable": true,
      "is_repeated": false,
      "description": ""
    }
  ]
}
```

### Top-Level Response (live vs demo)

| Key | Type | Live mode | Demo mode |
|-----|------|-----------|-----------|
| `name` | `string` | Resource name from URL | Same |
| `label` | `string` | Auto-generated from name (`"Ad Group Criterion"`) | Hand-authored label |
| `category` | `string` | Empty string `""` | Category ID (e.g. `"campaigns"`) |
| `description` | `string` | Empty string `""` | Hand-authored description |
| `fields_count` | `integer` | Live count from API (often 50–200+) | Curated count (~7–20) |
| `mode` | `string` | `"live"` | `"demo"` |
| `gaql_example` | `string` | Auto-generated from first 5 `ATTRIBUTE` fields | Hand-authored example |
| `fields` | `array` | All fields from `GoogleAdsFieldService` | Curated subset with descriptions |

### Each Field Entry

| Key | Type | Description |
|-----|------|-------------|
| `name` | `string` | Fully-qualified GAQL field name in dot notation (e.g. `campaign.id`, `metrics.clicks`, `ad_group_criterion.keyword.text`) |
| `label` | `string` | Display label. **Live:** auto-generated from field name (strip prefix, title-case). **Demo:** hand-authored. |
| `data_type` | `string` | `INT64`, `STRING`, `DOUBLE`, `BOOLEAN`, `ENUM`, `MESSAGE`, `INT32` — see [Section 5](#5-field-data-type-reference) |
| `category` | `string` | `ATTRIBUTE`, `METRIC`, `SEGMENT`, or `RESOURCE` — see [Section 6](#6-field-category-reference) |
| `filterable` | `boolean` | Can be used in GAQL `WHERE` clause |
| `selectable` | `boolean` | Can be included in GAQL `SELECT` clause |
| `sortable` | `boolean` | Can be used in GAQL `ORDER BY` clause |
| `is_repeated` | `boolean` | Field holds multiple values (e.g. `ad_group_ad.ad.final_urls`) |
| `description` | `string` | Field explanation. **Live:** usually empty (API does not return descriptions in field search). **Demo:** includes enum values and micros notes. |

---

## 5. Field Data Type Reference

| `data_type` | Description |
|-------------|-------------|
| `INT64` | 64-bit integer — IDs, counts, monetary amounts in **micros** (÷ 1,000,000 for currency) |
| `INT32` | 32-bit integer — e.g. quality score (1–10) |
| `DOUBLE` | Floating-point — rates, ratios (`metrics.ctr`, `metrics.conversions`) |
| `STRING` | Text — names, dates (`YYYY-MM-DD`), resource names |
| `BOOLEAN` | `true` / `false` flags |
| `ENUM` | Fixed string values — `ENABLED`, `PAUSED`, `REMOVED`, `SEARCH`, `DISPLAY`, etc. |
| `MESSAGE` | Nested/complex objects — RSA headlines, conversion tag snippets |

> **Micros:** `metrics.cost_micros = 5000000` → $5.00

---

## 6. Field Category Reference

| `category` | Prefix | GAQL usage | Description |
|------------|--------|------------|-------------|
| `ATTRIBUTE` | `{resource}.*` | SELECT, WHERE, ORDER BY | Entity properties — names, status, budgets, bids |
| `METRIC` | `metrics.*` | SELECT, WHERE, ORDER BY | Performance numbers — clicks, spend, conversions |
| `SEGMENT` | `segments.*` | SELECT, WHERE | Breakdown dimensions — date, device, network |
| `RESOURCE` | Resource refs | SELECT | Links to related resources |

---

## 7. Category & Resource Reference

Curated navigation catalog (9 resources). Live `/fields` returns the full schema for each.

### Campaigns

| Resource | Label | Catalog fields | Notable live fields |
|----------|-------|----------------|---------------------|
| `campaign` | Campaign | 20 | `campaign.id`, `campaign.status`, `campaign.advertising_channel_type`, `metrics.clicks`, `metrics.cost_micros`, `segments.date` |
| `campaign_budget` | Campaign Budget | 7 | `campaign_budget.amount_micros`, `campaign_budget.delivery_method` |

### Ad Groups

| Resource | Label | Catalog fields | Notable live fields |
|----------|-------|----------------|---------------------|
| `ad_group` | Ad Group | 11 | `ad_group.id`, `ad_group.campaign`, `ad_group.cpc_bid_micros` |
| `ad_group_criterion` | Keywords / Criteria | 12 | `ad_group_criterion.keyword.text`, `ad_group_criterion.keyword.match_type` |

### Ads & Creatives

| Resource | Label | Catalog fields | Notable live fields |
|----------|-------|----------------|---------------------|
| `ad_group_ad` | Ad | 12 | `ad_group_ad.ad.type`, `ad_group_ad.ad.final_urls`, `ad_group_ad.policy_summary.approval_status` |

### Performance & Reports

| Resource | Label | Catalog fields | Notable live fields |
|----------|-------|----------------|---------------------|
| `search_term_view` | Search Term View | 7 | `search_term_view.search_term`, `metrics.clicks` |
| `geographic_view` | Geographic View | 7 | `geographic_view.country_criterion_id`, `metrics.conversions` |

### Account

| Resource | Label | Catalog fields | Notable live fields |
|----------|-------|----------------|---------------------|
| `customer` | Customer (Account) | 10 | `customer.id`, `customer.descriptive_name`, `customer.currency_code` |
| `conversion_action` | Conversion Action | 7 | `conversion_action.type`, `conversion_action.status` |

---

## 8. GAQL Query Examples

Use these with `POST /v24/customers/{customer_id}/googleAds:search` or the Google Ads Query tool.

| Resource | Example GAQL |
|----------|--------------|
| `campaign` | `SELECT campaign.id, campaign.name, campaign.status, metrics.clicks, metrics.cost_micros FROM campaign WHERE campaign.status = 'ENABLED'` |
| `ad_group` | `SELECT ad_group.id, ad_group.name, metrics.clicks FROM ad_group WHERE campaign.status = 'ENABLED'` |
| `ad_group_criterion` | `SELECT ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, metrics.clicks FROM ad_group_criterion WHERE ad_group_criterion.type = 'KEYWORD'` |
| `search_term_view` | `SELECT search_term_view.search_term, metrics.clicks FROM search_term_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.clicks DESC LIMIT 100` |
| `customer` | `SELECT customer.id, customer.descriptive_name, customer.currency_code, metrics.cost_micros FROM customer` |

**GAQL rules:**
- Dot notation: `resource.field` or `resource.nested.field`
- Metrics: `metrics.*` prefix; segments: `segments.*` prefix
- Status values: uppercase strings (`'ENABLED'`, `'PAUSED'`, `'REMOVED'`)
- Date ranges: `WHERE segments.date DURING LAST_30_DAYS`
- Money: micros (÷ 1,000,000)

---

## 9. Demo Mode Fallback

When `GADS_DEVELOPER_TOKEN` is **not** set, all endpoints return built-in schema. No Google account needed.

### Demo `/connect` response

```json
{
  "connected": true,
  "mode": "demo",
  "message": "Running in Demo Mode — showing real Google Ads API v17 field schema. Set GADS_DEVELOPER_TOKEN, GADS_CLIENT_ID, GADS_CLIENT_SECRET, GADS_REFRESH_TOKEN, GADS_CUSTOMER_ID in .env to connect to a real account.",
  "categories_count": 5,
  "total_resources": 9,
  "total_fields": 107,
  "api_version": "v24"
}
```

| Key | Type | Description |
|-----|------|-------------|
| `connected` | `boolean` | Always `true` in demo |
| `mode` | `string` | `"demo"` |
| `message` | `string` | Instructions to switch to live mode |
| `categories_count` | `integer` | 5 |
| `total_resources` | `integer` | 9 |
| `total_fields` | `integer` | ~107 across all resources |
| `api_version` | `string` | `"v24"` |

In demo mode, `/resources/{name}/fields` returns the curated field list with hand-authored labels and descriptions instead of live API data.

---

*Generated from backend source: `backend/googleads/service.py` — `test_connection()`, `list_categories()`, `list_resources()`, and `get_resource_fields()`*

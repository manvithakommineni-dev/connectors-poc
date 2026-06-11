# Google Ads API — Response Schema Documentation

This document describes every key-value pair returned by the Google Ads metadata endpoints exposed by this backend.

---

## Background — How Google Ads Exposes Metadata

Google Ads does not use a traditional database-style schema API. Instead it uses:

1. **GAQL (Google Ads Query Language)** — SQL-like language to query resources and fields
2. **GoogleAdsFieldService** — metadata service that describes every queryable field

**Key Google API endpoints (live mode):**

| Purpose              | Endpoint |
|----------------------|----------|
| Field metadata search | `POST https://googleads.googleapis.com/v17/googleAdsFields:search` |
| List accessible accounts | `GET https://googleads.googleapis.com/v17/customers:listAccessibleCustomers` |
| Run GAQL query       | `POST https://googleads.googleapis.com/v17/customers/{id}/googleAds:search` |

**Key concept mapping:**

| Traditional DB     | Salesforce      | SAP              | NetSuite        | ServiceNow       | Google Ads                    |
|--------------------|-----------------|------------------|-----------------|------------------|-------------------------------|
| Database / Schema  | Org             | System           | Account         | Instance         | **Customer (Account)**        |
| Schema / Domain    | —               | OData Service    | Module          | Category         | **Category**                  |
| Table              | SObject         | EntityType       | Record Type     | Table            | **Resource**                  |
| Column / Field     | Field           | Property         | Field           | Column           | **Field** (`resource.field`)  |
| Row                | Record          | Entity           | Record          | Record           | **Row** (query result)        |
| Foreign Key        | Relationship    | NavigationProp   | `referenceType` | Reference field  | **Resource name** (`STRING`) |
| Performance data   | —               | —                | —               | —                | **Metric** (`metrics.*`)      |
| Group-by dimension | —               | —                | —               | —                | **Segment** (`segments.*`)    |

**Field categories in Google Ads (unique to this platform):**

| Category    | Prefix / Pattern   | Purpose |
|-------------|--------------------|---------|
| `ATTRIBUTE` | `campaign.name`, `ad_group.status` | Descriptive settings and entity properties |
| `METRIC`    | `metrics.clicks`, `metrics.cost_micros` | Performance numbers (clicks, spend, conversions) |
| `SEGMENT`   | `segments.date`, `segments.device` | Dimensions for breaking down metrics |
| `RESOURCE`  | Resource references | Related sub-resource links |

**Two operating modes:**
- **Demo Mode** — when `GADS_DEVELOPER_TOKEN` is not set in `.env`, returns built-in metadata based on real Google Ads API v17 field definitions (5 categories, 9 resources, 100+ fields). No Google Ads account needed.
- **Live Mode** — when `GADS_DEVELOPER_TOKEN`, `GADS_CLIENT_ID`, `GADS_CLIENT_SECRET`, `GADS_REFRESH_TOKEN`, and `GADS_CUSTOMER_ID` are set, authenticates via OAuth 2.0 and queries the real `GoogleAdsFieldService`.

**Authentication (live mode):** OAuth 2.0 with offline refresh token + Developer Token header.
- Token URL: `https://oauth2.googleapis.com/token`
- API Base: `https://googleads.googleapis.com/v17`
- Required header: `developer-token: <GADS_DEVELOPER_TOKEN>`

---

## Table of Contents

1. [GET /api/v1/googleads/connect](#1-get-apiv1googleadsconnect)
2. [GET /api/v1/googleads/categories](#2-get-apiv1googleadscategories)
   - [Each Category Entry](#21-each-category-entry)
3. [GET /api/v1/googleads/resources](#3-get-apiv1googleadsresources)
   - [Query Parameters](#query-parameters)
   - [Top-Level Response](#31-top-level-response)
   - [Each Resource Summary Entry](#32-each-resource-summary-entry-inside-resources-array)
4. [GET /api/v1/googleads/resources/{resource_name}/fields](#4-get-apiv1googleadsresourcesresource_namefields)
   - [Top-Level Response](#41-top-level-response)
   - [Each Field Entry](#42-each-field-entry-inside-fields-array)
5. [Field Data Type Reference](#5-field-data-type-reference)
6. [Field Category Reference](#6-field-category-reference)
7. [Category & Resource Reference](#7-category--resource-reference)
8. [GAQL Query Examples](#8-gaql-query-examples)

---

## 1. GET /api/v1/googleads/connect

Tests Google Ads connectivity. In Demo Mode returns a schema summary. In Live Mode queries `GoogleAdsFieldService` with a 1-record probe to confirm OAuth, Developer Token, and API access are working.

**Example — Demo Mode Response**

```json
{
  "connected": true,
  "mode": "demo",
  "message": "Running in Demo Mode — showing real Google Ads API v17 field schema. Set GADS_DEVELOPER_TOKEN, GADS_CLIENT_ID, GADS_CLIENT_SECRET, GADS_REFRESH_TOKEN, GADS_CUSTOMER_ID in .env to connect to a real account.",
  "categories_count": 5,
  "total_resources": 9,
  "total_fields": 107,
  "api_version": "v17"
}
```

**Example — Live Mode Response**

```json
{
  "connected": true,
  "mode": "live",
  "customer_id": "1234567890",
  "sample_resources": 1
}
```

---

### Demo Mode Response Fields

| Key                | Type      | Description |
|--------------------|-----------|-------------|
| `connected`        | `boolean` | Always `true` when this response is returned. A `503` HTTP error is raised instead if OAuth or Developer Token authentication fails in live mode. |
| `mode`             | `string`  | `"demo"` when `GADS_DEVELOPER_TOKEN` is not configured; `"live"` when connected to a real Google Ads account. Present on all endpoint responses. |
| `message`          | `string`  | Human-readable explanation of the current mode with instructions for switching to live mode. Only present in `"demo"` mode. |
| `categories_count` | `integer` | Total number of resource categories in the demo data (Campaigns, Ad Groups, Ads & Creatives, Performance & Reports, Account). Only present in `"demo"` mode. |
| `total_resources`  | `integer` | Total count of Google Ads resources across all categories in demo data. Only present in `"demo"` mode. |
| `total_fields`     | `integer` | Total number of fields across all demo resources. Gives a broad sense of schema coverage. Only present in `"demo"` mode. |
| `api_version`      | `string`  | The Google Ads API version used by this backend (e.g. `"v17"`). Only present in `"demo"` mode. |

### Live Mode Response Fields

| Key                | Type      | Description |
|--------------------|-----------|-------------|
| `connected`        | `boolean` | Always `true` on a successful live response. |
| `mode`             | `string`  | Always `"live"` when a real Google Ads account is connected. |
| `customer_id`      | `string`  | The Google Ads Customer ID from `GADS_CUSTOMER_ID` in `.env` (digits only, no dashes, e.g. `"1234567890"`). This is the account used for all GAQL queries. |
| `sample_resources` | `integer` | Number of records returned from a quick `GoogleAdsFieldService` probe query (`SELECT name FROM google_ads_field WHERE category = 'RESOURCE' LIMIT 1`). Should be `1` on a healthy connection. |

---

## 2. GET /api/v1/googleads/categories

Lists all Google Ads resource categories. These are logical groupings used for navigation — equivalent to "modules" in Oracle/Workday or "categories" in ServiceNow.

> **Note:** Unlike other connectors, this endpoint returns a **raw JSON array** (not wrapped in `{total, categories}`).

**Example Response**

```json
[
  {
    "id": "campaigns",
    "label": "Campaigns",
    "description": "Campaign settings, budgets, targeting, bidding strategies",
    "resources_count": 2
  }
]
```

---

### 2.1 Each Category Entry

| Key               | Type      | Description |
|-------------------|-----------|-------------|
| `id`              | `string`  | The **category identifier** used as the `category` query parameter in `/resources?category={id}` (e.g. `"campaigns"`, `"adGroups"`, `"ads"`, `"performance"`, `"account"`). CamelCase for multi-word IDs. |
| `label`           | `string`  | The **human-readable display name** of the category (e.g. `"Campaigns"`, `"Ad Groups"`, `"Performance & Reports"`). |
| `description`     | `string`  | Brief summary of what Google Ads resources and business area this category covers (e.g. `"Campaign settings, budgets, targeting, bidding strategies"`). |
| `resources_count` | `integer` | Number of resources (queryable entities) available within this category in the demo data. |

---

## 3. GET /api/v1/googleads/resources

Lists Google Ads resources — the queryable entities you use in GAQL `FROM` clauses. In demo mode returns predefined resources; in live mode the same structure is returned (live mode does not dynamically list all resources from the API).

### Query Parameters

| Parameter  | Type     | Default | Description |
|------------|----------|---------|-------------|
| `category` | `string` | `null`  | Filter resources by category ID (e.g. `campaigns`, `adGroups`, `performance`). If omitted, returns all resources across all categories. |

**Example Response**

```json
{
  "total": 2,
  "mode": "demo",
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

---

### 3.1 Top-Level Response

| Key         | Type            | Description |
|-------------|-----------------|-------------|
| `total`     | `integer`       | Total count of resources returned after applying any `category` filter. |
| `mode`      | `string`        | `"demo"` or `"live"`. |
| `resources` | `array<object>` | List of resource descriptors. See [3.2](#32-each-resource-summary-entry-inside-resources-array). |

---

### 3.2 Each Resource Summary Entry (inside `resources` array)

| Key            | Type      | Description |
|----------------|-----------|-------------|
| `name`         | `string`  | The **resource name** used as the `{resource_name}` path parameter in `/resources/{resource_name}/fields` and as the `FROM` clause in GAQL queries (e.g. `"campaign"`, `"ad_group"`, `"ad_group_criterion"`, `"search_term_view"`). Snake_case convention. |
| `label`        | `string`  | The **human-readable display name** for this resource (e.g. `"Campaign"`, `"Keywords / Criteria"`, `"Search Term View"`). |
| `category`     | `string`  | The `id` of the category this resource belongs to (e.g. `"campaigns"`, `"adGroups"`, `"performance"`). |
| `description`  | `string`  | Plain-English description of what this resource represents and what data it holds (e.g. `"Top-level campaign resource. Controls budget, targeting, and bidding for a group of ads."`). |
| `fields_count` | `integer` | Number of fields (attributes, metrics, segments) defined for this resource in the metadata. |
| `gaql_example` | `string`  | A ready-to-use **GAQL query example** demonstrating how to SELECT fields from this resource. Useful for copy-paste into the Google Ads Query tool or API calls. Shows the dot-notation field naming convention. |

---

## 4. GET /api/v1/googleads/resources/{resource_name}/fields

Returns **complete field-level metadata** for one Google Ads resource — all attributes, metrics, and segments with their data types, query capabilities, and descriptions. In live mode this queries `GoogleAdsFieldService` filtered by `resource_name`.

This is the Google Ads equivalent of:
- Salesforce: `GET /api/v1/salesforce/objects/{name}/metadata`
- SAP: `GET /api/v1/sap/services/{service}/entities/{entity}/fields`
- NetSuite: `GET /api/v1/netsuite/records/{record_type}/fields`
- ServiceNow: `GET /api/v1/servicenow/tables/{table}/fields`

**Path Parameter**

| Parameter       | Type     | Description |
|-----------------|----------|-------------|
| `resource_name` | `string` | The resource name (e.g. `campaign`, `ad_group`, `ad_group_criterion`, `search_term_view`, `customer`). Must match a `name` from the resources list. |

**Example Response**

```json
{
  "name": "campaign",
  "label": "Campaign",
  "category": "campaigns",
  "description": "Top-level campaign resource. Controls budget, targeting, and bidding for a group of ads.",
  "fields_count": 20,
  "mode": "demo",
  "gaql_example": "SELECT campaign.id, campaign.name, campaign.status, metrics.clicks, metrics.impressions, metrics.cost_micros FROM campaign WHERE campaign.status = 'ENABLED'",
  "fields": [
    {
      "name": "campaign.id",
      "label": "Campaign ID",
      "data_type": "INT64",
      "category": "ATTRIBUTE",
      "filterable": true,
      "selectable": true,
      "sortable": true,
      "is_repeated": false,
      "description": "Unique ID of the campaign"
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
      "description": "Total number of clicks"
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
      "description": "Date segment (YYYY-MM-DD) for breaking down by day"
    }
  ]
}
```

---

### 4.1 Top-Level Response

| Key            | Type            | Description |
|----------------|-----------------|-------------|
| `name`         | `string`        | The resource name as used in the URL path and GAQL `FROM` clause. |
| `label`        | `string`        | Human-readable display name (e.g. `"Campaign"`, `"Search Term View"`). In live mode, auto-generated from the resource name. |
| `category`     | `string`        | The category `id` this resource belongs to (e.g. `"campaigns"`, `"performance"`). Empty string in live mode (category grouping is not returned by `GoogleAdsFieldService`). |
| `description`  | `string`        | Plain-English description of this resource's purpose. May be empty in live mode. |
| `fields_count` | `integer`       | Total number of fields returned for this resource. |
| `mode`         | `string`        | `"demo"` or `"live"`. |
| `gaql_example` | `string`        | A GAQL query example for this resource. In demo mode this is hand-authored; in live mode it is auto-generated from the first 5 `ATTRIBUTE` fields. |
| `fields`       | `array<object>` | Complete list of field descriptors. See [4.2](#42-each-field-entry-inside-fields-array). |

---

### 4.2 Each Field Entry (inside `fields` array)

| Key           | Type      | Description |
|---------------|-----------|-------------|
| `name`        | `string`  | The **fully-qualified field name** in dot-notation used in GAQL `SELECT`, `WHERE`, and `ORDER BY` clauses (e.g. `"campaign.id"`, `"metrics.clicks"`, `"segments.date"`, `"ad_group_criterion.keyword.text"`). This is the exact string you pass in GAQL queries — there is no separate API name vs display name. |
| `label`       | `string`  | The **human-readable display label** for this field (e.g. `"Campaign ID"`, `"Clicks"`, `"Date"`). In live mode, auto-generated from the field name by stripping the resource prefix and title-casing. |
| `data_type`   | `string`  | The **data type** of the field value as defined by `GoogleAdsFieldService`. See the [Field Data Type Reference](#5-field-data-type-reference) for all values (`"INT64"`, `"STRING"`, `"DOUBLE"`, `"BOOLEAN"`, `"ENUM"`, `"MESSAGE"`, `"INT32"`). |
| `category`    | `string`  | The **field category** — one of `"ATTRIBUTE"`, `"METRIC"`, `"SEGMENT"`, or `"RESOURCE"`. Determines how the field is used in queries. See the [Field Category Reference](#6-field-category-reference). |
| `filterable`  | `boolean` | Whether this field can be used in a GAQL `WHERE` clause to filter results (e.g. `WHERE campaign.status = 'ENABLED'`). `false` for complex/nested fields like `ad_group_ad.ad.responsive_search_ad.headlines`. |
| `selectable`  | `boolean` | Whether this field can be included in a GAQL `SELECT` clause to retrieve its value. Most fields are selectable; some internal-only fields are not. |
| `sortable`    | `boolean` | Whether this field can be used in a GAQL `ORDER BY` clause (e.g. `ORDER BY metrics.clicks DESC`). `false` for enum segment fields like `segments.device` and complex message fields. |
| `is_repeated` | `boolean` | Whether this field can hold **multiple values** (array/list). `true` for fields like `ad_group_ad.ad.final_urls` (multiple landing page URLs) and `conversion_action.tag_snippets`. `false` for scalar fields. |
| `description` | `string`  | A plain-English explanation of what this field represents. For enum fields, may include valid values (e.g. `"ENABLED, PAUSED, REMOVED"` for status fields). For monetary fields, may note the micros convention (`1,000,000 micros = $1`). |

---

## 5. Field Data Type Reference

Google Ads field types come from `GoogleAdsFieldService.dataType`. They are distinct from JSON Schema or EDM types used by other connectors.

| `data_type` | Description |
|-------------|-------------|
| `INT64`     | A 64-bit integer. Used for IDs (`campaign.id`), counts (`metrics.clicks`, `metrics.impressions`), and monetary amounts in **micros** (`metrics.cost_micros` — divide by 1,000,000 for dollars). The most common numeric type. |
| `INT32`     | A 32-bit integer. Used for smaller numeric values like `ad_group_criterion.quality_info.quality_score` (1–10). |
| `DOUBLE`    | A floating-point decimal number. Used for rates and ratios (`metrics.ctr`, `metrics.conversion_rate`, `metrics.conversions`, `campaign.target_roas.target_roas`). |
| `STRING`    | A text value. Used for names (`campaign.name`), dates as strings (`campaign.start_date` in `YYYY-MM-DD`), resource names (`campaign.campaign_budget`), and search terms (`search_term_view.search_term`). |
| `BOOLEAN`   | A `true`/`false` value. Used for flags like `customer.manager` (is MCC account), `customer.auto_tagging_enabled`, `campaign_budget.explicitly_shared`. |
| `ENUM`      | An enumeration with a fixed set of string values. Used for status fields (`ENABLED`, `PAUSED`, `REMOVED`), channel types (`SEARCH`, `DISPLAY`, `SHOPPING`), match types (`EXACT`, `PHRASE`, `BROAD`), and device segments (`MOBILE`, `DESKTOP`, `TABLET`). Values are always uppercase strings in GAQL. |
| `MESSAGE`   | A nested/complex object type. Used for structured fields like `ad_group_ad.ad.responsive_search_ad.headlines` (array of headline assets) and `conversion_action.tag_snippets` (tracking code snippets). Cannot be filtered; typically `is_repeated: true`. |

> **Micros convention:** Google Ads stores all monetary values in **micros** (millionths of the currency unit). `metrics.cost_micros = 5000000` means $5.00. Always divide by 1,000,000 when displaying currency values.

---

## 6. Field Category Reference

Every Google Ads field belongs to one of four categories. This is unique to Google Ads — no other connector in this project has this distinction.

| `category`  | Prefix Pattern    | Used In GAQL As | Description |
|-------------|-------------------|-----------------|-------------|
| `ATTRIBUTE` | `{resource}.*`    | `SELECT`, `WHERE`, `ORDER BY` | **Descriptive properties** of the entity — names, IDs, status, settings, bids, budgets. These describe *what* the entity is. Example: `campaign.name`, `ad_group.status`, `ad_group_criterion.keyword.text`. |
| `METRIC`    | `metrics.*`       | `SELECT`, `WHERE`, `ORDER BY` | **Performance numbers** — clicks, impressions, cost, conversions, CTR, CPC. These describe *how the entity performed*. Metrics require a date range segment when querying (e.g. `segments.date`). Example: `metrics.clicks`, `metrics.cost_micros`. |
| `SEGMENT`   | `segments.*`      | `SELECT`, `WHERE` | **Grouping dimensions** for breaking down metrics — date, device, network, hour. Adding a segment splits one row into multiple rows. Example: `segments.date`, `segments.device`, `segments.ad_network_type`. |
| `RESOURCE`  | Resource refs     | `SELECT`        | **Related resource references** — links to other queryable resources. Less common in field lists; mostly used in the metadata catalog itself. |

---

## 7. Category & Resource Reference

All 5 categories and 9 resources available in this backend.

### Campaigns
*Campaign settings, budgets, targeting, bidding strategies*

| Resource          | Label           | Fields | Notable Fields |
|-------------------|-----------------|--------|----------------|
| `campaign`        | Campaign        | 20     | `campaign.id`, `campaign.name`, `campaign.status`, `campaign.advertising_channel_type`, `campaign.bidding_strategy_type`, `metrics.clicks`, `metrics.cost_micros`, `segments.date` |
| `campaign_budget` | Campaign Budget | 7      | `campaign_budget.amount_micros`, `campaign_budget.delivery_method`, `campaign_budget.explicitly_shared` |

### Ad Groups
*Ad Groups, Keywords, Criteria*

| Resource             | Label               | Fields | Notable Fields |
|----------------------|---------------------|--------|----------------|
| `ad_group`           | Ad Group            | 11     | `ad_group.id`, `ad_group.name`, `ad_group.campaign`, `ad_group.cpc_bid_micros`, `metrics.clicks` |
| `ad_group_criterion` | Keywords / Criteria | 12     | `ad_group_criterion.keyword.text`, `ad_group_criterion.keyword.match_type`, `ad_group_criterion.quality_info.quality_score` |

### Ads & Creatives
*Individual ads, responsive search ads, display ads*

| Resource      | Label | Fields | Notable Fields |
|---------------|-------|--------|----------------|
| `ad_group_ad` | Ad    | 12     | `ad_group_ad.ad.type`, `ad_group_ad.ad.final_urls`, `ad_group_ad.ad.responsive_search_ad.headlines`, `ad_group_ad.policy_summary.approval_status` |

### Performance & Reports
*Search terms, geographic performance, audience insights*

| Resource           | Label             | Fields | Notable Fields |
|--------------------|-------------------|--------|----------------|
| `search_term_view` | Search Term View  | 7      | `search_term_view.search_term`, `search_term_view.status`, `metrics.clicks`, `segments.date` |
| `geographic_view`  | Geographic View   | 7      | `geographic_view.location_type`, `geographic_view.country_criterion_id`, `metrics.conversions` |

### Account
*Customer account info, conversion actions, billing*

| Resource            | Label              | Fields | Notable Fields |
|---------------------|--------------------|--------|----------------|
| `customer`          | Customer (Account) | 10     | `customer.id`, `customer.descriptive_name`, `customer.currency_code`, `customer.manager`, `metrics.cost_micros` |
| `conversion_action` | Conversion Action  | 7      | `conversion_action.type`, `conversion_action.counting_type`, `conversion_action.value_settings.default_value` |

---

## 8. GAQL Query Examples

Each resource in the demo data includes a `gaql_example`. Here are the patterns:

| Resource             | Example GAQL |
|----------------------|--------------|
| `campaign`           | `SELECT campaign.id, campaign.name, campaign.status, metrics.clicks, metrics.impressions, metrics.cost_micros FROM campaign WHERE campaign.status = 'ENABLED'` |
| `campaign_budget`    | `SELECT campaign_budget.id, campaign_budget.name, campaign_budget.amount_micros FROM campaign_budget` |
| `ad_group`           | `SELECT ad_group.id, ad_group.name, ad_group.status, metrics.clicks, metrics.cost_micros FROM ad_group WHERE campaign.status = 'ENABLED'` |
| `ad_group_criterion` | `SELECT ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, metrics.clicks, metrics.impressions FROM ad_group_criterion WHERE ad_group_criterion.type = 'KEYWORD'` |
| `ad_group_ad`        | `SELECT ad_group_ad.ad.id, ad_group_ad.ad.type, ad_group_ad.status, metrics.clicks, metrics.impressions, metrics.ctr FROM ad_group_ad WHERE ad_group_ad.status != 'REMOVED'` |
| `search_term_view`   | `SELECT search_term_view.search_term, metrics.clicks, metrics.impressions, metrics.conversions FROM search_term_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.clicks DESC LIMIT 100` |
| `geographic_view`    | `SELECT geographic_view.country_criterion_id, metrics.clicks, metrics.conversions FROM geographic_view ORDER BY metrics.clicks DESC` |
| `customer`           | `SELECT customer.id, customer.descriptive_name, customer.currency_code, metrics.clicks, metrics.cost_micros FROM customer` |
| `conversion_action`  | `SELECT conversion_action.id, conversion_action.name, conversion_action.type, conversion_action.status FROM conversion_action WHERE conversion_action.status = 'ENABLED'` |

**GAQL syntax rules:**
- Field names use **dot notation**: `resource.field` or `resource.nested.field`
- Metrics always prefixed with `metrics.`
- Segments always prefixed with `segments.`
- Status values are **uppercase strings**: `'ENABLED'`, `'PAUSED'`, `'REMOVED'`
- Date ranges use `DURING` keyword: `WHERE segments.date DURING LAST_30_DAYS`
- Monetary values are in **micros** (divide by 1,000,000 for display)

---

*Generated from backend source: `backend/googleads/service.py` — `test_connection()`, `list_categories()`, `list_resources()`, and `get_resource_fields()`*

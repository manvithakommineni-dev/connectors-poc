# Meta Ads (Facebook + Instagram) API — Response Schema Documentation

This document describes every key-value pair returned by the Meta Ads metadata endpoints exposed by this backend.

**Live-only connector.** There is no demo mode — `META_ACCESS_TOKEN` and `META_AD_ACCOUNT_ID` must be set in `backend/.env` before any endpoint will respond.

Instagram ads are managed through the **same Meta Marketing API**. Use the `publisher_platform` insights breakdown to split performance between Facebook and Instagram.

---

## Background — How Meta Exposes Metadata

Meta uses the **Facebook Graph API** (Marketing API) for all ad object and performance data. Unlike GA4's dedicated metadata endpoint, Meta combines:

1. **Live object reads** — fetch real Campaign, AdSet, and Ad records from your ad account
2. **Static field catalogs** — documented Graph API fields for each object type (maintained in this backend from official v21.0 reference)
3. **Insights API** — performance metrics and breakdown dimensions queried separately

**Key concept mapping:**

| Traditional DB     | Salesforce      | Google Ads           | Meta Ads                         |
|--------------------|-----------------|----------------------|----------------------------------|
| Database / Schema  | Org             | Customer (Account)   | **Ad Account** (`act_{id}`)      |
| Schema / Domain    | —               | Category             | **Category** (campaigns, adsets, etc.) |
| Table              | SObject         | Resource             | **Campaign / AdSet / Ad**        |
| Column / Field     | Field           | Field                | **Graph API field** (`name`, `status`) |
| Row                | Record          | Query result row     | **Live object** from Graph API   |
| Performance data   | —               | Metric               | **Insights metric** (`impressions`, `spend`) |
| Group-by dimension | —               | Segment              | **Insights breakdown** (`publisher_platform`) |

**Authentication:** Long-lived **User Access Token** or **System User token** with `ads_read` scope, passed as `access_token` query parameter on every Graph API call.

---

## Table of Contents

1. [Authentication & Setup](#authentication--setup)
2. [GET /api/v1/metaads/connect](#1-get-apiv1metaadsconnect)
3. [GET /api/v1/metaads/categories](#2-get-apiv1metaadscategories)
4. [GET /api/v1/metaads/items](#3-get-apiv1metaadsitems)
   - [Top-Level Response](#31-top-level-response)
   - [Account Item](#32-account-item-categoryaccount)
   - [Live Object Items](#33-live-object-items-categorycampaigns-adsets-ads)
   - [Field Catalog Items](#34-field-catalog-items)
5. [GET /api/v1/metaads/items/{item_id}](#4-get-apiv1metaadsitemsitem_id)
6. [Campaign Field Reference](#5-campaign-field-reference)
7. [Ad Set Field Reference](#6-ad-set-field-reference)
8. [Ad Field Reference](#7-ad-field-reference)
9. [Insights Metrics Reference](#8-insights-metrics-reference)
10. [Insights Breakdowns Reference](#9-insights-breakdowns-reference)
11. [Account Status Codes](#10-account-status-codes)
12. [Underlying Graph API](#11-underlying-graph-api)
13. [Meta vs Salesforce Terminology](#12-meta-vs-salesforce-terminology)

---

## Authentication & Setup

| Variable | Description |
|----------|-------------|
| `META_ACCESS_TOKEN` | Long-lived User Access Token or System User token with **`ads_read`** scope |
| `META_AD_ACCOUNT_ID` | Ad account ID — with or without `act_` prefix (e.g. `act_123456789` or `123456789`) |
| `META_API_VERSION` | Graph API version (default: `v21.0`) |

**Setup:**
1. Create a Meta Developer account and Business app with **Marketing API** product
2. Generate an access token with `ads_read` permission (Graph API Explorer or System User in Business Manager)
3. Link the token to your ad account in Business Manager
4. Set env vars in `backend/.env`

---

## Endpoints

| Purpose | URL |
|---------|-----|
| Connect / test | `GET /api/v1/metaads/connect` |
| List categories | `GET /api/v1/metaads/categories` |
| List items by category | `GET /api/v1/metaads/items?category={category_id}` |
| Item detail | `GET /api/v1/metaads/items/{item_id}?category={category_id}` |

**Valid `category_id` values:**

| ID | Type | Source |
|----|------|--------|
| `account` | Live ad account | Graph API |
| `campaigns` | Live campaign list | Graph API |
| `adsets` | Live ad set list | Graph API |
| `ads` | Live ad list | Graph API |
| `campaign_fields` | Field catalog | Static schema |
| `adset_fields` | Field catalog | Static schema |
| `ad_fields` | Field catalog | Static schema |
| `insights_metrics` | Metrics catalog | Static schema |
| `insights_breakdowns` | Breakdown catalog | Static schema |

---

## 1. GET /api/v1/metaads/connect

Tests Meta Marketing API connectivity by fetching ad account info and a sample campaign count from the live Graph API.

**Example Response**

```json
{
  "connected": true,
  "mode": "live",
  "ad_account_id": "123456789",
  "ad_account_name": "My Business Ad Account",
  "account_status": 1,
  "currency": "USD",
  "timezone": "America/Los_Angeles",
  "amount_spent": "1250.50",
  "business_name": "My Business LLC",
  "campaigns_sample": 5,
  "platforms": "Facebook + Instagram (via Marketing API)",
  "auth_method": "Access Token (ads_read)",
  "api_version": "v21.0"
}
```

### Response Fields

| Key | Type | Description |
|-----|------|-------------|
| `connected` | `boolean` | Always `true` when this response is returned. A `401` HTTP error is raised if the access token is invalid or expired. |
| `mode` | `string` | Always `"live"`. Meta Ads has no demo mode in this connector. |
| `ad_account_id` | `string` | The numeric ad account ID (without `act_` prefix). Sourced from `account_id` or `id` in the Graph API ad account response. |
| `ad_account_name` | `string` | The display name of the ad account as set in Meta Business Manager (e.g. `"My Business Ad Account"`). |
| `account_status` | `integer` | Numeric account status code from Meta. `1` = ACTIVE. See [Account Status Codes](#10-account-status-codes). |
| `currency` | `string` | ISO 4217 currency code for the ad account (e.g. `"USD"`, `"EUR"`, `"INR"`). All budget and spend values use this currency. |
| `timezone` | `string` | IANA timezone for the ad account (e.g. `"America/Los_Angeles"`). Report date boundaries use this timezone. |
| `amount_spent` | `string` | Total lifetime amount spent on this ad account, as a decimal string in account currency (e.g. `"1250.50"`). |
| `business_name` | `string` | The business name associated with this ad account in Business Manager. May be empty for personal ad accounts. |
| `campaigns_sample` | `integer \| string` | Count of campaigns returned in a probe query (`limit=1`). Returns `"1+"` if pagination indicates more campaigns exist beyond the first page. |
| `platforms` | `string` | Fixed label indicating supported platforms. Always `"Facebook + Instagram (via Marketing API)"`. |
| `auth_method` | `string` | Fixed label describing authentication. Always `"Access Token (ads_read)"`. |
| `api_version` | `string` | The Graph API version in use (from `META_API_VERSION`, default `"v21.0"`). |

---

## 2. GET /api/v1/metaads/categories

Lists all nine metadata categories with live item counts. Counts for `campaigns`, `adsets`, and `ads` are fetched from the Graph API; field catalog counts come from static schema definitions.

> **Note:** This endpoint returns a **raw JSON array** (not wrapped in `{total, categories}`).

**Example Response**

```json
[
  {
    "id": "account",
    "label": "Ad Account",
    "description": "Live ad account details from Graph API",
    "items_count": 1
  },
  {
    "id": "campaigns",
    "label": "Campaigns",
    "description": "Live campaigns in the ad account",
    "items_count": 12
  },
  {
    "id": "campaign_fields",
    "label": "Campaign Fields",
    "description": "Queryable fields on Campaign object",
    "items_count": 17
  }
]
```

### Each Category Entry

| Key | Type | Description |
|-----|------|-------------|
| `id` | `string` | Category identifier used as the `category` query parameter in `/items` and `/items/{id}` endpoints. |
| `label` | `string` | Human-readable display name (e.g. `"Campaigns"`, `"Insights Metrics"`, `"Insights Breakdowns"`). |
| `description` | `string` | Brief explanation of what this category contains and whether data is live or catalog-based. |
| `items_count` | `integer \| string` | Count of items in this category. For live lists (`campaigns`, `adsets`, `ads`), fetched from Graph API (max 100 per request). Returns `"100+"` when pagination indicates more items exist. For field catalogs, this is the static field count. |

---

## 3. GET /api/v1/metaads/items

Returns all items for a given category. The item shape depends on the category type — live objects, field catalog entries, or the single ad account record.

**Query Parameter**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | `string` | Yes | One of the nine category IDs listed above. |

**Example Response (field catalog — `campaign_fields`)**

```json
{
  "category": "campaign_fields",
  "total": 17,
  "mode": "live",
  "items": [
    {
      "name": "id",
      "label": "Campaign ID",
      "description": "Unique campaign identifier",
      "data_type": "string"
    },
    {
      "name": "objective",
      "label": "Objective",
      "description": "OUTCOME_LEADS, OUTCOME_SALES, OUTCOME_TRAFFIC, etc.",
      "data_type": "enum"
    }
  ]
}
```

**Example Response (live campaigns)**

```json
{
  "category": "campaigns",
  "total": 3,
  "mode": "live",
  "items": [
    {
      "name": "23851234567890123",
      "label": "Summer Sale 2024",
      "description": "status=ACTIVE · effective=ACTIVE · objective=OUTCOME_SALES",
      "raw": {
        "id": "23851234567890123",
        "name": "Summer Sale 2024",
        "status": "ACTIVE",
        "effective_status": "ACTIVE",
        "objective": "OUTCOME_SALES",
        "daily_budget": "5000",
        "created_time": "2024-06-01T10:00:00+0000"
      }
    }
  ]
}
```

---

### 3.1 Top-Level Response

| Key | Type | Description |
|-----|------|-------------|
| `category` | `string` | Echoes back the `category` query parameter. |
| `total` | `integer` | Total count of items returned for this category. |
| `mode` | `string` | Always `"live"`. |
| `items` | `array<object>` | List of item descriptors. Shape varies by category — see sections below. |

---

### 3.2 Account Item (`category=account`)

Returns a single item representing the connected ad account with full Graph API response in `raw`.

| Key | Type | Description |
|-----|------|-------------|
| `name` | `string` | The ad account ID (numeric string). |
| `label` | `string` | The ad account display name. |
| `description` | `string` | Summary string in format `"{currency} · status {account_status}"` (e.g. `"USD · status 1"`). |
| `raw` | `object` | Full Graph API ad account object. Includes: `id`, `account_id`, `name`, `account_status`, `currency`, `timezone_name`, `amount_spent`, `balance`, `business_name`, `created_time`, `age`. |

---

### 3.3 Live Object Items (`category=campaigns`, `adsets`, `ads`)

Each item is a real record fetched from the Graph API for the connected ad account.

| Key | Type | Description |
|-----|------|-------------|
| `name` | `string` | The Meta object ID (e.g. `"23851234567890123"`). Used as `{item_id}` in `/items/{item_id}?category=...` for detail fetch. |
| `label` | `string` | The object name from Graph API (`name` field). Falls back to `id` if name is empty. |
| `description` | `string` | Auto-generated summary. For campaigns: `status=... · effective=... · objective=...`. For ad sets: includes `optimization_goal`. For ads: status fields only. |
| `raw` | `object` | Partial Graph API object with fields from the list query. See fields fetched per type below. |

**Fields fetched in list queries (`raw` object keys):**

| Category | Graph API fields in `raw` |
|----------|---------------------------|
| `campaigns` | `id`, `name`, `status`, `effective_status`, `objective`, `daily_budget`, `lifetime_budget`, `created_time`, `updated_time` |
| `adsets` | `id`, `name`, `status`, `effective_status`, `campaign_id`, `daily_budget`, `optimization_goal`, `created_time` |
| `ads` | `id`, `name`, `status`, `effective_status`, `adset_id`, `campaign_id`, `created_time` |

---

### 3.4 Field Catalog Items

Used for categories: `campaign_fields`, `adset_fields`, `ad_fields`, `insights_metrics`, `insights_breakdowns`.

| Key | Type | Description |
|-----|------|-------------|
| `name` | `string` | The Graph API field or metric name (e.g. `"objective"`, `"impressions"`, `"publisher_platform"`). Used in `fields=` parameter or Insights API requests. |
| `label` | `string` | Human-readable display label (e.g. `"Objective"`, `"Impressions"`, `"Publisher Platform"`). |
| `description` | `string` | Plain-English description including valid enum values where applicable. |
| `data_type` | `string` | Field data type: `"string"`, `"integer"`, `"float"`, `"enum"`, `"datetime"`, `"object"`, `"array"`, or `"breakdown"`. See field reference sections for full lists. |

---

## 4. GET /api/v1/metaads/items/{item_id}

Returns detail for a single item. Response shape depends on category type.

**Path Parameter**

| Parameter | Type | Description |
|-----------|------|-------------|
| `item_id` | `string` | Field name (for catalog categories) or Meta object ID (for live object categories). |

**Query Parameter**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | `string` | Yes | The category this item belongs to. |

---

### Field catalog detail (`campaign_fields`, `adset_fields`, `ad_fields`, `insights_metrics`, `insights_breakdowns`)

**Example:** `GET /api/v1/metaads/items/objective?category=campaign_fields`

```json
{
  "name": "objective",
  "label": "Objective",
  "type": "enum",
  "description": "OUTCOME_LEADS, OUTCOME_SALES, OUTCOME_TRAFFIC, etc.",
  "category": "campaign_fields",
  "mode": "live"
}
```

| Key | Type | Description |
|-----|------|-------------|
| `name` | `string` | Field/metric/breakdown name. |
| `label` | `string` | Display label. |
| `type` | `string` | Data type (`string`, `enum`, `integer`, etc.). Note: key is `type` here (not `data_type` as in list response). |
| `description` | `string` | Field description with valid values where applicable. |
| `category` | `string` | Echoes back the category query parameter. |
| `mode` | `string` | Always `"live"`. |

---

### Live object detail (`campaigns`, `adsets`, `ads`)

**Example:** `GET /api/v1/metaads/items/23851234567890123?category=campaigns`

```json
{
  "name": "23851234567890123",
  "label": "Summer Sale 2024",
  "category": "campaigns",
  "fields": {
    "id": "23851234567890123",
    "name": "Summer Sale 2024",
    "status": "ACTIVE",
    "effective_status": "ACTIVE",
    "objective": "OUTCOME_SALES",
    "daily_budget": "5000",
    "lifetime_budget": "0",
    "created_time": "2024-06-01T10:00:00+0000",
    "updated_time": "2024-06-15T14:30:00+0000"
  },
  "mode": "live"
}
```

| Key | Type | Description |
|-----|------|-------------|
| `name` | `string` | Meta object ID. |
| `label` | `string` | Object display name. |
| `category` | `string` | Echoes back the category (`campaigns`, `adsets`, or `ads`). |
| `fields` | `object` | Full Graph API object fetched directly by ID with the same field set as the list query. |
| `mode` | `string` | Always `"live"`. |

---

### Account detail (`category=account`)

Returns the same single account item as `/items?category=account` with `category` and `mode` added. The `raw` object contains the full ad account Graph API response.

Returns `404` if `item_id` is not found in the specified category.

---

## 5. Campaign Field Reference

All 17 queryable fields on the **Campaign** Graph API object (`category=campaign_fields`).

| `name` | `type` | Description |
|--------|--------|-------------|
| `id` | string | Unique campaign identifier |
| `name` | string | Campaign name |
| `status` | enum | `ACTIVE`, `PAUSED`, `DELETED`, `ARCHIVED` |
| `effective_status` | enum | Actual delivery status considering parent account/campaign state |
| `objective` | enum | `OUTCOME_LEADS`, `OUTCOME_SALES`, `OUTCOME_TRAFFIC`, `OUTCOME_AWARENESS`, `OUTCOME_ENGAGEMENT`, `OUTCOME_APP_PROMOTION` |
| `buying_type` | enum | `AUCTION` or `RESERVED` |
| `daily_budget` | integer | Daily budget in account currency **cents** |
| `lifetime_budget` | integer | Lifetime budget in account currency cents |
| `budget_remaining` | integer | Remaining budget |
| `spend_cap` | integer | Campaign spending limit |
| `bid_strategy` | enum | `LOWEST_COST_WITHOUT_CAP`, `COST_CAP`, `LOWEST_COST_WITH_BID_CAP`, etc. |
| `start_time` | datetime | Campaign start time (ISO 8601) |
| `stop_time` | datetime | Campaign stop time |
| `created_time` | datetime | When campaign was created |
| `updated_time` | datetime | Last update timestamp |
| `special_ad_categories` | array | `CREDIT`, `EMPLOYMENT`, `HOUSING`, `ISSUES_ELECTIONS_POLITICS`, etc. |
| `account_id` | string | Parent ad account ID |

> **Budget note:** Meta stores budgets as integers in the **smallest currency unit** (cents for USD). `daily_budget: 5000` = $50.00.

---

## 6. Ad Set Field Reference

All 18 queryable fields on the **AdSet** Graph API object (`category=adset_fields`).

| `name` | `type` | Description |
|--------|--------|-------------|
| `id` | string | Unique ad set identifier |
| `name` | string | Ad set name |
| `status` | enum | `ACTIVE`, `PAUSED`, `DELETED`, `ARCHIVED` |
| `effective_status` | enum | Actual delivery status |
| `campaign_id` | string | Parent campaign ID (foreign key) |
| `daily_budget` | integer | Daily budget in cents |
| `lifetime_budget` | integer | Lifetime budget in cents |
| `billing_event` | enum | `IMPRESSIONS`, `LINK_CLICKS`, `APP_INSTALLS`, etc. |
| `optimization_goal` | enum | `REACH`, `LINK_CLICKS`, `CONVERSIONS`, `VALUE`, `APP_INSTALLS`, etc. |
| `bid_amount` | integer | Bid in account currency |
| `bid_strategy` | enum | Bidding strategy type |
| `targeting` | object | Audience targeting spec — geo locations, age, gender, interests, custom audiences |
| `start_time` | datetime | Ad set start time |
| `end_time` | datetime | Ad set end time |
| `created_time` | datetime | Creation timestamp |
| `updated_time` | datetime | Last update timestamp |
| `destination_type` | enum | `WEBSITE`, `APP`, `MESSENGER`, `INSTAGRAM_DIRECT`, etc. |
| `promoted_object` | object | Pixel ID, page ID, or app ID being promoted for conversion tracking |

---

## 7. Ad Field Reference

All 12 queryable fields on the **Ad** Graph API object (`category=ad_fields`).

| `name` | `type` | Description |
|--------|--------|-------------|
| `id` | string | Unique ad identifier |
| `name` | string | Ad name |
| `status` | enum | `ACTIVE`, `PAUSED`, `DELETED`, `ARCHIVED` |
| `effective_status` | enum | Actual delivery status |
| `adset_id` | string | Parent ad set ID (foreign key) |
| `campaign_id` | string | Parent campaign ID (foreign key) |
| `creative` | object | Ad creative object — image hash, video ID, text, call-to-action |
| `tracking_specs` | array | Conversion tracking configuration (pixel events, app events) |
| `conversion_specs` | array | Conversion event specifications |
| `created_time` | datetime | Creation timestamp |
| `updated_time` | datetime | Last update timestamp |
| `preview_shareable_link` | string | Shareable URL to preview the ad as it appears on Facebook/Instagram |

---

## 8. Insights Metrics Reference

All 19 performance metrics available from the Insights API (`category=insights_metrics`). Request via `GET /act_{id}/insights?fields=impressions,clicks,spend,...`.

| `name` | `type` | Description |
|--------|--------|-------------|
| `impressions` | integer | Times the ad was on screen |
| `clicks` | integer | Total clicks on the ad (all click types) |
| `spend` | float | Amount spent in account currency |
| `reach` | integer | Unique people who saw the ad |
| `frequency` | float | Average impressions per person (`impressions / reach`) |
| `cpm` | float | Cost per 1,000 impressions |
| `cpc` | float | Cost per click |
| `ctr` | float | Click-through rate (`clicks / impressions`) |
| `cpp` | float | Cost per 1,000 people reached |
| `actions` | array | Conversion actions broken down by type (purchase, lead, add_to_cart, etc.) |
| `conversions` | array | Conversion events |
| `cost_per_action_type` | array | Cost broken down by action type |
| `purchase_roas` | array | Return on ad spend for purchase conversions |
| `video_p25_watched_actions` | array | Video views at 25% completion |
| `video_p50_watched_actions` | array | Video views at 50% completion |
| `inline_link_clicks` | integer | Clicks specifically on links in the ad |
| `inline_link_click_ctr` | float | Link click-through rate |
| `unique_clicks` | integer | Unique people who clicked |
| `unique_ctr` | float | Unique click-through rate |

---

## 9. Insights Breakdowns Reference

All 9 segmentation dimensions for the Insights API (`category=insights_breakdowns`). Pass as `breakdowns=` parameter to split metrics.

| `name` | Description | Example Values |
|--------|-------------|----------------|
| `publisher_platform` | Platform where ad was shown | `facebook`, `instagram`, `audience_network`, `messenger` |
| `platform_position` | Placement within platform | `feed`, `story`, `reels`, `search`, `instant_article` |
| `age` | Age bracket of audience | `18-24`, `25-34`, `35-44`, `45-54`, `55-64`, `65+` |
| `gender` | Gender of audience | `male`, `female`, `unknown` |
| `country` | Country code | `US`, `IN`, `GB`, etc. |
| `region` | Region or state | State/province codes |
| `device_platform` | Device category | `mobile`, `desktop` |
| `impression_device` | Specific device type | `android_smartphone`, `iphone`, `ipad`, `desktop` |
| `product_id` | Product in catalog/dynamic ad | Catalog product SKU |

**Example Insights query (Facebook vs Instagram split):**

```
GET /act_{id}/insights
  ?fields=impressions,clicks,spend,reach
  &breakdowns=publisher_platform
  &date_preset=last_30d
```

---

## 10. Account Status Codes

The `account_status` field on `/connect` and in the account `raw` object uses these Meta-defined codes:

| Code | Status | Description |
|------|--------|-------------|
| `1` | ACTIVE | Account is active and can deliver ads |
| `2` | DISABLED | Account is disabled |
| `3` | UNSETTLED | Account has unsettled balance |
| `7` | PENDING_RISK_REVIEW | Account is pending risk review |
| `8` | PENDING_SETTLEMENT | Account is pending settlement |
| `9` | IN_GRACE_PERIOD | Account is in grace period |
| `100` | PENDING_CLOSURE | Account is pending closure |
| `101` | CLOSED | Account is closed |
| `201` | ANY_ACTIVE | Any active status (used in filters) |
| `202` | ANY_CLOSED | Any closed status (used in filters) |

---

## 11. Underlying Graph API

| Resource | Graph API Endpoint | Purpose |
|----------|-------------------|---------|
| Ad Account | `GET /v21.0/act_{id}?fields=...` | Account info, currency, spend |
| Campaigns | `GET /v21.0/act_{id}/campaigns?fields=...` | List campaigns |
| Ad Sets | `GET /v21.0/act_{id}/adsets?fields=...` | List ad sets |
| Ads | `GET /v21.0/act_{id}/ads?fields=...` | List ads |
| Campaign by ID | `GET /v21.0/{campaign_id}?fields=...` | Single campaign detail |
| Insights | `GET /v21.0/act_{id}/insights?fields=...&breakdowns=...` | Performance metrics |

**Base URL:** `https://graph.facebook.com`

**Official docs:** https://developers.facebook.com/docs/marketing-api

**Meta ad hierarchy:**

```
Ad Account (act_{id})
  └── Campaign
        └── Ad Set (targeting + budget)
              └── Ad (creative)
                    └── Insights (metrics per ad/campaign/account)
```

---

## 12. Meta vs Salesforce Terminology

| Concept | Salesforce | Meta Ads |
|---------|------------|----------|
| Whole instance | Org | Ad Account (`act_{id}`) |
| Table / entity | SObject | Campaign / AdSet / Ad |
| Column / field | Field (`FirstName`) | Graph API field (`name`, `status`, `objective`) |
| Schema discovery | Describe API | Field catalog + live object fetch |
| Data row | Record | Live Campaign / AdSet / Ad from Graph API |
| Performance metric | N/A | Insights metric (`impressions`, `spend`, `ctr`) |
| Group-by dimension | N/A | Insights breakdown (`publisher_platform`, `age`) |
| Foreign key | Relationship (lookup) | `campaign_id`, `adset_id` on child objects |
| Status field | Picklist | Enum (`ACTIVE`, `PAUSED`, `DELETED`, `ARCHIVED`) |
| Currency amounts | Decimal field | Integer in cents (`daily_budget: 5000` = $50.00) |
| Instagram data | N/A | Same API — use `publisher_platform` breakdown |

---

*Generated from backend source: `backend/metaads/service.py` — `test_connection()`, `list_categories()`, `list_items()`, and `get_item_detail()`*

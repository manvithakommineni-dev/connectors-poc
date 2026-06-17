# Google Analytics 4 (GA4) API — Response Schema Documentation

This document describes every key-value pair returned by the GA4 metadata endpoints exposed by this backend.

**Live-only connector.** There is no demo mode — `GA4_PROPERTY_ID` and `GA4_SERVICE_ACCOUNT_FILE` must be set in `backend/.env` before any endpoint will respond.

---

## Background — How GA4 Exposes Metadata

GA4 uses two Google APIs for metadata retrieval:

| API | Base URL | Purpose |
|-----|----------|---------|
| **Google Analytics Data API** | `https://analyticsdata.googleapis.com/v1beta` | Dimensions and metrics catalog (`/properties/{id}/metadata`) |
| **Google Analytics Admin API** | `https://analyticsadmin.googleapis.com/v1beta` | Property info, custom dimensions/metrics, data streams |

**Key concept mapping:**

| Traditional DB     | Salesforce      | Google Ads           | GA4                              |
|--------------------|-----------------|----------------------|----------------------------------|
| Database / Schema  | Org             | Customer (Account)   | **Property**                     |
| Schema / Domain    | —               | Category             | **Category** (dimensions, metrics, etc.) |
| Table              | SObject         | Resource             | **Dimension / Metric / Data Stream** |
| Column / Field     | Field           | Field (`resource.field`) | **apiName** (`country`, `activeUsers`) |
| Row                | Record          | Query result row     | **Report row** from `runReport`  |
| Describe API       | `describe()`    | `GoogleAdsFieldService` | **Metadata API** `getMetadata` |

**Authentication:** Google Cloud **Service Account** with a JSON key file.
- Scope: `https://www.googleapis.com/auth/analytics.readonly`
- The service account email must be added to GA4 → Admin → Property Access Management with **Viewer** role.

---

## Table of Contents

1. [Authentication & Setup](#authentication--setup)
2. [GET /api/v1/ga4/connect](#1-get-apiv1ga4connect)
3. [GET /api/v1/ga4/categories](#2-get-apiv1ga4categories)
4. [GET /api/v1/ga4/items](#3-get-apiv1ga4items)
   - [Top-Level Response](#31-top-level-response)
   - [Dimension Items](#32-dimension-item-fields-categorydimensions)
   - [Metric Items](#33-metric-item-fields-categorymetrics)
   - [Custom Dimension Items](#34-custom-dimension-item-fields-categorycustom_dimensions)
   - [Custom Metric Items](#35-custom-metric-item-fields-categorycustom_metrics)
   - [Data Stream Items](#36-data-stream-item-fields-categorydata_streams)
5. [GET /api/v1/ga4/items/{item_name}](#4-get-apiv1ga4itemsitem_name)
6. [Metric Type Reference](#5-metric-type-reference)
7. [Dimension Category Reference](#6-dimension-category-reference)
8. [Underlying Google APIs](#7-underlying-google-apis)
9. [GA4 vs Salesforce Terminology](#8-ga4-vs-salesforce-terminology)

---

## Authentication & Setup

| Variable | Description |
|----------|-------------|
| `GA4_PROPERTY_ID` | Numeric GA4 property ID (GA4 → Admin → Property Settings). With or without `properties/` prefix. |
| `GA4_SERVICE_ACCOUNT_FILE` | Absolute path to the Google Cloud service account JSON key file. |

**Setup (FREE):**
1. Create a GA4 property at https://analytics.google.com
2. Google Cloud Console → enable **Google Analytics Data API** + **Google Analytics Admin API**
3. Create a service account → download JSON key
4. GA4 → Admin → Property Access Management → add service account email as **Viewer**

---

## Endpoints

| Purpose | URL |
|---------|-----|
| Connect / test | `GET /api/v1/ga4/connect` |
| List categories | `GET /api/v1/ga4/categories` |
| List items by category | `GET /api/v1/ga4/items?category={category_id}` |
| Item detail | `GET /api/v1/ga4/items/{item_name}?category={category_id}` |

**Valid `category_id` values:** `dimensions`, `metrics`, `custom_dimensions`, `custom_metrics`, `data_streams`

---

## 1. GET /api/v1/ga4/connect

Tests GA4 connectivity by fetching property info from the Admin API and dimension/metric counts from the Data API Metadata endpoint.

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

### Response Fields

| Key | Type | Description |
|-----|------|-------------|
| `connected` | `boolean` | Always `true` when this response is returned. A `401` HTTP error is raised instead if the service account credentials are invalid or the JSON key file is missing. |
| `mode` | `string` | Always `"live"`. GA4 has no demo mode in this connector. |
| `property_id` | `string` | The numeric GA4 property ID (e.g. `"123456789"`). Stripped of the `properties/` prefix. This is the property whose metadata is returned by all other endpoints. |
| `property_name` | `string` | The human-readable display name of the GA4 property as set in Admin (e.g. `"My Website"`). Sourced from `displayName` in the Admin API. |
| `time_zone` | `string` | The IANA timezone configured for this property (e.g. `"Asia/Calcutta"`, `"America/New_York"`). Report date boundaries are interpreted in this timezone. |
| `currency_code` | `string` | The ISO 4217 currency code for the property (e.g. `"INR"`, `"USD"`, `"EUR"`). Used as the default for revenue metrics. |
| `industry_category` | `string` | The industry category assigned to the property in GA4 Admin (e.g. `"TECHNOLOGY"`, `"RETAIL"`, `"FINANCE"`). Sourced from `industryCategory` in the Admin API. |
| `service_level` | `string` | The GA4 service tier for this property (e.g. `"GOOGLE_ANALYTICS_STANDARD"`, `"GOOGLE_ANALYTICS_360"`). Indicates whether this is a free Standard property or an enterprise 360 property. |
| `dimensions_count` | `integer` | Total number of queryable dimensions returned by the Data API Metadata endpoint for this property. Typically 200–400+ depending on enabled features. |
| `metrics_count` | `integer` | Total number of queryable metrics returned by the Data API Metadata endpoint. Typically 80–150+. |
| `auth_method` | `string` | A fixed descriptive label indicating how the backend authenticates. Always `"Service Account (Google Cloud JSON key)"`. |

---

## 2. GET /api/v1/ga4/categories

Lists the five metadata categories available for this GA4 property, with live item counts fetched from the Data API and Admin API.

> **Note:** This endpoint returns a **raw JSON array** (not wrapped in `{total, categories}`).

**Example Response**

```json
[
  {
    "id": "dimensions",
    "label": "Dimensions",
    "description": "Attributes that describe user sessions and events (country, device, page, event name)",
    "items_count": 320
  },
  {
    "id": "metrics",
    "label": "Metrics",
    "description": "Quantitative measurements (activeUsers, sessions, conversions, revenue)",
    "items_count": 85
  },
  {
    "id": "custom_dimensions",
    "label": "Custom Dimensions",
    "description": "User-defined dimensions configured in GA4 Admin",
    "items_count": 5
  },
  {
    "id": "custom_metrics",
    "label": "Custom Metrics",
    "description": "User-defined metrics configured in GA4 Admin",
    "items_count": 2
  },
  {
    "id": "data_streams",
    "label": "Data Streams",
    "description": "Web, iOS, and Android data collection streams for this property",
    "items_count": 3
  }
]
```

### Each Category Entry

| Key | Type | Description |
|-----|------|-------------|
| `id` | `string` | The **category identifier** used as the `category` query parameter in `/items?category={id}` and `/items/{name}?category={id}` (e.g. `"dimensions"`, `"metrics"`, `"custom_dimensions"`, `"custom_metrics"`, `"data_streams"`). |
| `label` | `string` | The human-readable display name for this category (e.g. `"Dimensions"`, `"Custom Metrics"`, `"Data Streams"`). |
| `description` | `string` | Brief explanation of what metadata items this category contains and where they come from in GA4. |
| `items_count` | `integer` | Live count of items in this category for the connected property. Fetched dynamically from the Data API (dimensions/metrics) or Admin API (custom definitions, data streams). |

---

## 3. GET /api/v1/ga4/items

Returns all metadata items for a given category — dimensions, metrics, custom definitions, or data streams — fetched live from Google APIs.

**Query Parameter**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | `string` | Yes | One of: `dimensions`, `metrics`, `custom_dimensions`, `custom_metrics`, `data_streams`. |

**Example Response (dimensions)**

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

---

### 3.1 Top-Level Response

| Key | Type | Description |
|-----|------|-------------|
| `category` | `string` | Echoes back the `category` query parameter. Confirms which category's items are in the response. |
| `total` | `integer` | Total count of items returned for this category. |
| `mode` | `string` | Always `"live"`. |
| `items` | `array<object>` | List of item descriptors. The shape of each item depends on the category — see sections [3.2](#32-dimension-item-fields-categorydimensions) through [3.6](#36-data-stream-item-fields-categorydata_streams). |

---

### 3.2 Dimension Item Fields (`category=dimensions`)

Sourced from `GET /v1beta/properties/{id}/metadata` → `dimensions[]`.

| Key | Type | Description |
|-----|------|-------------|
| `name` | `string` | The **API name** used in GA4 Data API `runReport` requests (e.g. `"country"`, `"deviceCategory"`, `"pagePath"`, `"eventName"`). Pass this value in the `dimensions` array of a report query. |
| `label` | `string` | The **human-readable UI name** for this dimension as shown in GA4 reports (e.g. `"Country"`, `"Device category"`, `"Page path"`). Sourced from `uiName` in the Metadata API. |
| `description` | `string` | A plain-English explanation of what this dimension represents (e.g. `"The country from which the user activity originated."`). |
| `category` | `string` | The **dimension grouping** assigned by Google (e.g. `"GEO"`, `"TIME"`, `"USER"`, `"TRAFFIC_SOURCE"`, `"CONTENT"`, `"EVENT"`, `"PLATFORM"`). See [Section 6](#6-dimension-category-reference). |
| `custom_definition` | `boolean` | Whether this dimension was **created by the property owner** in GA4 Admin (`true`) vs. being a built-in Google dimension (`false`). |
| `deprecated` | `boolean` | Whether this dimension has **deprecated API names** that should no longer be used. `true` if `deprecatedApiNames` is non-empty in the Metadata API response. |

---

### 3.3 Metric Item Fields (`category=metrics`)

Sourced from `GET /v1beta/properties/{id}/metadata` → `metrics[]`.

| Key | Type | Description |
|-----|------|-------------|
| `name` | `string` | The **API name** used in GA4 Data API `runReport` requests (e.g. `"activeUsers"`, `"sessions"`, `"conversions"`, `"totalRevenue"`). Pass this value in the `metrics` array of a report query. |
| `label` | `string` | The **human-readable UI name** for this metric (e.g. `"Active users"`, `"Sessions"`, `"Conversions"`). Sourced from `uiName`. |
| `description` | `string` | Plain-English explanation of what this metric measures. |
| `type` | `string` | The **data type** of the metric value. See [Metric Type Reference](#5-metric-type-reference) (e.g. `"TYPE_INTEGER"`, `"TYPE_FLOAT"`, `"TYPE_SECONDS"`, `"TYPE_CURRENCY"`). |
| `expression` | `string` | For **calculated metrics**, the formula expression (e.g. `"eventCount / sessions"`). Empty string for standard metrics that are not derived from a formula. |
| `custom_definition` | `boolean` | Whether this metric was created by the property owner in GA4 Admin (`true`) vs. being a built-in Google metric (`false`). |
| `deprecated` | `boolean` | Whether this metric has deprecated API names. `true` if `deprecatedApiNames` is non-empty in the Metadata API response. |

---

### 3.4 Custom Dimension Item Fields (`category=custom_dimensions`)

Sourced from `GET /v1beta/properties/{id}/customDimensions` → `customDimensions[]`.

| Key | Type | Description |
|-----|------|-------------|
| `name` | `string` | The **parameter name** of the custom dimension — the key used when sending event parameters from your website/app (e.g. `"user_type"`, `"subscription_plan"`). Sourced from `parameterName`. |
| `label` | `string` | The **display name** configured in GA4 Admin (e.g. `"User Type"`, `"Subscription Plan"`). Sourced from `displayName`. |
| `description` | `string` | Optional description set when the custom dimension was created in GA4 Admin. |
| `scope` | `string` | The **scope** of the custom dimension: `"EVENT"` (applies to a single event), `"USER"` (applies across all events for a user), or `"ITEM"` (applies to e-commerce item events). Determines how the dimension is joined to report data. |
| `disallow_ads_personalization` | `boolean` | Whether this custom dimension is **excluded from ads personalization**. When `true`, Google will not use this dimension for remarketing audience building. |
| `resource_name` | `string` | The fully-qualified **Google resource name** for this custom dimension (e.g. `"properties/123456789/customDimensions/1"`). Used in Admin API update/delete operations. |

---

### 3.5 Custom Metric Item Fields (`category=custom_metrics`)

Sourced from `GET /v1beta/properties/{id}/customMetrics` → `customMetrics[]`.

| Key | Type | Description |
|-----|------|-------------|
| `name` | `string` | The **parameter name** of the custom metric — the numeric key sent with events (e.g. `"purchase_value"`, `"scroll_depth"`). Sourced from `parameterName`. |
| `label` | `string` | The **display name** configured in GA4 Admin (e.g. `"Purchase Value"`, `"Scroll Depth"`). Sourced from `displayName`. |
| `description` | `string` | Optional description set when the custom metric was created. |
| `scope` | `string` | The **scope** of the custom metric: `"EVENT"` (per event) or `"ITEM"` (per e-commerce item). |
| `measurement_unit` | `string` | The unit of measurement configured for this metric (e.g. `"STANDARD"`, `"CURRENCY"`, `"FEET"`, `"METERS"`, `"KILOMETERS"`, `"MILES"`, `"MILLISECONDS"`, `"SECONDS"`, `"MINUTES"`, `"HOURS"`). Affects how the value is displayed in GA4 reports. |
| `resource_name` | `string` | The fully-qualified Google resource name (e.g. `"properties/123456789/customMetrics/1"`). Used in Admin API update/delete operations. |

---

### 3.6 Data Stream Item Fields (`category=data_streams`)

Sourced from `GET /v1beta/properties/{id}/dataStreams` → `dataStreams[]`.

| Key | Type | Description |
|-----|------|-------------|
| `name` | `string` | The **stream ID** — the last segment of the Google resource name (e.g. `"1234567890"`). Used as a short identifier in this API. |
| `label` | `string` | The **display name** of the data stream as configured in GA4 Admin (e.g. `"My Website"`, `"iOS App"`, `"Android App"`). Sourced from `displayName`. |
| `description` | `string` | Auto-generated description in the format `"{type} data stream"` (e.g. `"WEB_DATA_STREAM data stream"`, `"IOS_APP_DATA_STREAM data stream"`). |
| `type` | `string` | The **stream type**: `"WEB_DATA_STREAM"` (website via gtag.js / GTM), `"IOS_APP_DATA_STREAM"` (iOS via Firebase SDK), or `"ANDROID_APP_DATA_STREAM"` (Android via Firebase SDK). |
| `stream_id` | `string` | Same as `name` — the numeric stream ID extracted from the resource name. |
| `measurement_id` | `string` | For **web streams only**: the GA4 Measurement ID used in the gtag.js snippet (e.g. `"G-XXXXXXXXXX"`). Empty for app streams. Sourced from `webStreamData.measurementId`. |
| `default_uri` | `string` | For **web streams only**: the default website URL configured for this stream (e.g. `"https://www.example.com"`). Empty for app streams. Sourced from `webStreamData.defaultUri`. |
| `firebase_app_id` | `string` | For **iOS/Android app streams only**: the Firebase App ID linked to this stream. Empty for web streams. Sourced from `androidAppStreamData.firebaseAppId` or `iosAppStreamData.firebaseAppId`. |
| `resource_name` | `string` | The fully-qualified Google resource name (e.g. `"properties/123456789/dataStreams/1234567890"`). Used in Admin API operations. |

---

## 4. GET /api/v1/ga4/items/{item_name}

Returns the full metadata for a **single item** within a category. The backend looks up the item by `name` from the category list and returns the matching entry with `category` and `mode` added.

**Path Parameter**

| Parameter | Type | Description |
|-----------|------|-------------|
| `item_name` | `string` | The `name` field of the item (e.g. `country`, `activeUsers`, `user_type`). Must match exactly. |

**Query Parameter**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | `string` | Yes | The category the item belongs to (e.g. `dimensions`, `metrics`, `custom_dimensions`). |

**Example Request**

```
GET /api/v1/ga4/items/country?category=dimensions
```

**Example Response**

```json
{
  "name": "country",
  "label": "Country",
  "description": "The country from which the user activity originated.",
  "category": "dimensions",
  "custom_definition": false,
  "deprecated": false,
  "mode": "live"
}
```

### Response Fields

The response contains **all fields for the item type** (same as the matching entry in `/items?category=...`) plus two additional top-level fields:

| Key | Type | Description |
|-----|------|-------------|
| `category` | `string` | Echoes back the `category` query parameter (the metadata category this item belongs to). Note: for dimension items, this is the same key name as the dimension's GA4 grouping (`"GEO"`, `"TIME"`, etc.) — the query parameter category and the dimension grouping are distinct concepts sharing the same key name in the detail response. |
| `mode` | `string` | Always `"live"`. |

All other fields match the item schema for the given category — see [Section 3.2](#32-dimension-item-fields-categorydimensions) through [3.6](#36-data-stream-item-fields-categorydata_streams).

Returns `404` if `item_name` is not found in the specified category.

---

## 5. Metric Type Reference

The `type` field on metric items comes from the GA4 Metadata API `type` attribute.

| `type` | Description |
|--------|-------------|
| `TYPE_INTEGER` | A whole number. Used for counts: `activeUsers`, `sessions`, `eventCount`, `newUsers`, `conversions`. |
| `TYPE_FLOAT` | A floating-point decimal. Used for rates and ratios: `bounceRate`, `engagementRate`, `averageSessionDuration` (when expressed as a ratio). |
| `TYPE_SECONDS` | A duration in seconds. Used for time-based metrics: `averageSessionDuration`, `userEngagementDuration`. Displayed as `HH:MM:SS` in GA4 UI. |
| `TYPE_MILLISECONDS` | A duration in milliseconds. Used for fine-grained timing metrics. |
| `TYPE_MINUTES` | A duration in minutes. |
| `TYPE_HOURS` | A duration in hours. |
| `TYPE_CURRENCY` | A monetary value in the property's `currency_code`. Used for: `totalRevenue`, `purchaseRevenue`, `averagePurchaseRevenue`. |
| `TYPE_FEET` | A distance in feet. |
| `TYPE_MILES` | A distance in miles. |
| `TYPE_METERS` | A distance in meters. |
| `TYPE_KILOMETERS` | A distance in kilometers. |

---

## 6. Dimension Category Reference

The `category` field on dimension items groups dimensions by their analytical domain.

| `category` | Description | Example Dimensions |
|------------|-------------|-------------------|
| `GEO` | Geographic location | `country`, `city`, `region`, `continent` |
| `TIME` | Date and time | `date`, `year`, `month`, `hour`, `dayOfWeek` |
| `USER` | User attributes | `newVsReturning`, `userAgeBracket`, `userGender` |
| `TRAFFIC_SOURCE` | Acquisition source | `sessionSource`, `sessionMedium`, `sessionCampaignName`, `firstUserSource` |
| `CONTENT` | Page and screen content | `pagePath`, `pageTitle`, `landingPage`, `hostName` |
| `EVENT` | Event parameters | `eventName`, `isConversionEvent`, `eventValue` |
| `PLATFORM` | Device and platform | `deviceCategory`, `operatingSystem`, `browser`, `platform` |
| `ECOMMERCE` | E-commerce data | `itemName`, `itemCategory`, `transactionId` |
| `PUBLISHER` | Ad publisher data | `adFormat`, `adSourceName` |
| `COHORT` | Cohort analysis | `cohort`, `cohortNthDay`, `cohortNthWeek` |
| `OTHER` | Miscellaneous | Dimensions not in the above groups |

---

## 7. Underlying Google APIs

| API | Endpoint | Purpose |
|-----|----------|---------|
| Data API | `GET /v1beta/properties/{id}/metadata` | Full dimensions + metrics catalog for the property |
| Admin API | `GET /v1beta/properties/{id}` | Property info (name, timezone, currency, industry) |
| Admin API | `GET /v1beta/properties/{id}/customDimensions` | User-defined custom dimensions |
| Admin API | `GET /v1beta/properties/{id}/customMetrics` | User-defined custom metrics |
| Admin API | `GET /v1beta/properties/{id}/dataStreams` | Web, iOS, and Android data collection streams |

**Official docs:** https://developers.google.com/analytics/devguides/reporting/data/v1

**Example `runReport` using metadata fields:**

```json
POST /v1beta/properties/123456789:runReport
{
  "dimensions": [{ "name": "country" }, { "name": "deviceCategory" }],
  "metrics": [{ "name": "activeUsers" }, { "name": "sessions" }],
  "dateRanges": [{ "startDate": "2024-01-01", "endDate": "2024-01-31" }]
}
```

---

## 8. GA4 vs Salesforce Terminology

| Concept | Salesforce | GA4 |
|---------|------------|-----|
| Whole instance | Org | Property |
| Table / entity | SObject | Dimension / Metric / Data Stream |
| Column / field | Field (`FirstName`) | apiName (`country`, `activeUsers`) |
| Schema discovery | Describe API | Metadata API `getMetadata` |
| Data row | Record | Report row from `runReport` |
| Custom field | Custom Field (`__c`) | Custom Dimension / Custom Metric |
| Foreign key | Relationship (lookup) | N/A — dimensions are flat attributes |
| Performance number | N/A | Metric (`metrics.*`) |
| Group-by dimension | N/A | Dimension used in `dimensions[]` array |
| Status values | Picklist | Dimension values (e.g. `newVsReturning`: `new`, `returning`) |

---

*Generated from backend source: `backend/ga4/service.py` — `test_connection()`, `list_categories()`, `list_items()`, and `get_item_detail()`*

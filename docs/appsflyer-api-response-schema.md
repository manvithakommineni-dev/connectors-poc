# AppsFlyer API — Documentation (Metadata & Data Retrieval)

**Status:** Documentation only — no POC connector built in this repo.

**Reason:** AppsFlyer free (Zero) plan provides an API token, but **Pull API / Raw Data** (the main source of install, event, and attribution metadata) is a **premium feature** or limited to a **30-day Welcome Package trial**. Meaningful live data also requires a **registered mobile app** with the AppsFlyer SDK sending events. Unlike Salesforce, a free signup alone does not yield full metadata access.

**When to build a live connector:** Ontio has a paid AppsFlyer plan (Growth/Enterprise) with Pull API enabled, or you complete signup + mobile app + active API trial.

---

## Table of Contents

1. [Overview](#1-overview)
2. [How AppsFlyer exposes data](#2-how-appsflyer-exposes-data)
3. [Authentication](#3-authentication)
4. [API categories](#4-api-categories)
5. [Pull API — Raw data reports (primary for metadata)](#5-pull-api--raw-data-reports-primary-for-metadata)
6. [App List API](#6-app-list-api)
7. [Push API](#7-push-api)
8. [Master API & aggregated reports](#8-master-api--aggregated-reports)
9. [Report field reference](#9-report-field-reference)
10. [AppsFlyer vs Salesforce terminology](#10-appsflyer-vs-salesforce-terminology)
11. [Free vs paid access](#11-free-vs-paid-access)
12. [Setup guide (when you have API access)](#12-setup-guide-when-you-have-api-access)
13. [Official documentation links](#13-official-documentation-links)

---

## 1. Overview

AppsFlyer is a **mobile attribution and marketing analytics** platform. It tracks:

- App installs (organic vs non-organic)
- In-app events (signup, purchase, trial, etc.)
- Campaign / media source attribution (Meta, Google, TikTok, etc.)
- SKAdNetwork (iOS privacy) postbacks
- Revenue and ROI (with add-ons)

**Platform focus:** iOS and Android apps (not web-only like GA4). Web-to-app is supported via OneLink but core data is mobile.

---

## 2. How AppsFlyer exposes data

| Method | Purpose | Metadata use |
|--------|---------|--------------|
| **Pull API (Raw Data)** | Export CSV reports (installs, events, uninstalls, etc.) | **Primary** — column headers = field schema |
| **Push API** | Real-time postbacks to your server | Event payload schema |
| **Master API** | Customizable aggregated queries | Metrics + dimensions |
| **App List API** | List apps in account | App IDs, basic app metadata |
| **Cohort API** | Retention / LTV cohorts | Cohort dimensions |
| **SKAN APIs** | iOS conversion value schemas | CV-to-event mapping |
| **Dashboard UI** | Reports, pivot tables | Manual exploration |

There is **no single “describe table” API** like Salesforce. Metadata is derived from:

1. **Report type definitions** (installs_report, in_app_events_report, etc.)
2. **Column lists** in Pull API CSV exports
3. **Custom in-app event names** configured in the AppsFlyer dashboard

---

## 3. Authentication

### Token types

| Token | Use |
|-------|-----|
| **API token V2** (JWT) | Pull API, Cohort API, App List API, Master API — `Authorization: Bearer {token}` |
| **S2S token** | Server-to-server event posting (incoming data) |
| **OneLink API token** | Premium — deep link generation |

### Where to get API token V2

1. Sign up: https://www.appsflyer.com → **Sign up free**
2. Dashboard → account menu (email dropdown) → **Security center**
3. **Manage your AppsFlyer API tokens** → copy **API token V2**

**Docs:** https://support.appsflyer.com/hc/en-us/articles/360004562377-Managing-AppsFlyer-tokens

### Example auth header

```http
GET /api/raw-data/export/app/{app-id}/installs_report/v5
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Legacy Pull API also accepts `api_token` query parameter (being phased out in favor of Bearer token).

---

## 4. API categories

| Category | Base URL pattern | Plan |
|----------|------------------|------|
| Raw Data Pull API V5 | `https://hq1.appsflyer.com/api/raw-data/export/app/{app-id}/{report}/v5` | Growth+ / 30-day trial |
| App List API | `https://hq1.appsflyer.com/api/app-list/v1/...` | Advertiser accounts |
| Master API | `https://hq.appsflyer.com/export/{app-id}/...` | Growth+ |
| Push API config | Dashboard + postback URLs | Growth+ |
| SKAN CV schema | `https://dev.appsflyer.com/hc/reference/...` | Varies |

**API reference hub:** https://dev.appsflyer.com/hc/reference/api-reference-overview

---

## 5. Pull API — Raw data reports (primary for metadata)

### Endpoint pattern (V5)

```http
GET https://hq1.appsflyer.com/api/raw-data/export/app/{app_id}/{report_type}/v5
    ?from=YYYY-MM-DD
    &to=YYYY-MM-DD
    &maximum_rows=1000000
Authorization: Bearer {API_TOKEN_V2}
```

- **app_id:** iOS = `id1234567890`, Android = `com.company.app`
- Response: **CSV file** (first row = column names = field metadata)

### Common report types

| Report type | Description | Key fields |
|-------------|-------------|------------|
| `installs_report` | Non-organic + organic installs | `Media Source`, `Campaign`, `Install Time`, `Device ID`, `Country Code` |
| `in_app_events_report` | In-app events | `Event Name`, `Event Value`, `Event Time`, `Media Source`, `Campaign` |
| `uninstalls_report` | App uninstalls | `Uninstall Time`, `Media Source`, `Campaign` |
| `organic_installs_report` | Organic installs only | Same as installs, organic filter |
| `organic_in_app_events_report` | Organic events | Event fields |
| `installs-retarget` | Retargeting installs | Retargeting-specific fields |
| `in-app-events-retarget` | Retargeting events | Retargeting events |

**Docs:** https://support.appsflyer.com/hc/en-us/articles/207034346-Pull-APIs-Pulling-AppsFlyer-Reports-by-APIs

### Example request (cURL)

```bash
curl -G "https://hq1.appsflyer.com/api/raw-data/export/app/id1234567890/installs_report/v5" \
  -H "Authorization: Bearer YOUR_API_TOKEN_V2" \
  --data-urlencode "from=2026-01-01" \
  --data-urlencode "to=2026-01-31"
```

### Example CSV columns (installs_report — subset)

| Column | Description |
|--------|-------------|
| `Attributed Touch Type` | click, impression, etc. |
| `Attributed Touch Time` | When touch occurred |
| `Install Time` | Install timestamp |
| `Event Time` | Event timestamp |
| `Event Name` | For event reports |
| `Event Value` | JSON payload of event |
| `Media Source` | facebook, googleadwords_int, organic, etc. |
| `Campaign` | Campaign name |
| `Campaign ID` | Campaign identifier |
| `Adset` | Ad set name |
| `Adset ID` | Ad set ID |
| `Ad` | Ad name |
| `Ad ID` | Ad ID |
| `Country Code` | ISO country |
| `Platform` | ios / android |
| `Device Type` | Device model |
| `AppsFlyer ID` | Unique AppsFlyer user ID |
| `Customer User ID` | Your app's user ID (if set) |
| `Is Retargeting` | true/false |
| `Conversion Type` | install, re-engagement, etc. |

Full field list varies by report type and account features — always use the CSV header row as source of truth.

### Rate limits (Pull API)

- Subject to **Raw Data API policy** (row limits, date range limits, retention windows)
- Growth plan: ~1M rows per export, 90-day retention (typical)
- See: https://support.appsflyer.com/hc/en-us/articles/207034346 (API policy section)

---

## 6. App List API

Returns JSON list of apps in the advertiser account.

```http
GET https://hq1.appsflyer.com/api/app-list/v1/advertisers/apps
Authorization: Bearer {API_TOKEN_V2}
```

### Example response shape

```json
{
  "data": [
    {
      "app_id": "id1234567890",
      "app_name": "My App iOS",
      "platform": "ios",
      "status": "active"
    },
    {
      "app_id": "com.ontio.app",
      "app_name": "My App Android",
      "platform": "android",
      "status": "active"
    }
  ],
  "meta": {
    "total_items": 2
  },
  "links": {
    "self": "...",
    "next": null
  }
}
```

**Limits:** 20 requests/minute, 100 requests/day, 1,000 records per page.

**Docs:** https://dev.appsflyer.com/hc/reference/app-list-ad-nets-overview

---

## 7. Push API

Real-time HTTP postbacks to your server when installs/conversions occur.

- Configured in AppsFlyer dashboard per app
- Payload includes: `media_source`, `campaign`, `event_name`, `event_value`, `appsflyer_id`, etc.
- Used for **streaming data**, not schema discovery

**Docs:** https://support.appsflyer.com/hc/en-us/articles/207034356-Push-APIs

---

## 8. Master API & aggregated reports

Master API allows customizable aggregated queries (group-by dimensions, filters).

```http
GET https://hq.appsflyer.com/export/{app_id}/master_report/v4
    ?api_token={token}
    &from=2026-01-01
    &to=2026-01-31
    &groupings=media_source,campaign
    &kpis=installs,clicks,impressions,cost
```

**Docs:** https://support.appsflyer.com/hc/en-us/articles/213223166-Master-API

---

## 9. Report field reference

### Standard in-app event names (examples)

Configured in AppsFlyer dashboard → **In-app events**. Common events for conversion tracking:

| Event name | Use case |
|------------|----------|
| `af_purchase` | Revenue / paid conversion |
| `af_complete_registration` | Account created |
| `af_tutorial_completion` | Onboarding complete |
| `af_subscribe` | Subscription started |
| `af_start_trial` | Trial started |
| Custom events | `account_created`, `checkout_complete`, etc. |

### Media source values (examples)

| Value | Platform |
|-------|----------|
| `facebook` | Meta Ads |
| `googleadwords_int` | Google Ads |
| `organic` | Organic install |
| `tiktokglobal_int` | TikTok Ads |
| `snapchat_int` | Snapchat |

### SKAdNetwork (iOS)

Separate APIs for conversion value schemas — relevant for iOS 14+ attribution without device ID.

**Docs:** https://dev.appsflyer.com/hc/reference/skan-overview

---

## 10. AppsFlyer vs Salesforce terminology

| Salesforce | AppsFlyer |
|------------|-----------|
| SObject | Report type (installs_report, in_app_events_report) |
| Field / Column | CSV column / event parameter |
| Record | Install row / Event row |
| Describe API | Pull API CSV header + dashboard event config |
| Org | AppsFlyer account |
| Object list | App List API |
| Custom field | Custom in-app event + event parameters |

---

## 11. Free vs paid access

| Feature | Zero (Free) | Growth | Enterprise |
|---------|-------------|--------|------------|
| Sign up | Yes | Yes | Custom |
| API token V2 | Yes | Yes | Yes |
| 12K free conversions | Yes (year 1) | Yes (year 1) | Custom |
| 30-day premium trial | Yes | Yes | N/A |
| **Pull API (Raw Data)** | Trial only / limited | Yes (1M row limit) | Yes (Data Locker) |
| **Push API** | Premium | Yes | Yes |
| App List API | Yes (if apps exist) | Yes | Yes |
| Mobile SDK required | Yes for data | Yes | Yes |

**Pricing:** https://www.appsflyer.com/pricing/

---

## 12. Setup guide (when you have API access)

### Step 1 — Create account
https://www.appsflyer.com → **Sign up free**

### Step 2 — Add mobile app
Dashboard → **Add app** → iOS (`id...`) or Android (`com...`) → integrate SDK

### Step 3 — Configure in-app events
Dashboard → **In-app events** → map events (purchase, registration, etc.)

### Step 4 — Connect ad networks
**Integrated partners** → Meta, Google, TikTok, etc. → enable attribution

### Step 5 — Get API token
Security center → **API token V2**

### Step 6 — Test Pull API
```bash
curl -G "https://hq1.appsflyer.com/api/raw-data/export/app/{APP_ID}/installs_report/v5" \
  -H "Authorization: Bearer {TOKEN}" \
  --data-urlencode "from=2026-06-01" \
  --data-urlencode "to=2026-06-11"
```

### Step 7 — Future POC env vars (not implemented yet)
```env
APPSFLYER_API_TOKEN=
APPSFLYER_APP_ID=id1234567890
```

---

## 13. Official documentation links

| Resource | URL |
|----------|-----|
| Developer hub | https://dev.appsflyer.com/hc/reference/api-reference-overview |
| Pull API | https://support.appsflyer.com/hc/en-us/articles/207034346 |
| API tokens | https://support.appsflyer.com/hc/en-us/articles/360004562377 |
| App List API | https://dev.appsflyer.com/hc/reference/app-list-ad-nets-overview |
| Push API | https://support.appsflyer.com/hc/en-us/articles/207034356 |
| Master API | https://support.appsflyer.com/hc/en-us/articles/213223166 |
| Pricing | https://www.appsflyer.com/pricing/ |
| In-app events | https://support.appsflyer.com/hc/en-us/articles/115005546169 |

---

## Summary for metadata generation POC

To build a metadata catalog for AppsFlyer (similar to Salesforce field lists):

1. **Call App List API** → get app IDs
2. **Call Pull API** for each report type → parse CSV headers as field definitions
3. **Dashboard export** → In-app events list = custom “fields”
4. **Document media sources** → dimension values for attribution
5. **Store report schemas** per report type in your metadata store

**Blocker today:** Pull API requires Growth plan or active 30-day trial + mobile app with live data.

**Next connector in sequence:** Adjust — evaluate free live API access before building.

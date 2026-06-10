# Workday REST API — Response Schema Documentation

This document describes every key-value pair returned by the Workday metadata endpoints exposed by this backend.

---

## Background — How Workday Exposes Metadata

Workday uses **REST APIs** under the path `/api/v1/{tenant}/`. Unlike SAP (EDMX XML) or Salesforce (describe endpoint), Workday organises its data into **Business Objects** grouped by **functional modules**. Each Business Object maps directly to a REST resource endpoint.

**Key concept mapping:**

| Traditional DB     | Salesforce         | SAP                 | Oracle Fusion       | HubSpot     | Workday                      |
|--------------------|--------------------|---------------------|---------------------|-------------|------------------------------|
| Database / Schema  | Org                | System              | Cloud Instance      | Portal      | **Tenant**                   |
| Schema / Domain    | —                  | OData Service       | Module              | —           | **Module**                   |
| Table              | SObject            | EntityType          | Resource            | Object      | **Business Object**          |
| Column / Field     | Field              | Property            | Attribute           | Property    | **Field**                    |
| Row                | Record             | Entity              | Record              | Record      | **Record**                   |
| Foreign Key / Join | Relationship       | NavigationProperty  | Child Resource      | Association | **Related Resource**         |
| Primary Key        | Id (18-char)       | Key Property        | Key Attribute       | id          | **Key Field** (`is_key`)     |

**Two operating modes:**
- **Demo Mode** — when `WORKDAY_TENANT` is not set in `.env`, returns built-in metadata based on the real Workday REST API schema (6 modules, 13 objects, 100+ fields). No Workday subscription needed.
- **Live Mode** — when `WORKDAY_TENANT`, `WORKDAY_CLIENT_ID`, and `WORKDAY_CLIENT_SECRET` are set, authenticates via OAuth 2.0 Client Credentials and fetches data from the real Workday tenant.

**Authentication (live mode):** OAuth 2.0 Client Credentials grant.
- Token URL: `https://{tenant}.workday.com/oauth2/token`
- API Base: `https://{tenant}.workday.com/api/v1/{tenant}`

---

## Table of Contents

1. [GET /api/v1/workday/connect](#1-get-apiv1workdayconnect)
2. [GET /api/v1/workday/modules](#2-get-apiv1workdaymodules)
   - [Top-Level Response](#21-top-level-response)
   - [Each Module Entry](#22-each-module-entry-inside-modules-array)
3. [GET /api/v1/workday/modules/{module_id}/objects](#3-get-apiv1workdaymodulesmodule_idobjects)
   - [Top-Level Response](#31-top-level-response)
   - [Each Object Summary Entry](#32-each-object-summary-entry-inside-objects-array)
4. [GET /api/v1/workday/objects](#4-get-apiv1workdayobjects)
5. [GET /api/v1/workday/objects/{object_name}/describe](#5-get-apiv1workdayobjectsobject_namedescribe)
   - [Top-Level Response](#51-top-level-response)
   - [Each Field Entry](#52-each-field-entry-inside-fields-array)
   - [Each Related Resource Entry](#53-each-entry-inside-related-array)
6. [Field Type Reference](#6-field-type-reference)
7. [Module & Business Object Reference](#7-module--business-object-reference)

---

## 1. GET /api/v1/workday/connect

Tests Workday connectivity. In Demo Mode returns a schema summary. In Live Mode fetches a sample worker record to confirm the OAuth token and tenant are valid.

**Example — Demo Mode Response**

```json
{
  "connected": true,
  "mode": "demo",
  "message": "Running in Demo Mode — showing real Workday REST API schema structure. Set WORKDAY_TENANT, WORKDAY_CLIENT_ID, WORKDAY_CLIENT_SECRET in .env to connect to a real Workday tenant.",
  "modules_count": 6,
  "total_objects": 13,
  "total_fields": 107,
  "workday_api_path": "/api/v1"
}
```

**Example — Live Mode Response**

```json
{
  "connected": true,
  "mode": "live",
  "tenant": "mycompany",
  "total_workers_sample": 4850
}
```

---

### Demo Mode Response Fields

| Key                  | Type      | Description |
|----------------------|-----------|-------------|
| `connected`          | `boolean` | Always `true` when this response is returned. A `401` HTTP error is raised instead if OAuth authentication fails in live mode. |
| `mode`               | `string`  | Indicates which operating mode is active. `"demo"` when `WORKDAY_TENANT` is not configured; `"live"` when a real Workday tenant is connected. This field is present on all endpoint responses. |
| `message`            | `string`  | A human-readable explanation of the current mode, with instructions for switching to live mode by setting environment variables. Only present in `"demo"` mode. |
| `modules_count`      | `integer` | Total number of Workday functional modules in the demo data (e.g. Human Resources, Payroll, Recruiting, Benefits, Time & Absence, Learning). Only present in `"demo"` mode. |
| `total_objects`      | `integer` | Total count of Business Objects (tables) across all modules in the demo data. Only present in `"demo"` mode. |
| `total_fields`       | `integer` | Total number of fields across all objects and all modules in the demo data. Gives an overall sense of schema coverage. Only present in `"demo"` mode. |
| `workday_api_path`   | `string`  | The REST API base path used for all Workday requests: `"/api/v1"`. The full URL is `https://{tenant}.workday.com/api/v1/{tenant}`. Only present in `"demo"` mode. |

### Live Mode Response Fields

| Key                    | Type      | Description |
|------------------------|-----------|-------------|
| `connected`            | `boolean` | Always `true` on a successful live connection. |
| `mode`                 | `string`  | Always `"live"` when a real Workday tenant is connected. |
| `tenant`               | `string`  | The Workday tenant name from `WORKDAY_TENANT` in `.env` (e.g. `"mycompany"`). Used as a URL path segment in all Workday REST API calls. |
| `total_workers_sample` | `integer` | The total count of worker records returned in a quick `GET /workers?limit=1` health check call. Confirms that the API is reachable and the token has read access to HR data. |

---

## 2. GET /api/v1/workday/modules

Lists all Workday functional modules. In both demo and live mode these are the 6 built-in Workday modules (Workday's REST API does not have a dynamic module-listing endpoint).

**Example Response**

```json
{
  "total": 6,
  "modules": [
    {
      "id": "humanResources",
      "label": "Human Resources",
      "description": "Workers, Positions, Job Profiles, Organizations, Locations, Compensation",
      "objects_count": 4
    }
  ]
}
```

---

### 2.1 Top-Level Response

| Key       | Type            | Description |
|-----------|-----------------|-------------|
| `total`   | `integer`       | Total number of modules returned. |
| `modules` | `array<object>` | List of module descriptors. Each entry represents one Workday functional area. See [2.2](#22-each-module-entry-inside-modules-array). |

---

### 2.2 Each Module Entry (inside `modules` array)

| Key             | Type      | Description |
|-----------------|-----------|-------------|
| `id`            | `string`  | The **module identifier** used as the `{module_id}` path parameter in `/modules/{module_id}/objects` (e.g. `"humanResources"`, `"payroll"`, `"recruiting"`, `"benefits"`, `"timeAndAbsence"`, `"learning"`). CamelCase, no spaces. |
| `label`         | `string`  | The **human-readable display name** of the module shown in the UI (e.g. `"Human Resources"`, `"Time & Absence"`, `"Learning"`). |
| `description`   | `string`  | A brief summary of the business area this module covers, listing the primary Business Objects it contains (e.g. `"Workers, Positions, Job Profiles, Organizations, Locations, Compensation"`). |
| `objects_count` | `integer` | Number of Business Objects (tables) available within this module. Useful for displaying a count badge in the UI. |

---

## 3. GET /api/v1/workday/modules/{module_id}/objects

Returns a lightweight summary list of all Business Objects within a specific Workday module — without full field details.

**Path Parameter**

| Parameter   | Type     | Description |
|-------------|----------|-------------|
| `module_id` | `string` | The module identifier from the `id` field in `/modules` (e.g. `humanResources`, `payroll`, `recruiting`). |

**Example Response**

```json
{
  "module_id": "humanResources",
  "module_label": "Human Resources",
  "total": 4,
  "mode": "demo",
  "objects": [
    {
      "name": "workers",
      "title": "Workers",
      "rest_path": "/workers",
      "description": "All workers (employees and contingent workers) in Workday",
      "fields_count": 16,
      "related_count": 3
    }
  ]
}
```

---

### 3.1 Top-Level Response

| Key            | Type            | Description |
|----------------|-----------------|-------------|
| `module_id`    | `string`        | Echoes back the `{module_id}` path parameter. |
| `module_label` | `string`        | Human-readable label of the module (e.g. `"Human Resources"`, `"Payroll"`). |
| `total`        | `integer`       | Total number of Business Objects returned for this module. |
| `mode`         | `string`        | `"demo"` or `"live"`. |
| `objects`      | `array<object>` | Summary list of Business Objects in this module. See [3.2](#32-each-object-summary-entry-inside-objects-array). |

---

### 3.2 Each Object Summary Entry (inside `objects` array)

| Key             | Type      | Description |
|-----------------|-----------|-------------|
| `name`          | `string`  | The **Business Object name** — used as the `{object_name}` path parameter in `/objects/{object_name}/describe` (e.g. `"workers"`, `"organizations"`, `"payrollResults"`). Also the Workday REST API path segment (appended to the tenant base URL). |
| `title`         | `string`  | The **human-readable display name** for this Business Object (e.g. `"Workers"`, `"Pay Groups"`, `"Job Requisitions"`). Used in UI lists and headers. |
| `rest_path`     | `string`  | The **relative REST API path** for querying records of this Business Object (e.g. `"/workers"`, `"/payrollResults"`, `"/jobRequisitions"`). Appended to the tenant base URL to build a full request URL: `https://{tenant}.workday.com/api/v1/{tenant}/workers`. |
| `description`   | `string`  | Brief plain-English description of what business data this object holds (e.g. `"All workers (employees and contingent workers) in Workday"`). |
| `fields_count`  | `integer` | Number of fields (columns) defined on this Business Object in the metadata. Gives a quick sense of schema complexity. |
| `related_count` | `integer` | Number of related resources (sub-endpoints accessible from a specific record of this object, e.g. compensation history, job history). |

---

## 4. GET /api/v1/workday/objects

Returns a **flat list of all Business Objects across every module** in one call. Useful for global search, cross-module comparisons, or when building a full schema overview.

**Example Response**

```json
{
  "total": 13,
  "mode": "demo",
  "objects": [
    {
      "name": "workers",
      "title": "Workers",
      "module": "humanResources",
      "rest_path": "/workers",
      "description": "All workers (employees and contingent workers) in Workday",
      "fields_count": 16,
      "related_count": 3
    }
  ]
}
```

### Response Fields

| Key       | Type            | Description |
|-----------|-----------------|-------------|
| `total`   | `integer`       | Total count of all Business Objects across all modules. |
| `mode`    | `string`        | `"demo"` or `"live"`. |
| `objects` | `array<object>` | Flat list of all objects. Same structure as [3.2](#32-each-object-summary-entry-inside-objects-array) with one additional field: |

**Additional field (only in the flat list):**

| Key      | Type     | Description |
|----------|----------|-------------|
| `module` | `string` | The `id` of the Workday module this object belongs to (e.g. `"humanResources"`, `"payroll"`, `"recruiting"`). Included because this flat list spans all modules. |

---

## 5. GET /api/v1/workday/objects/{object_name}/describe

Returns **complete metadata** for one Workday Business Object — all field definitions with types and constraint flags, plus related resource (sub-endpoint) links.

**Path Parameter**

| Parameter     | Type     | Description |
|---------------|----------|-------------|
| `object_name` | `string` | The Business Object name (e.g. `workers`, `organizations`, `payrollResults`, `jobRequisitions`, `learningCourses`). Must match a `name` from the objects list. |

**Example Response**

```json
{
  "name": "workers",
  "title": "Workers",
  "module": "humanResources",
  "rest_path": "/workers",
  "description": "All workers (employees and contingent workers) in Workday",
  "fields_count": 16,
  "related_count": 3,
  "mode": "demo",
  "fields": [
    {
      "name": "workerId",
      "title": "Worker ID",
      "type": "string",
      "required": true,
      "filterable": true,
      "is_key": true,
      "description": "Unique identifier for the worker"
    },
    {
      "name": "primaryJob",
      "title": "Primary Job",
      "type": "object",
      "required": true,
      "filterable": true,
      "is_key": false,
      "description": "Current primary job assignment"
    }
  ],
  "related": [
    {
      "name": "workers/{workerId}/jobHistory",
      "title": "Job History",
      "description": "Historical job positions for the worker"
    }
  ]
}
```

---

### 5.1 Top-Level Response

| Key             | Type            | Description |
|-----------------|-----------------|-------------|
| `name`          | `string`        | Business Object name as used in the URL. |
| `title`         | `string`        | Human-readable display title (e.g. `"Workers"`, `"Payroll Results"`). |
| `module`        | `string`        | The `id` of the module this object belongs to. Used for breadcrumb navigation. |
| `rest_path`     | `string`        | Relative REST API path for querying records (e.g. `"/workers"`). Appended to the tenant base URL. |
| `description`   | `string`        | Plain-English description of the business data this object holds. |
| `fields_count`  | `integer`       | Total number of fields on this object. |
| `related_count` | `integer`       | Total number of related sub-resources accessible from a record of this object. |
| `mode`          | `string`        | `"demo"` or `"live"`. |
| `fields`        | `array<object>` | Complete list of field descriptors. Each entry describes one column. See [5.2](#52-each-field-entry-inside-fields-array). |
| `related`       | `array<object>` | List of related resource links — sub-endpoints accessible from a specific record. See [5.3](#53-each-entry-inside-related-array). |

---

### 5.2 Each Field Entry (inside `fields` array)

| Key           | Type      | Description |
|---------------|-----------|-------------|
| `name`        | `string`  | The **API field name** as used in Workday REST API JSON payloads and query filters (e.g. `"workerId"`, `"hireDate"`, `"primarySupervisoryOrganization"`). CamelCase convention. This is the key in the JSON response body when fetching records from the live Workday API. |
| `title`       | `string`  | The **human-readable display label** for this field as shown in Workday's UI (e.g. `"Worker ID"`, `"Hire Date"`, `"Supervisory Org"`). Use this for UI column headers and form labels. May be significantly shorter than `name`. |
| `type`        | `string`  | The **data type** of the field value. Determines how the value is serialized, rendered, and validated. See the [Field Type Reference](#6-field-type-reference) for all possible values (`"string"`, `"integer"`, `"number"`, `"boolean"`, `"date"`, `"object"`, `"array"`). |
| `required`    | `boolean` | Whether this field **must have a value** in a valid Workday record. `true` = mandatory; `false` = optional. Required fields will cause a validation error if missing in create/update operations via the live REST API. |
| `filterable`  | `boolean` | Whether this field can be used in **REST query filter parameters** when retrieving records (e.g. `?hireDate>=2023-01-01`). `false` for free-text narrative fields (`comments`, `courseDescription`), binary fields, and fields not indexed by Workday for filtering. |
| `is_key`      | `boolean` | Whether this field is the **primary key (unique identifier)** for this Business Object. `true` for exactly one field per object (e.g. `workerId` on Workers, `id` on Organizations). Used when constructing record-specific URL paths (e.g. `/workers/{workerId}/compensation`). |
| `description` | `string`  | A plain-English description of what this specific field represents and how it is used (e.g. `"Unique identifier for the worker"`, `"Date the worker was hired"`, `"Full Time or Part Time"`). Based on real Workday field semantics. |

---

### 5.3 Each Entry (inside `related` array)

Related resources are **sub-endpoints** accessible from a specific record of the parent Business Object. They represent one-to-many relationships — one parent record has many related child records accessible via a nested URL.

| Key           | Type     | Description |
|---------------|----------|-------------|
| `name`        | `string` | The **related resource path template** for accessing this sub-resource from a parent record (e.g. `"workers/{workerId}/jobHistory"`, `"payrollResults/{id}/earningLines"`). The `{key}` placeholder is replaced by the actual record's key field value when making a live API call: `GET /workers/abc123/jobHistory`. |
| `title`       | `string` | The **human-readable display name** for this related resource (e.g. `"Job History"`, `"Earning Lines"`, `"Benefit Elections"`). Used in UI sub-tabs and nested list headers. |
| `description` | `string` | A brief explanation of what data this related resource contains and its relationship to the parent (e.g. `"Historical job positions for the worker"`, `"Individual earning components (salary, bonus, etc.)"`). |

---

## 6. Field Type Reference

Workday REST API fields use 7 types. Unlike SAP's verbose EDM types, Workday uses JSON-native types aligned with the REST/JSON standard.

| `type`      | Description |
|-------------|-------------|
| `string`    | A text value. Covers names, codes, status values, enumerations (e.g. `"Employee"`, `"Full Time"`, `"Approved"`), phone numbers, email addresses, and any free-form text. The most common type in Workday. |
| `integer`   | A whole number with no decimal places. Used for counts and quantities (e.g. `numberOfOpenings` on Job Requisitions, `durationMinutes` on Learning Courses). |
| `number`    | A decimal numeric value. Used for monetary amounts and fractional quantities (e.g. `grossPay`, `netPay`, `totalDays`). May include decimal places. |
| `boolean`   | A `true` / `false` value. Used for flag fields such as `inactive` (on Organizations, Locations, Job Profiles), `paidTimeOff` (on Time Off Types), and `includeOrganizationInHierarchy`. |
| `date`      | A calendar date value in `YYYY-MM-DD` format (e.g. `"2023-06-15"`). Used for hire dates, period dates, enrollment dates, and expiration dates. No time component. |
| `object`    | A **nested JSON object** representing a reference to a related Workday record. Instead of storing just a foreign key ID, Workday embeds a structured reference (typically `{ "id": "...", "descriptor": "..." }`). Examples: `primaryJob`, `location`, `worker`, `payGroup`, `currency`, `country`. Use the `id` inside to navigate to the related record. |
| `array`     | A **list of values or objects**. Used for multi-value fields such as `coverageLevels` on Benefit Plans, which can hold multiple coverage tier values (e.g. `["Employee Only", "Employee + Spouse", "Family"]`). |

> **Workday object references:** When `type` is `"object"`, the value in a live API response is typically `{ "id": "WID_xxx", "descriptor": "Human-readable label" }`. The `id` is a Workday Internal ID (WID) — a UUID-style string used to uniquely identify any record in Workday across all object types.

---

## 7. Module & Business Object Reference

All 6 Workday modules and their 13 Business Objects available in this backend.

### Human Resources
*Workers, Positions, Job Profiles, Organizations, Locations, Compensation*

| Object          | Title                | Key Field   | Related Resources |
|-----------------|----------------------|-------------|-------------------|
| `workers`       | Workers              | `workerId`  | `jobHistory`, `compensation`, `roles` |
| `organizations` | Organizations        | `id`        | `workers` (in org) |
| `jobProfiles`   | Job Profiles         | `id`        | *(none)* |
| `locations`     | Locations            | `id`        | *(none)* |

### Payroll
*Pay Groups, Pay Period Calendars, Payroll Results, Earnings, Deductions*

| Object           | Title            | Key Field | Related Resources |
|------------------|------------------|-----------|-------------------|
| `payGroups`      | Pay Groups       | `id`      | `payPeriodCalendars` |
| `payrollResults` | Payroll Results  | `id`      | `earningLines`, `deductionLines` |

### Recruiting
*Job Requisitions, Job Applications, Candidates, Interview Feedback, Offers*

| Object              | Title              | Key Field | Related Resources |
|---------------------|--------------------|-----------|-------------------|
| `jobRequisitions`   | Job Requisitions   | `id`      | `jobApplications` |
| `jobApplications`   | Job Applications   | `id`      | `interviewFeedback` |

### Benefits
*Benefit Plans, Benefit Elections, Dependents, Coverage*

| Object         | Title          | Key Field | Related Resources |
|----------------|----------------|-----------|-------------------|
| `benefitPlans` | Benefit Plans  | `id`      | `benefitElections` |

### Time & Absence
*Time Off Types, Absence Requests, Time Entries, Accrual Balances*

| Object              | Title               | Key Field | Related Resources |
|---------------------|---------------------|-----------|-------------------|
| `timeOffTypes`      | Time Off Types      | `id`      | *(none)* |
| `absenceRequests`   | Absence Requests    | `id`      | *(none)* |

### Learning
*Courses, Learning Content, Programs, Enrollments, Completions*

| Object            | Title             | Key Field | Related Resources |
|-------------------|-------------------|-----------|-------------------|
| `learningCourses` | Learning Courses  | `id`      | `enrollments` |

---

*Generated from backend source: `backend/workday/service.py` — `test_connection()`, `list_modules()`, `get_module_objects()`, `get_all_objects()`, and `get_object_describe()`*

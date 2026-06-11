# ServiceNow API — Response Schema Documentation

This document describes every key-value pair returned by the ServiceNow metadata endpoints exposed by this backend.

---

## Background — How ServiceNow Exposes Metadata

ServiceNow is unique in that its **entire platform schema is stored in its own tables**. Every table definition, every column, every label — all of it lives in two system tables that are queryable through the standard Table API:

| System Table     | Purpose |
|------------------|---------|
| `sys_db_object`  | Lists all tables (equivalent to `INFORMATION_SCHEMA.TABLES` in SQL) |
| `sys_dictionary` | Lists all columns/fields for every table (equivalent to `INFORMATION_SCHEMA.COLUMNS`) |

This means the same REST API used for business data (`/api/now/table/{table_name}`) is also used to fetch metadata — there is no separate schema/describe endpoint.

**Key concept mapping:**

| Traditional DB     | Salesforce      | SAP              | Oracle Fusion   | Workday             | ServiceNow                   |
|--------------------|-----------------|------------------|-----------------|---------------------|------------------------------|
| Database / Schema  | Org             | System           | Cloud Instance  | Tenant              | **Instance**                 |
| Schema / Domain    | —               | OData Service    | Module          | Module              | **Category** (grouping)      |
| Table              | SObject         | EntityType       | Resource        | Business Object     | **Table**                    |
| Column / Field     | Field           | Property         | Attribute       | Field               | **Column** (sys_dictionary)  |
| Row                | Record          | Entity           | Record          | Record              | **Record**                   |
| Foreign Key / Join | Relationship    | NavigationProp   | Child Resource  | Related Resource    | **Reference** field          |
| Primary Key        | Id (18-char)    | Key Property     | Key Attribute   | Key Field (`is_key`)| **`sys_id`** (32-char GUID)  |
| Table Inheritance  | —               | —                | —               | —                   | **`is_extendable`** (extends)|

**Two operating modes:**
- **Demo Mode** — when `SN_INSTANCE_URL` is not set in `.env`, returns built-in metadata based on the real ServiceNow schema (4 categories, 11 tables, 100+ fields). No ServiceNow account needed.
- **Live Mode** — when `SN_INSTANCE_URL`, `SN_USERNAME`, and `SN_PASSWORD` are set, queries the real ServiceNow instance's `sys_db_object` and `sys_dictionary` tables directly.

**Authentication (live mode):** HTTP Basic Auth — `SN_USERNAME` + `SN_PASSWORD`.
> Free Personal Developer Instances are available at [developer.servicenow.com](https://developer.servicenow.com).

---

## Table of Contents

1. [GET /api/v1/servicenow/connect](#1-get-apiv1servicenowconnect)
2. [GET /api/v1/servicenow/categories](#2-get-apiv1servicenowcategories)
   - [Top-Level Response](#21-top-level-response)
   - [Each Category Entry](#22-each-category-entry-inside-categories-array)
3. [GET /api/v1/servicenow/tables](#3-get-apiv1servicenowstables)
   - [Query Parameters](#query-parameters)
   - [Top-Level Response](#31-top-level-response)
   - [Each Table Entry](#32-each-table-entry-inside-tables-array)
4. [GET /api/v1/servicenow/tables/{table_name}/fields](#4-get-apiv1servicenow-tablestable_namefields)
   - [Top-Level Response](#41-top-level-response)
   - [Each Field Entry](#42-each-field-entry-inside-fields-array)
5. [ServiceNow Field Type Reference](#5-servicenow-field-type-reference)
6. [Category & Table Reference](#6-category--table-reference)
7. [System Fields Present on Every Table](#7-system-fields-present-on-every-table)

---

## 1. GET /api/v1/servicenow/connect

Tests ServiceNow connectivity. In Demo Mode returns a schema summary. In Live Mode queries `sys_db_object` with a 1-record limit to confirm the instance URL, credentials, and Table API are reachable.

**Example — Demo Mode Response**

```json
{
  "connected": true,
  "mode": "demo",
  "message": "Running in Demo Mode — showing real ServiceNow table/field schema. Set SN_INSTANCE_URL, SN_USERNAME, SN_PASSWORD in .env to connect to your Personal Developer Instance.",
  "categories_count": 4,
  "total_tables": 11,
  "total_fields": 107
}
```

**Example — Live Mode Response**

```json
{
  "connected": true,
  "mode": "live",
  "instance_url": "https://dev12345.service-now.com",
  "result_count": 1
}
```

---

### Demo Mode Response Fields

| Key                | Type      | Description |
|--------------------|-----------|-------------|
| `connected`        | `boolean` | Always `true` when this response is returned. A `401` HTTP error is raised instead if Basic Auth credentials are wrong in live mode. |
| `mode`             | `string`  | `"demo"` when `SN_INSTANCE_URL` is not configured; `"live"` when a real ServiceNow instance is connected. Present on all endpoint responses. |
| `message`          | `string`  | Human-readable explanation of the current mode with instructions for switching to live mode. Only present in `"demo"` mode. |
| `categories_count` | `integer` | Total number of table categories in the demo data (ITSM, CMDB, Users & Access, Service Catalog). Only present in `"demo"` mode. |
| `total_tables`     | `integer` | Total count of tables across all categories in demo data. Only present in `"demo"` mode. |
| `total_fields`     | `integer` | Total number of fields across all demo tables. Gives a broad sense of schema coverage. Only present in `"demo"` mode. |

### Live Mode Response Fields

| Key            | Type      | Description |
|----------------|-----------|-------------|
| `connected`    | `boolean` | Always `true` on a successful live response. |
| `mode`         | `string`  | Always `"live"` when connected to a real ServiceNow instance. |
| `instance_url` | `string`  | The ServiceNow instance base URL from `SN_INSTANCE_URL` in `.env` (e.g. `"https://dev12345.service-now.com"`). Uniquely identifies the connected ServiceNow tenant. |
| `result_count` | `integer` | Number of records returned from a quick `sys_db_object` probe query (`sysparm_limit=1`). Should always be `1` on a healthy connected instance, confirming the Table API is responding. |

---

## 2. GET /api/v1/servicenow/categories

Lists the top-level category groupings used to organise ServiceNow tables. ServiceNow does not natively expose a category concept — these groupings are defined in this backend for navigation convenience and match the major functional areas of every ServiceNow instance.

**Example Response**

```json
{
  "total": 4,
  "categories": [
    {
      "id": "itsm",
      "label": "IT Service Management",
      "description": "Incident, Change, Problem, Service Request management",
      "tables_count": 4
    }
  ]
}
```

---

### 2.1 Top-Level Response

| Key          | Type            | Description |
|--------------|-----------------|-------------|
| `total`      | `integer`       | Total number of categories returned. |
| `categories` | `array<object>` | List of category descriptors. See [2.2](#22-each-category-entry-inside-categories-array). |

---

### 2.2 Each Category Entry (inside `categories` array)

| Key            | Type      | Description |
|----------------|-----------|-------------|
| `id`           | `string`  | The **category identifier** used as the `category` query parameter in `/tables?category={id}` to filter tables by functional area (e.g. `"itsm"`, `"cmdb"`, `"users"`, `"catalog"`). Lowercase, no spaces. |
| `label`        | `string`  | The **human-readable name** of the category displayed in the UI (e.g. `"IT Service Management"`, `"Configuration Management (CMDB)"`, `"Users & Access"`). |
| `description`  | `string`  | A brief explanation of which ServiceNow application area this category covers and which tables it contains (e.g. `"Incident, Change, Problem, Service Request management"`). |
| `tables_count` | `integer` | Number of tables within this category available in the demo data. `0` in live mode (ServiceNow does not expose a native table-count-per-scope endpoint). |

---

## 3. GET /api/v1/servicenow/tables

Lists ServiceNow tables. In demo mode returns the well-known built-in tables. In live mode dynamically queries `sys_db_object` — the ServiceNow system table that contains one record per table in the entire instance.

### Query Parameters

| Parameter  | Type      | Default | Description |
|------------|-----------|---------|-------------|
| `category` | `string`  | `null`  | Filter tables by category ID (e.g. `itsm`, `cmdb`, `users`, `catalog`). Demo mode only. |
| `search`   | `string`  | `null`  | Search tables by name or label substring (e.g. `search=incident`). Works in both demo and live mode. |
| `limit`    | `integer` | `100`   | Maximum number of tables to return. Applies to live mode only (demo always returns all matching). |

**Example Response**

```json
{
  "total": 4,
  "mode": "demo",
  "tables": [
    {
      "name": "incident",
      "label": "Incident",
      "category": "itsm",
      "description": "IT incidents reported by users or monitoring systems",
      "is_extendable": true,
      "fields_count": 20
    }
  ]
}
```

---

### 3.1 Top-Level Response

| Key      | Type            | Description |
|----------|-----------------|-------------|
| `total`  | `integer`       | Total count of tables returned after applying any `category` or `search` filters. |
| `mode`   | `string`        | `"demo"` or `"live"`. |
| `tables` | `array<object>` | List of table descriptors. See [3.2](#32-each-table-entry-inside-tables-array). |

---

### 3.2 Each Table Entry (inside `tables` array)

| Key             | Type              | Description |
|-----------------|-------------------|-------------|
| `name`          | `string`          | The **technical table name** as stored in ServiceNow and used in all API calls (e.g. `"incident"`, `"change_request"`, `"cmdb_ci_server"`, `"sys_user"`). This is the value used as `{table_name}` in the `/tables/{table_name}/fields` endpoint and in live Table API queries (`GET /api/now/table/incident`). Follows `snake_case` convention. |
| `label`         | `string`          | The **human-readable display name** for the table as shown in ServiceNow's UI (e.g. `"Incident"`, `"Change Request"`, `"Server"`). May differ significantly from `name`. |
| `category`      | `string`          | The `id` of the category this table belongs to (e.g. `"itsm"`, `"cmdb"`, `"users"`, `"catalog"`). In live mode this may be the `sys_scope.name` value from `sys_db_object`. |
| `description`   | `string`          | Plain-English description of what business data this table holds (e.g. `"IT incidents reported by users or monitoring systems"`). May be empty string in live mode since `sys_db_object` does not always store descriptions. |
| `is_extendable` | `boolean`         | Whether this table is part of ServiceNow's **table inheritance hierarchy** — i.e., other tables can extend (inherit from) it. `true` for base tables like `cmdb_ci` (which `cmdb_ci_server`, `cmdb_ci_appl`, etc. all extend). When `true`, child tables inherit all fields from this parent table in addition to their own. |
| `fields_count`  | `integer \| null` | Number of fields defined on this table. Available in demo mode. `null` in live mode (fetching field counts for every table would require one `sys_dictionary` query per table). |

---

## 4. GET /api/v1/servicenow/tables/{table_name}/fields

Returns **complete field-level metadata** for one ServiceNow table — sourced from `sys_dictionary` in live mode, or from the built-in demo schema in demo mode.

This is the ServiceNow equivalent of:
- Salesforce: `GET /api/v1/salesforce/objects/{name}/metadata`
- SAP: `GET /api/v1/sap/services/{service}/entities/{entity}/fields`
- Oracle: `GET /api/v1/oracle/resources/{resource}/describe`
- Workday: `GET /api/v1/workday/objects/{object}/describe`

**Path Parameter**

| Parameter    | Type     | Description |
|--------------|----------|-------------|
| `table_name` | `string` | The technical name of the ServiceNow table (e.g. `incident`, `change_request`, `cmdb_ci_server`, `sys_user`). Must match the `name` from the tables list. |

**Example Response**

```json
{
  "table_name": "incident",
  "table_label": "Incident",
  "description": "IT incidents reported by users or monitoring systems",
  "is_extendable": true,
  "fields_count": 20,
  "mode": "demo",
  "fields": [
    {
      "name": "sys_id",
      "label": "Sys ID",
      "type": "GUID",
      "mandatory": true,
      "is_key": true,
      "max_length": 32,
      "reference": null,
      "description": "Unique system identifier"
    },
    {
      "name": "caller_id",
      "label": "Caller",
      "type": "reference",
      "mandatory": true,
      "is_key": false,
      "max_length": 32,
      "reference": "sys_user",
      "description": "User who reported the incident"
    },
    {
      "name": "state",
      "label": "State",
      "type": "integer",
      "mandatory": true,
      "is_key": false,
      "max_length": null,
      "reference": null,
      "description": "1=New, 2=In Progress, 3=On Hold, 6=Resolved, 7=Closed"
    }
  ]
}
```

---

### 4.1 Top-Level Response

| Key             | Type            | Description |
|-----------------|-----------------|-------------|
| `table_name`    | `string`        | The technical table name as used in the URL path parameter. |
| `table_label`   | `string`        | The human-readable display name for this table (e.g. `"Incident"`, `"Server"`, `"User"`). In live mode, sourced from `sys_db_object.label`. |
| `description`   | `string`        | Plain-English description of the table's business purpose. May be empty in live mode. |
| `is_extendable` | `boolean`       | Whether this table can be extended (inherited from) by other tables. Base class tables like `cmdb_ci` and `task` are extendable; most leaf tables are not. |
| `fields_count`  | `integer`       | Total number of fields returned for this table. |
| `mode`          | `string`        | `"demo"` or `"live"`. |
| `fields`        | `array<object>` | Complete list of field descriptors. Each entry describes one column. See [4.2](#42-each-field-entry-inside-fields-array). |

---

### 4.2 Each Field Entry (inside `fields` array)

| Key           | Type               | Description |
|---------------|--------------------|-------------|
| `name`        | `string`           | The **technical field/column name** as stored in `sys_dictionary.element` and used in all Table API requests and responses (e.g. `"sys_id"`, `"short_description"`, `"caller_id"`, `"assigned_to"`). `snake_case` convention. This is the key used in JSON payloads when creating/updating records and in `sysparm_fields` query parameters. |
| `label`       | `string`           | The **human-readable column label** displayed in the ServiceNow UI forms and list views (e.g. `"Short Description"`, `"Caller"`, `"Assigned To"`). Sourced from `sys_dictionary.column_label`. May differ significantly from `name`. |
| `type`        | `string`           | The **internal Glide field type** from `sys_dictionary.internal_type`. Determines how the value is stored, rendered, and validated in ServiceNow. See the [Field Type Reference](#5-servicenow-field-type-reference) for all types (e.g. `"string"`, `"integer"`, `"reference"`, `"glide_date_time"`, `"GUID"`, `"boolean"`). |
| `mandatory`   | `boolean`          | Whether this field **must have a value** when creating a record. `true` = required field; omitting it in a `POST` will cause a ServiceNow validation error. Sourced from `sys_dictionary.mandatory`. |
| `is_key`      | `boolean`          | Whether this field is the **primary key** of the table. `true` only for `sys_id` — the 32-character GUID that uniquely identifies every record in every ServiceNow table. Used to construct direct-access URLs (e.g. `GET /api/now/table/incident/{sys_id}`). |
| `max_length`  | `integer \| null`  | Maximum allowed character length for text-based fields (e.g. `160` for `short_description`, `4000` for `description`, `32` for `reference` fields). `null` for numeric, boolean, date, and GUID types where character length is not applicable. |
| `reference`   | `string \| null`   | For `"reference"` type fields only: the **name of the table this field links to** (e.g. `"sys_user"`, `"sys_user_group"`, `"cmn_location"`, `"cmn_department"`). This is how ServiceNow implements foreign keys — a reference field stores the `sys_id` of a record in the referenced table. `null` for all non-reference field types. |
| `description` | `string`           | A plain-English explanation of what this field represents, including coded value meanings for integer choice fields (e.g. `"1=New, 2=In Progress, 3=On Hold, 6=Resolved, 7=Closed"` for `state`). Sourced from `sys_dictionary.comments` in live mode; hand-authored for demo mode. |

---

## 5. ServiceNow Field Type Reference

ServiceNow uses **Glide** types (prefixed internally as `glide_*`). These are ServiceNow's own type system stored in `sys_dictionary.internal_type`.

| `type`              | Description |
|---------------------|-------------|
| `GUID`              | A 32-character hexadecimal globally unique identifier. Every record in every ServiceNow table has exactly one `sys_id` of this type. Used as the primary key and in all cross-table references. |
| `string`            | A plain text field. The most common type. `max_length` defines the character limit (e.g. 160 for `short_description`, 4000 for `description`, 40 for `number`). |
| `integer`           | A whole number. Widely used for coded/choice fields where each integer maps to a label (e.g. `state`: 1=New, 2=In Progress; `priority`: 1=Critical, 2=High, etc.). |
| `boolean`           | A true/false field. Serialized as `"true"` or `"false"` strings in the Table API JSON response. Used for flags like `active`, `virtual`, `mandatory`. |
| `glide_date_time`   | A date and time value stored in UTC, formatted as `YYYY-MM-DD HH:MM:SS` (e.g. `"2024-01-15 09:30:00"`). Used for all timestamp fields: `opened_at`, `resolved_at`, `sys_created_on`, `sys_updated_on`. |
| `glide_date`        | A date-only value with no time component, formatted as `YYYY-MM-DD`. Used for scheduled dates without specific times. |
| `reference`         | A foreign key field that stores the `sys_id` of a record in another (or the same) table. The `reference` field in the metadata names the target table. In Table API responses, reference fields return both a `value` (the raw `sys_id`) and a `display_value` (the human-readable label). |
| `currency`          | A monetary value. Stored as a decimal number with a currency code (e.g. `"USD;100.00"`). Used for `price` fields on Service Catalog items and Service Requests. |
| `decimal`           | A floating-point decimal number. Used for physical measurements like `disk_space` (GB). |
| `float`             | A single-precision floating-point number. Used for calculated numeric values. |
| `long`              | A 64-bit integer. Used for very large numeric values. |
| `email`             | A text field validated as an email address format. Stored as plain text but validated on input. |
| `phone_number`      | A text field for phone numbers. May include country code formatting depending on instance configuration. |
| `url`               | A text field validated and rendered as a clickable hyperlink in the ServiceNow UI. |
| `html`              | A rich-text/HTML field. Content is stored with HTML markup and rendered in the UI as formatted text. |
| `choice`            | An enumeration field where valid values are defined in the `sys_choice` table. Choice fields are rendered as dropdowns in the UI. Integer-based choice fields use numeric codes. |
| `journal_input`     | A journal/activity field for appending time-stamped notes. Used for work notes and comments on ITSM records. Append-only — cannot be overwritten. |
| `glide_list`        | A multi-value list field that stores multiple `sys_id` references. Used for fields like CI lists on Change Requests. |
| `conditions`        | A filter conditions field. Stores encoded query strings used for dynamic scoping (e.g. in groups, notifications). |
| `script`            | A JavaScript code field. Used in business rules, client scripts, and script includes. |

---

## 6. Category & Table Reference

All 4 categories and 11 tables available in this backend (demo and live mode).

### IT Service Management (`itsm`)
*Incident, Change, Problem, Service Request management*

| Table           | Label           | Key Field | `is_extendable` | Notable Fields |
|-----------------|-----------------|-----------|-----------------|----------------|
| `incident`      | Incident        | `sys_id`  | `true`          | `number`, `state`, `priority`, `urgency`, `impact`, `caller_id`, `assigned_to` |
| `change_request`| Change Request  | `sys_id`  | `true`          | `number`, `type`, `state`, `risk`, `requested_by`, `start_date`, `end_date` |
| `problem`       | Problem         | `sys_id`  | `false`         | `number`, `state`, `cause_notes`, `fix_notes` |
| `sc_request`    | Service Request | `sys_id`  | `false`         | `number`, `requested_for`, `state`, `price` |

### Configuration Management (`cmdb`)
*Configuration Items: Servers, Applications, Databases, Network devices*

| Table           | Label                  | Key Field | `is_extendable` | Notable Fields |
|-----------------|------------------------|-----------|-----------------|----------------|
| `cmdb_ci`       | Configuration Item     | `sys_id`  | `true`          | `name`, `sys_class_name`, `operational_status`, `install_status` |
| `cmdb_ci_server`| Server                 | `sys_id`  | `true`          | `ip_address`, `fqdn`, `os`, `os_version`, `cpu_count`, `ram`, `disk_space`, `virtual` |

### Users & Access (`users`)
*Users, Groups, Roles, Access Control*

| Table           | Label  | Key Field | `is_extendable` | Notable Fields |
|-----------------|--------|-----------|-----------------|----------------|
| `sys_user`      | User   | `sys_id`  | `false`         | `user_name`, `first_name`, `last_name`, `email`, `active`, `manager` |
| `sys_user_group`| Group  | `sys_id`  | `false`         | `name`, `manager`, `active`, `email`, `type` |

### Service Catalog (`catalog`)
*Catalog Items, Categories, Orders*

| Table        | Label        | Key Field | `is_extendable` | Notable Fields |
|--------------|--------------|-----------|-----------------|----------------|
| `sc_cat_item`| Catalog Item | `sys_id`  | `true`          | `name`, `short_description`, `category`, `price`, `active`, `availability` |

---

## 7. System Fields Present on Every Table

ServiceNow automatically adds a set of **`sys_*` system fields** to every table. These are not user-defined — they are managed by the ServiceNow platform and should always be present in any `/fields` response.

| Field Name        | Type              | Description |
|-------------------|-------------------|-------------|
| `sys_id`          | `GUID`            | The universal primary key — a 32-character GUID unique across all tables. Every record in every ServiceNow table has this field. |
| `sys_created_on`  | `glide_date_time` | Timestamp of when the record was first created. Set automatically by the platform; never user-editable. |
| `sys_created_by`  | `string`          | Username of the user who created the record. Set automatically by the platform. |
| `sys_updated_on`  | `glide_date_time` | Timestamp of the most recent change to any field on the record. Updated automatically on every save. |
| `sys_updated_by`  | `string`          | Username of the last user to modify the record. |
| `sys_class_name`  | `string`          | The actual table class name of the record — critical for polymorphic queries on extendable tables (e.g. querying `cmdb_ci` returns records of type `cmdb_ci_server`, `cmdb_ci_appl`, etc., and `sys_class_name` tells you which sub-type each record is). |
| `sys_mod_count`   | `integer`         | A counter incremented each time the record is saved. Useful for optimistic concurrency and detecting stale reads. |

---

*Generated from backend source: `backend/servicenow/service.py` — `test_connection()`, `list_categories()`, `list_tables()`, and `get_table_fields()`*

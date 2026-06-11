# NetSuite REST API — Response Schema Documentation

This document describes every key-value pair returned by the NetSuite metadata endpoints exposed by this backend.

---

## Background — How NetSuite Exposes Metadata

NetSuite uses a dedicated **REST Metadata Catalog API** under:
```
/services/rest/record/v1/metadata-catalog/
```

This is distinct from the data API (`/services/rest/record/v1/{recordType}`). The metadata catalog returns JSON Schema-style documents describing every field, type, and reference for a given Record Type — similar in concept to Salesforce's describe API but following JSON Schema conventions.

**Key API endpoints used internally:**

| Purpose             | Endpoint |
|---------------------|----------|
| List all record types | `GET /services/rest/record/v1/metadata-catalog/` |
| Record type schema  | `GET /services/rest/record/v1/metadata-catalog/{recordType}` |
| Fetch live records  | `GET /services/rest/record/v1/{recordType}` |

**Key concept mapping across all connectors:**

| Traditional DB     | Salesforce      | SAP              | Oracle Fusion   | Workday             | ServiceNow       | NetSuite                    |
|--------------------|-----------------|------------------|-----------------|---------------------|------------------|-----------------------------|
| Database / Schema  | Org             | System           | Cloud Instance  | Tenant              | Instance         | **Account**                 |
| Schema / Domain    | —               | OData Service    | Module          | Module              | Category         | **Module**                  |
| Table              | SObject         | EntityType       | Resource        | Business Object     | Table            | **Record Type**             |
| Column / Field     | Field           | Property         | Attribute       | Field               | Column           | **Field / Property**        |
| Row                | Record          | Entity           | Record          | Record              | Record           | **Record**                  |
| Foreign Key / Join | Relationship    | NavigationProp   | Child Resource  | Related Resource    | Reference field  | **`select` + `referenceType`** |
| Primary Key        | Id (18-char)    | Key Property     | Key Attribute   | `is_key` field      | `sys_id` (GUID)  | **`id` (integer)**          |
| Multi-row section  | —               | —                | Child Resource  | —                   | —                | **Sublist**                 |

**Two operating modes:**
- **Demo Mode** — when `NS_ACCOUNT_ID` is not set in `.env`, returns built-in metadata based on the real NetSuite REST Metadata Catalog schema (7 modules, 13 record types, 130+ fields). No NetSuite account needed.
- **Live Mode** — when `NS_ACCOUNT_ID`, `NS_CLIENT_ID`, and `NS_CLIENT_SECRET` are set, authenticates via OAuth 2.0 Client Credentials and queries the real NetSuite Metadata Catalog API.

**Authentication (live mode):** OAuth 2.0 Client Credentials (Machine-to-Machine).
- Token URL: `https://{account_id}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token`
- API Base: `https://{account_id}.suitetalk.api.netsuite.com/services/rest/record/v1`

---

## Table of Contents

1. [GET /api/v1/netsuite/connect](#1-get-apiv1netsuiteconnect)
2. [GET /api/v1/netsuite/modules](#2-get-apiv1netsuitmodules)
   - [Top-Level Response](#21-top-level-response)
   - [Each Module Entry](#22-each-module-entry-inside-modules-array)
3. [GET /api/v1/netsuite/modules/{module_id}/records](#3-get-apiv1netsuitemodulesmodule_idrecords)
   - [Top-Level Response](#31-top-level-response)
   - [Each Record Summary Entry](#32-each-record-summary-entry-inside-records-array)
4. [GET /api/v1/netsuite/records](#4-get-apiv1netsuiterecords)
5. [GET /api/v1/netsuite/records/{record_type}/fields](#5-get-apiv1netsuiterecordsrecord_typefields)
   - [Top-Level Response](#51-top-level-response)
   - [Each Field Entry](#52-each-field-entry-inside-fields-array)
6. [Field Type Reference](#6-field-type-reference)
7. [Module & Record Type Reference](#7-module--record-type-reference)
8. [Common NetSuite Reference Types](#8-common-netsuite-reference-types)

---

## 1. GET /api/v1/netsuite/connect

Tests NetSuite connectivity. In Demo Mode returns a schema summary. In Live Mode fetches the root metadata catalog listing to verify the Account ID, OAuth token, and API access are working.

**Example — Demo Mode Response**

```json
{
  "connected": true,
  "mode": "demo",
  "message": "Running in Demo Mode — showing real NetSuite REST Metadata Catalog schema. Set NS_ACCOUNT_ID, NS_CLIENT_ID, NS_CLIENT_SECRET in .env to connect to a real NetSuite account.",
  "modules_count": 7,
  "total_record_types": 13,
  "total_fields": 132
}
```

**Example — Live Mode Response**

```json
{
  "connected": true,
  "mode": "live",
  "account_id": "1234567",
  "total_record_types": 287
}
```

---

### Demo Mode Response Fields

| Key                   | Type      | Description |
|-----------------------|-----------|-------------|
| `connected`           | `boolean` | Always `true` when this response is returned. A `401` HTTP error is raised instead if OAuth authentication fails in live mode. |
| `mode`                | `string`  | `"demo"` when `NS_ACCOUNT_ID` is not configured; `"live"` when connected to a real NetSuite account. Present on all endpoint responses. |
| `message`             | `string`  | Human-readable explanation of the current mode with instructions for switching to live mode. Only present in `"demo"` mode. |
| `modules_count`       | `integer` | Total number of NetSuite functional modules in the demo data (Accounting, Customers & CRM, Vendors & Purchasing, Inventory, Sales, Employees & HR, Projects). Only present in `"demo"` mode. |
| `total_record_types`  | `integer` | Total count of Record Types (tables) across all modules in the demo data. Only present in `"demo"` mode. In live mode, this reflects the count of record types in the Metadata Catalog of the connected account. |
| `total_fields`        | `integer` | Total number of fields across all demo record types. Gives a broad sense of schema coverage. Only present in `"demo"` mode. |

### Live Mode Response Fields

| Key                  | Type      | Description |
|----------------------|-----------|-------------|
| `connected`          | `boolean` | Always `true` on a successful live response. |
| `mode`               | `string`  | Always `"live"` when a real NetSuite account is connected. |
| `account_id`         | `string`  | The NetSuite Account ID from `NS_ACCOUNT_ID` in `.env` (e.g. `"1234567"`). Visible in the NetSuite URL: `https://{account_id}.app.netsuite.com`. Used to construct all API base URLs. |
| `total_record_types` | `integer` | Count of record types returned from the live `/metadata-catalog/` endpoint — represents the total number of record types accessible with the configured credentials (typically 200–300+ in a standard NetSuite account). |

---

## 2. GET /api/v1/netsuite/modules

Lists all NetSuite functional modules. Both demo and live mode return the same 7 module definitions (NetSuite's REST API does not expose a dynamic module-listing endpoint — modules are a logical grouping in this backend).

**Example Response**

```json
{
  "total": 7,
  "modules": [
    {
      "id": "accounting",
      "label": "Accounting",
      "description": "Chart of Accounts, Journal Entries, Accounting Periods, Budgets",
      "records_count": 2
    }
  ]
}
```

---

### 2.1 Top-Level Response

| Key       | Type            | Description |
|-----------|-----------------|-------------|
| `total`   | `integer`       | Total number of modules returned. |
| `modules` | `array<object>` | List of module descriptors. Each entry represents one NetSuite functional area. See [2.2](#22-each-module-entry-inside-modules-array). |

---

### 2.2 Each Module Entry (inside `modules` array)

| Key             | Type      | Description |
|-----------------|-----------|-------------|
| `id`            | `string`  | The **module identifier** used as the `{module_id}` path parameter in `/modules/{module_id}/records` (e.g. `"accounting"`, `"customers"`, `"vendors"`, `"inventory"`, `"sales"`, `"employees"`, `"projects"`). Lowercase, no spaces. |
| `label`         | `string`  | The **human-readable display name** of the module (e.g. `"Accounting"`, `"Customers & CRM"`, `"Vendors & Purchasing"`). |
| `description`   | `string`  | Brief summary of what business area and Record Types this module covers (e.g. `"Chart of Accounts, Journal Entries, Accounting Periods, Budgets"`). |
| `records_count` | `integer` | Number of Record Types (tables) available within this module in the demo data. |

---

## 3. GET /api/v1/netsuite/modules/{module_id}/records

Returns a lightweight summary list of all Record Types within a specific NetSuite module — without full field details.

**Path Parameter**

| Parameter   | Type     | Description |
|-------------|----------|-------------|
| `module_id` | `string` | The module identifier from the `id` field in `/modules` (e.g. `accounting`, `customers`, `sales`). |

**Example Response**

```json
{
  "module_id": "customers",
  "module_label": "Customers & CRM",
  "total": 3,
  "mode": "demo",
  "records": [
    {
      "name": "customer",
      "label": "Customer",
      "description": "Customer master records",
      "fields_count": 15
    }
  ]
}
```

---

### 3.1 Top-Level Response

| Key            | Type            | Description |
|----------------|-----------------|-------------|
| `module_id`    | `string`        | Echoes back the `{module_id}` path parameter. Confirms which module's records are returned. |
| `module_label` | `string`        | Human-readable label of the module (e.g. `"Customers & CRM"`, `"Sales Transactions"`). |
| `total`        | `integer`       | Total number of Record Types returned for this module. |
| `mode`         | `string`        | `"demo"` or `"live"`. |
| `records`      | `array<object>` | Summary list of Record Type descriptors. See [3.2](#32-each-record-summary-entry-inside-records-array). |

---

### 3.2 Each Record Summary Entry (inside `records` array)

| Key            | Type      | Description |
|----------------|-----------|-------------|
| `name`         | `string`  | The **Record Type name** used as the `{record_type}` path parameter in `/records/{record_type}/fields` and in live Metadata Catalog API calls (e.g. `"customer"`, `"salesOrder"`, `"inventoryItem"`, `"journalEntry"`). CamelCase for multi-word names. This is also the path segment used in live data queries: `GET /services/rest/record/v1/salesOrder`. |
| `label`        | `string`  | The **human-readable display name** for this Record Type as shown in the NetSuite UI (e.g. `"Customer"`, `"Sales Order"`, `"Inventory Item"`). |
| `description`  | `string`  | Plain-English description of what business data this Record Type holds (e.g. `"Customer master records"`, `"Customer sales orders"`, `"Physical inventory items tracked in stock"`). |
| `fields_count` | `integer` | Number of fields defined on this Record Type in the metadata. |

---

## 4. GET /api/v1/netsuite/records

Returns a **flat list of all Record Types across every module** in one call. Useful for a global overview, search across all types, or when the module is unknown.

**Example Response**

```json
{
  "total": 13,
  "mode": "demo",
  "records": [
    {
      "name": "customer",
      "label": "Customer",
      "module": "customers",
      "description": "Customer master records",
      "fields_count": 15
    }
  ]
}
```

### Response Fields

| Key       | Type            | Description |
|-----------|-----------------|-------------|
| `total`   | `integer`       | Total count of all Record Types across all modules. |
| `mode`    | `string`        | `"demo"` or `"live"`. |
| `records` | `array<object>` | Flat list of all Record Types. Same structure as [3.2](#32-each-record-summary-entry-inside-records-array) with one additional field: |

**Additional field (only in the flat list):**

| Key      | Type     | Description |
|----------|----------|-------------|
| `module` | `string` | The `id` of the NetSuite module this Record Type belongs to (e.g. `"accounting"`, `"customers"`, `"sales"`). Included because this list spans all modules — use it for grouping or filtering in a UI. |

---

## 5. GET /api/v1/netsuite/records/{record_type}/fields

Returns **complete field-level metadata** for one NetSuite Record Type — all field definitions with types, read/write permissions, nullability, and reference (foreign key) targets. In live mode this calls the real NetSuite REST Metadata Catalog: `GET /services/rest/record/v1/metadata-catalog/{recordType}`.

This is the NetSuite equivalent of:
- Salesforce: `GET /api/v1/salesforce/objects/{name}/metadata`
- SAP: `GET /api/v1/sap/services/{service}/entities/{entity}/fields`
- Oracle: `GET /api/v1/oracle/resources/{resource}/describe`
- Workday: `GET /api/v1/workday/objects/{object}/describe`
- ServiceNow: `GET /api/v1/servicenow/tables/{table}/fields`

**Path Parameter**

| Parameter     | Type     | Description |
|---------------|----------|-------------|
| `record_type` | `string` | The Record Type name (e.g. `customer`, `salesOrder`, `inventoryItem`, `journalEntry`, `employee`, `job`). Must match a `name` from the records list. |

**Example Response**

```json
{
  "name": "salesOrder",
  "label": "Sales Order",
  "module": "sales",
  "description": "Customer sales orders",
  "fields_count": 11,
  "mode": "demo",
  "fields": [
    {
      "name": "id",
      "label": "Internal ID",
      "type": "integer",
      "nullable": false,
      "readOnly": true,
      "is_key": true,
      "referenceType": null,
      "description": "Internal NetSuite ID"
    },
    {
      "name": "entity",
      "label": "Customer",
      "type": "select",
      "nullable": false,
      "readOnly": false,
      "is_key": false,
      "referenceType": "customer",
      "description": "Customer placing the order"
    },
    {
      "name": "status",
      "label": "Status",
      "type": "enum",
      "nullable": false,
      "readOnly": true,
      "is_key": false,
      "referenceType": null,
      "description": "Pending Approval, Pending Fulfillment, Partially Fulfilled, Closed, Cancelled"
    }
  ]
}
```

---

### 5.1 Top-Level Response

| Key            | Type            | Description |
|----------------|-----------------|-------------|
| `name`         | `string`        | The Record Type name as used in the URL path. |
| `label`        | `string`        | Human-readable display name (e.g. `"Sales Order"`, `"Inventory Item"`, `"Journal Entry"`). In live mode, sourced from the `title` field of the Metadata Catalog response. |
| `module`       | `string`        | The `id` of the NetSuite module this Record Type belongs to (e.g. `"sales"`, `"accounting"`). Empty string in live mode (module grouping is not returned by the Metadata Catalog API). |
| `description`  | `string`        | Plain-English description of this Record Type's business purpose. May be empty in live mode if not defined in the catalog. |
| `fields_count` | `integer`       | Total number of fields returned for this Record Type. |
| `mode`         | `string`        | `"demo"` or `"live"`. |
| `fields`       | `array<object>` | Complete list of field descriptors. Each entry describes one column. See [5.2](#52-each-field-entry-inside-fields-array). |

---

### 5.2 Each Field Entry (inside `fields` array)

| Key             | Type               | Description |
|-----------------|--------------------|-------------|
| `name`          | `string`           | The **internal field name** as used in NetSuite REST API JSON payloads and Metadata Catalog responses (e.g. `"id"`, `"tranId"`, `"entity"`, `"acctType"`, `"postingPeriod"`). CamelCase convention. This is the key used in `GET` responses and `POST`/`PATCH` request bodies when creating or updating records via the live REST API. |
| `label`         | `string`           | The **human-readable display label** shown in the NetSuite UI (e.g. `"Internal ID"`, `"Customer"`, `"Account Type"`, `"Posting Period"`). Sourced from the `title` field in the JSON Schema Metadata Catalog response. Use this for UI column headers and form labels. |
| `type`          | `string`           | The **field data type** from the NetSuite Metadata Catalog. Determines how the value is stored, validated, and serialized. See the [Field Type Reference](#6-field-type-reference) for all values (`"string"`, `"integer"`, `"float"`, `"boolean"`, `"date"`, `"dateTime"`, `"select"`, `"enum"`). |
| `nullable`      | `boolean`          | Whether this field **accepts `null` (empty) values**. `false` = the field is required and must have a value; `true` = the field is optional. Directly equivalent to Salesforce's `nillable` and SAP's `Nullable` attribute. |
| `readOnly`      | `boolean`          | Whether this field's value **can be set or changed via the API**. `true` = the field is system-managed and cannot be written to (e.g. `id`, `balance`, `total`, `status` on transactional records, `dateCreated`). `false` = the field is user-writable in `POST`/`PATCH` requests. |
| `is_key`        | `boolean`          | Whether this field is the **primary key** of the Record Type. `true` only for the `id` field — a system-assigned positive integer that uniquely identifies every NetSuite record. Used in record-specific URL paths: `GET /services/rest/record/v1/customer/{id}`. |
| `referenceType` | `string \| null`   | For `"select"` type fields: the **name of the Record Type this field references** (e.g. `"customer"`, `"employee"`, `"currency"`, `"subsidiary"`, `"term"`, `"department"`). This is how NetSuite implements foreign keys — a `select` field stores the `id` of a record in the referenced Record Type. `null` for all non-reference fields. See [Section 8](#8-common-netsuite-reference-types) for common reference types. |
| `description`   | `string`           | A plain-English explanation of what this field represents and how it is used. For coded `enum` and `select` fields, may include the valid value options (e.g. `"Bank, AccountsReceivable, AccountsPayable, Income, Expense, etc."` for `acctType`). |

---

## 6. Field Type Reference

NetSuite REST Metadata Catalog uses JSON Schema-style types. Unlike SAP's verbose EDM types, these are concise and JSON-native.

| `type`       | Description |
|--------------|-------------|
| `string`     | A plain text value. Used for names, IDs, descriptions, memos, phone numbers, emails, and any free-form text. The most common type. |
| `integer`    | A whole number. Used for the primary key `id` field on every Record Type — NetSuite uses auto-incremented positive integers as internal IDs, unlike the GUIDs used by Salesforce or ServiceNow. |
| `float`      | A decimal number. Used for monetary amounts (`total`, `balance`, `creditLimit`, `rate`, `cost`), quantities (`quantityOnHand`, `reorderPoint`), and percentages (`probability`). May include fractional values. |
| `boolean`    | A `true`/`false` value. Serialized as JSON `true` or `false`. Used for flag fields like `isInactive` (on customers, vendors, employees, items, accounts), `isBookSpecific` (on journal entries). |
| `date`       | A calendar date with no time component. Serialized as `YYYY-MM-DD` (e.g. `"2024-01-15"`). Used for transaction dates (`tranDate`), due dates (`dueDate`), hire dates (`hireDate`), and ship dates (`shipDate`). |
| `dateTime`   | A date + time value. Serialized as an ISO 8601 string with timezone (e.g. `"2024-01-15T10:30:00.000Z"`). Used for system-managed timestamps: `createdDate`, `lastModifiedDate`, `dateCreated`. |
| `select`     | A **reference / foreign key** field pointing to another Record Type. Stores the `id` of a linked record. The `referenceType` field names the target Record Type (e.g. `"customer"`, `"employee"`, `"currency"`). In Metadata Catalog responses, `select` fields include a schema reference (`$ref`) to the related record type's schema. |
| `enum`       | An **enumeration** field with a fixed set of allowed string values defined in NetSuite. Used for status fields and classification fields where values are set by NetSuite business logic (e.g. `acctType`: `"Bank"`, `"AccountsReceivable"`, `"Income"`, `"Expense"`; `status` on Sales Orders: `"Pending Approval"`, `"Closed"`, etc.). Unlike `select`, enum values are not records — they are hard-coded strings. |
| `array`      | A list/multi-value field. Used for sublists (the NetSuite term for line-item sections like order lines, journal lines, etc.) when they are embedded in the parent record's schema. |

---

## 7. Module & Record Type Reference

All 7 NetSuite modules and their 13 Record Types available in this backend.

### Accounting
*Chart of Accounts, Journal Entries, Accounting Periods, Budgets*

| Record Type      | Label          | Key Field | Notable Fields |
|------------------|----------------|-----------|----------------|
| `account`        | Account        | `id`      | `acctNumber`, `acctName`, `acctType`, `currency`, `parent`, `balance`, `isInactive` |
| `journalEntry`   | Journal Entry  | `id`      | `tranId`, `tranDate`, `postingPeriod`, `subsidiary`, `currency`, `memo`, `isBookSpecific` |

### Customers & CRM
*Customers, Contacts, Leads, Prospects, Cases*

| Record Type    | Label       | Key Field | Notable Fields |
|----------------|-------------|-----------|----------------|
| `customer`     | Customer    | `id`      | `entityId`, `companyName`, `email`, `phone`, `subsidiary`, `currency`, `salesRep`, `creditLimit`, `balance`, `isInactive` |
| `contact`      | Contact     | `id`      | `entityId`, `salutation`, `firstName`, `lastName`, `title`, `email`, `company` |
| `opportunity`  | Opportunity | `id`      | `tranId`, `title`, `entity`, `status`, `probability`, `projectedTotal`, `expectedCloseDate`, `salesRep` |

### Vendors & Purchasing
*Vendors, Bills, Purchase Orders, Payments*

| Record Type     | Label          | Key Field | Notable Fields |
|-----------------|----------------|-----------|----------------|
| `vendor`        | Vendor         | `id`      | `entityId`, `companyName`, `email`, `currency`, `terms`, `taxIdNum`, `balance`, `isInactive` |
| `purchaseOrder` | Purchase Order | `id`      | `tranId`, `tranDate`, `entity`, `status`, `total`, `currency`, `memo`, `shipDate` |

### Inventory & Items
*Inventory Items, Assemblies, Item Groups, Pricing*

| Record Type     | Label          | Key Field | Notable Fields |
|-----------------|----------------|-----------|----------------|
| `inventoryItem` | Inventory Item | `id`      | `itemId`, `displayName`, `description`, `rate`, `cost`, `quantityOnHand`, `reorderPoint`, `unitsType`, `isInactive` |

### Sales Transactions
*Sales Orders, Estimates, Item Fulfillments, Invoices*

| Record Type  | Label       | Key Field | Notable Fields |
|--------------|-------------|-----------|----------------|
| `salesOrder` | Sales Order | `id`      | `tranId`, `tranDate`, `entity`, `status`, `total`, `currency`, `salesRep`, `shipDate`, `terms` |
| `invoice`    | Invoice     | `id`      | `tranId`, `tranDate`, `dueDate`, `entity`, `status`, `total`, `amountRemaining`, `currency`, `terms` |

### Employees & HR
*Employees, Departments, Jobs, Payroll Items*

| Record Type  | Label      | Key Field | Notable Fields |
|--------------|------------|-----------|----------------|
| `employee`   | Employee   | `id`      | `entityId`, `firstName`, `lastName`, `email`, `title`, `department`, `subsidiary`, `supervisor`, `hireDate`, `releaseDate`, `isInactive` |
| `department` | Department | `id`      | `name`, `parent`, `subsidiary`, `isInactive` |

### Projects
*Projects, Project Tasks, Time Entries, Expenses*

| Record Type | Label   | Key Field | Notable Fields |
|-------------|---------|-----------|----------------|
| `job`       | Project | `id`      | `entityId`, `companyName`, `customer`, `status`, `startDate`, `endDate`, `estimatedCost`, `estimatedRevenue`, `isInactive` |

> **Note:** NetSuite calls projects "Jobs" internally (`job` is the Record Type name), while the UI displays them as "Projects".

---

## 8. Common NetSuite Reference Types

When a field has `"type": "select"`, the `referenceType` value names the linked Record Type. These are the most commonly referenced built-in NetSuite record types:

| `referenceType`    | What it points to |
|--------------------|-------------------|
| `customer`         | A Customer record (`/records/customer`) |
| `vendor`           | A Vendor record (`/records/vendor`) |
| `employee`         | An Employee record (`/records/employee`) |
| `account`          | A General Ledger Account (`/records/account`) |
| `department`       | A Department record (`/records/department`) |
| `subsidiary`       | A NetSuite Subsidiary (legal entity in a multi-company setup) — not exposed as its own module but referenced widely |
| `currency`         | A Currency record (e.g. USD, EUR) — system-managed |
| `term`             | A Payment Terms record (e.g. Net 30, Net 60) — system-managed |
| `accountingPeriod` | An Accounting Period (e.g. January 2024) — system-managed |
| `unitsType`        | A Units of Measure type (e.g. Weight, Volume) — used on Inventory Items |
| `jobStatus`        | A Project Status record — used on `job` (Project) Record Type |

---

*Generated from backend source: `backend/netsuite/service.py` — `test_connection()`, `list_modules()`, `get_module_records()`, `get_all_records()`, and `get_record_fields()`*

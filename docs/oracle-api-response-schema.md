# Oracle Fusion Cloud ERP API — Response Schema Documentation

This document describes every key-value pair returned by the Oracle Fusion ERP metadata endpoints exposed by this backend.

---

## Background — How Oracle Fusion Exposes Metadata

Oracle Fusion Cloud ERP uses **REST APIs** under the `/fscmRestApi/resources/latest/` path. Unlike SAP (EDMX XML) or Salesforce (describe API), Oracle exposes metadata through a `/describe` endpoint on each resource that returns JSON describing attributes and child relationships.

Oracle is also unique in that it is **module-organized** — resources (tables) are grouped into functional business modules such as Financials, Procurement, HCM, etc.

**Key concept mapping:**

| Traditional DB     | Salesforce        | SAP               | HubSpot    | Oracle Fusion              |
|--------------------|-------------------|-------------------|------------|----------------------------|
| Database / Schema  | Org               | System / Landscape| Portal     | Cloud Instance             |
| Schema / Domain    | —                 | OData Service     | —          | **Module**                 |
| Table              | SObject           | EntityType        | Object     | **Resource**               |
| Column / Field     | Field             | Property          | Property   | **Attribute**              |
| Row                | Record            | Entity            | Record     | **Record**                 |
| Foreign Key / Join | Relationship      | NavigationProperty| Association| **Child Resource**         |
| Primary Key        | Id (18-char)      | Key Property      | id         | **Key Attribute** (`is_key`)|

**Two operating modes:**
- **Demo Mode** — when `ORACLE_BASE_URL` is not set in `.env`, the backend returns built-in metadata modelled on the real Oracle Fusion ERP schema. No Oracle subscription needed.
- **Live Mode** — when `ORACLE_BASE_URL`, `ORACLE_USERNAME`, and `ORACLE_PASSWORD` are configured, metadata is fetched directly from a real Oracle Cloud instance via the `/describe` REST endpoint.

---

## Table of Contents

1. [GET /api/v1/oracle/connect](#1-get-apiv1oracleconnect)
2. [GET /api/v1/oracle/modules](#2-get-apiv1oraclemodules)
   - [Top-Level Response](#21-top-level-response)
   - [Each Module Entry](#22-each-module-entry-inside-modules-array)
3. [GET /api/v1/oracle/modules/{module_id}/resources](#3-get-apiv1oraclemodulesmodule_idresources)
   - [Top-Level Response](#31-top-level-response)
   - [Each Resource Summary Entry](#32-each-resource-summary-entry-inside-resources-array)
4. [GET /api/v1/oracle/resources](#4-get-apiv1oracleresources)
5. [GET /api/v1/oracle/resources/{resource_name}/describe](#5-get-apiv1oracleresourcesresource_namedescribe)
   - [Top-Level Response](#51-top-level-response)
   - [Each Attribute Entry](#52-each-attribute-entry-inside-attributes-array)
   - [Each Child Resource Entry](#53-each-entry-inside-children-array)
6. [Attribute Type Reference](#6-attribute-type-reference)
7. [Module & Resource Reference](#7-module--resource-reference)

---

## 1. GET /api/v1/oracle/connect

Tests Oracle Fusion ERP connectivity. In Demo Mode returns schema summary; in Live Mode fetches the root resource list from the Oracle REST API.

**Authentication:** HTTP Basic Auth — `ORACLE_USERNAME` + `ORACLE_PASSWORD` (Oracle Cloud login credentials).

**Demo Mode Response (no credentials configured)**

```json
{
  "connected": true,
  "mode": "demo",
  "message": "Running in Demo Mode — showing real Oracle Fusion ERP schema structure. Set ORACLE_BASE_URL, ORACLE_USERNAME, ORACLE_PASSWORD in .env to connect to a real Oracle Cloud instance.",
  "modules_count": 6,
  "total_resources": 11,
  "oracle_api_path": "/fscmRestApi/resources/latest"
}
```

**Live Mode Response (real Oracle Cloud connected)**

```json
{
  "connected": true,
  "mode": "live",
  "base_url": "https://abc-test.fa.oc1.oraclecloud.com",
  "items_count": 245
}
```

---

### Demo Mode Response Fields

| Key               | Type      | Description |
|-------------------|-----------|-------------|
| `connected`       | `boolean` | Always `true` when this response is returned. A `401` HTTP error is raised instead if authentication fails in live mode. |
| `mode`            | `string`  | Indicates which operating mode is active: `"demo"` when no `ORACLE_BASE_URL` is set, `"live"` when a real Oracle instance is configured. All other endpoints also include this field. |
| `message`         | `string`  | A human-readable explanation of the current mode and instructions for switching to live mode. Only present in `"demo"` mode. |
| `modules_count`   | `integer` | Total number of ERP functional modules available in the demo data (e.g. Financials, Procurement, HCM). Only present in `"demo"` mode. |
| `total_resources` | `integer` | Total count of resources (tables/business objects) across all modules in demo data. Only present in `"demo"` mode. |
| `oracle_api_path` | `string`  | The REST API base path used for all Oracle resource requests: `/fscmRestApi/resources/latest`. This is the standard Oracle Fusion Cloud ERP REST API root path. Only present in `"demo"` mode. |

### Live Mode Response Fields

| Key           | Type      | Description |
|---------------|-----------|-------------|
| `connected`   | `boolean` | Always `true` in a successful live response. |
| `mode`        | `string`  | Always `"live"` when connected to a real Oracle Cloud instance. |
| `base_url`    | `string`  | The Oracle Cloud instance hostname configured in `ORACLE_BASE_URL` (e.g. `"https://abc-test.fa.oc1.oraclecloud.com"`). |
| `items_count` | `integer` | Number of top-level resource items returned by the Oracle REST API root endpoint. Indicates how many resource groups are accessible with the configured credentials. |

---

## 2. GET /api/v1/oracle/modules

Lists all Oracle ERP functional modules. In Demo Mode these are the 6 built-in modules. In Live Mode these are the top-level resource groups from the Oracle Fusion REST API.

**Example Response**

```json
{
  "total": 6,
  "modules": [
    {
      "id": "financials",
      "label": "Financials",
      "description": "Accounts Payable, Accounts Receivable, General Ledger, Fixed Assets, Cash Management",
      "resources_count": 3
    }
  ]
}
```

---

### 2.1 Top-Level Response

| Key       | Type            | Description |
|-----------|-----------------|-------------|
| `total`   | `integer`       | Total number of modules returned. |
| `modules` | `array<object>` | List of module descriptors. Each entry represents one functional business domain within Oracle Fusion ERP. See [2.2](#22-each-module-entry-inside-modules-array). |

---

### 2.2 Each Module Entry (inside `modules` array)

| Key               | Type      | Description |
|-------------------|-----------|-------------|
| `id`              | `string`  | The **module identifier** used as the `{module_id}` path parameter in `/modules/{module_id}/resources` (e.g. `"financials"`, `"procurement"`, `"hcm"`, `"orderManagement"`, `"projects"`, `"supplyChain"`). Camel-case, no spaces. |
| `label`           | `string`  | The **human-readable name** of the module displayed in the UI (e.g. `"Financials"`, `"Human Capital Management"`, `"Supply Chain Management"`). |
| `description`     | `string`  | A brief description of the Oracle ERP functional area covered by this module, listing the major sub-applications included (e.g. `"Accounts Payable, Accounts Receivable, General Ledger, Fixed Assets, Cash Management"`). |
| `resources_count` | `integer` | Number of resources (tables/business objects) available within this module. Useful for displaying a badge count in the UI without fetching the full resource list. |

---

## 3. GET /api/v1/oracle/modules/{module_id}/resources

Returns all resources (tables/business objects) within a specific Oracle ERP module, as a lightweight summary without full attribute details.

**Path Parameter**

| Parameter   | Type     | Description |
|-------------|----------|-------------|
| `module_id` | `string` | The module identifier from the `id` field in the `/modules` response (e.g. `financials`, `procurement`, `hcm`). |

**Example Response**

```json
{
  "module_id": "financials",
  "module_label": "Financials",
  "total": 3,
  "mode": "demo",
  "resources": [
    {
      "name": "invoices",
      "title": "AP Invoices",
      "description": "Supplier invoices in Accounts Payable",
      "attributes_count": 15,
      "children_count": 2
    }
  ]
}
```

---

### 3.1 Top-Level Response

| Key            | Type            | Description |
|----------------|-----------------|-------------|
| `module_id`    | `string`        | Echoes back the `{module_id}` path parameter. Confirms which module's resources are returned. |
| `module_label` | `string`        | The human-readable label of the module (e.g. `"Financials"`, `"Procurement"`). |
| `total`        | `integer`       | Total number of resources returned for this module. |
| `mode`         | `string`        | `"demo"` or `"live"` — indicates whether the response comes from built-in demo metadata or a live Oracle Cloud instance. |
| `resources`    | `array<object>` | Lightweight list of resource descriptors within this module. See [3.2](#32-each-resource-summary-entry-inside-resources-array). |

---

### 3.2 Each Resource Summary Entry (inside `resources` array)

| Key                | Type      | Description |
|--------------------|-----------|-------------|
| `name`             | `string`  | The **resource name** — used as the `{resource_name}` path parameter in `/resources/{resource_name}/describe` (e.g. `"invoices"`, `"purchaseOrders"`, `"workers"`). Camel-case, matches the Oracle Fusion REST API path segment. |
| `title`            | `string`  | The **human-readable display name** for this resource (e.g. `"AP Invoices"`, `"Purchase Orders"`, `"Workers / Employees"`). Used in UI lists, breadcrumbs, and column headers. |
| `description`      | `string`  | A brief plain-English explanation of what business data this resource holds (e.g. `"Supplier invoices in Accounts Payable"`). |
| `attributes_count` | `integer` | Number of attributes (fields/columns) defined on this resource. Gives a quick sense of schema complexity without fetching full field details. |
| `children_count`   | `integer` | Number of child resources (nested sub-tables) associated with this resource. For example, `invoices` has 2 children: `invoiceLines` and `invoicePayments`. |

---

## 4. GET /api/v1/oracle/resources

Returns a **flat list of all resources across every module** in one call. Useful for global search, overview dashboards, or when you need to find a resource without knowing which module it belongs to.

**Example Response**

```json
{
  "total": 11,
  "mode": "demo",
  "resources": [
    {
      "name": "invoices",
      "title": "AP Invoices",
      "module": "financials",
      "description": "Supplier invoices in Accounts Payable",
      "attributes_count": 15,
      "children_count": 2
    }
  ]
}
```

---

### Response Fields

| Key         | Type            | Description |
|-------------|-----------------|-------------|
| `total`     | `integer`       | Total count of all resources across all modules. |
| `mode`      | `string`        | `"demo"` or `"live"`. |
| `resources` | `array<object>` | Flat list of all resources. Same structure as the per-module list ([3.2](#32-each-resource-summary-entry-inside-resources-array)) with one additional field: |

**Additional field (only in this flat list):**

| Key      | Type     | Description |
|----------|----------|-------------|
| `module` | `string` | The `id` of the module this resource belongs to (e.g. `"financials"`, `"procurement"`, `"hcm"`). Included here because the flat list spans all modules, so this field is needed to know which module a resource belongs to. |

---

## 5. GET /api/v1/oracle/resources/{resource_name}/describe

Returns **complete metadata** for one Oracle Fusion ERP resource — all attributes (fields) with full type/constraint information, plus child resource (sub-table) links.

**Path Parameter**

| Parameter       | Type     | Description |
|-----------------|----------|-------------|
| `resource_name` | `string` | The resource name from the `name` field in the resources list (e.g. `invoices`, `purchaseOrders`, `workers`, `salesOrders`). |

**Example Response**

```json
{
  "name": "invoices",
  "title": "AP Invoices",
  "module": "financials",
  "description": "Supplier invoices in Accounts Payable",
  "attributes_count": 15,
  "children_count": 2,
  "mode": "demo",
  "attributes": [
    {
      "name": "InvoiceId",
      "title": "Invoice ID",
      "type": "integer",
      "required": true,
      "queryable": true,
      "updatable": false,
      "is_key": true,
      "max_length": null
    },
    {
      "name": "InvoiceNumber",
      "title": "Invoice Number",
      "type": "string",
      "required": true,
      "queryable": true,
      "updatable": true,
      "is_key": false,
      "max_length": 50
    }
  ],
  "children": [
    {
      "name": "invoiceLines",
      "title": "Invoice Lines",
      "description": "Line items on an AP Invoice"
    }
  ]
}
```

---

### 5.1 Top-Level Response

| Key                | Type            | Description |
|--------------------|-----------------|-------------|
| `name`             | `string`        | The resource name as used in the URL path parameter. |
| `title`            | `string`        | The human-readable display title for this resource (e.g. `"AP Invoices"`, `"Workers / Employees"`). |
| `module`           | `string`        | The `id` of the Oracle ERP module this resource belongs to (e.g. `"financials"`, `"hcm"`). Used for breadcrumb navigation in the UI. |
| `description`      | `string`        | Plain-English description of what business data this resource represents. |
| `attributes_count` | `integer`       | Total number of attributes (fields) in this resource. |
| `children_count`   | `integer`       | Total number of child resources (nested sub-tables) associated with this resource. |
| `mode`             | `string`        | `"demo"` or `"live"` — indicates the data source. |
| `attributes`       | `array<object>` | Complete list of attribute (field) descriptors. Each entry fully describes one column. See [5.2](#52-each-attribute-entry-inside-attributes-array). |
| `children`         | `array<object>` | List of child resource links — nested sub-tables accessible from this resource. See [5.3](#53-each-entry-inside-children-array). |

---

### 5.2 Each Attribute Entry (inside `attributes` array)

| Key          | Type               | Description |
|--------------|--------------------|-------------|
| `name`       | `string`           | The **API attribute name** used in Oracle REST API requests and responses (e.g. `"InvoiceId"`, `"InvoiceNumber"`, `"SupplierId"`). PascalCase convention. This is the key used in JSON payloads when creating/updating records, and in query filter parameters. |
| `title`      | `string`           | The **human-readable display label** for this attribute as shown in the Oracle Fusion UI (e.g. `"Invoice ID"`, `"Invoice Number"`, `"Supplier Name"`). May differ from `name` — use this for UI column headers and form labels. |
| `type`       | `string`           | The **data type** of the attribute value. Determines how the value is stored, validated, and rendered. See the [Attribute Type Reference](#6-attribute-type-reference) for all possible values (`"string"`, `"integer"`, `"number"`, `"boolean"`). |
| `required`   | `boolean`          | Whether this attribute **must have a value** when creating a new record. `true` = mandatory field; `false` = optional. Required attributes will cause a validation error if omitted in a `POST` request to the Oracle REST API. |
| `queryable`  | `boolean`          | Whether this attribute can be used in **REST query parameters** to filter records (e.g. `?q=InvoiceNumber=INV-001`). `false` for computed fields, large text fields, or attributes not indexed for querying in Oracle. |
| `updatable`  | `boolean`          | Whether the value of this attribute can be **changed on an existing record** via a `PATCH` or `PUT` request. `false` for system-managed fields like primary keys (`InvoiceId`), creation dates (`CreationDate`), and derived values (`SupplierName` when set via `SupplierId`). |
| `is_key`     | `boolean`          | Whether this attribute is the **primary key** of the resource. `true` for the unique identifier field (e.g. `InvoiceId`, `POHeaderId`, `PersonId`). Used when constructing single-record Oracle REST URLs (e.g. `GET /invoices/10001`). Each resource has exactly one key attribute. |
| `max_length` | `integer \| null`  | For `"string"` type attributes, the **maximum allowed character length** (e.g. `50` for `InvoiceNumber`, `360` for `SupplierName`). `null` for non-string types (`integer`, `number`, `boolean`) where character length is not applicable. |

---

### 5.3 Each Entry (inside `children` array)

Child resources are **nested sub-tables** accessible via a sub-path on the parent resource. They represent a one-to-many relationship — one parent record has multiple child records (e.g. one Invoice has many Invoice Lines).

| Key           | Type     | Description |
|---------------|----------|-------------|
| `name`        | `string` | The **child resource name** — the URL path segment used to access this sub-table from the parent (e.g. `"invoiceLines"`, `"invoicePayments"`, `"supplierAddresses"`). To query child records, append this to the parent resource URL: `GET /invoices/{InvoiceId}/invoiceLines`. |
| `title`       | `string` | The **human-readable display name** for this child resource (e.g. `"Invoice Lines"`, `"Invoice Payments"`, `"Supplier Addresses"`). Used in UI sub-tabs and nested table headers. |
| `description` | `string` | A brief description of what data this child resource holds and its relationship to the parent (e.g. `"Line items on an AP Invoice"`, `"Payment records for an invoice"`). May be an empty string for live mode responses where Oracle does not return a description. |

---

## 6. Attribute Type Reference

Oracle Fusion ERP REST APIs use a simplified set of JSON-native types for attribute values. Unlike SAP's verbose EDM types, Oracle uses only 4 primitive types.

| `type`      | Description |
|-------------|-------------|
| `string`    | A text value. Used for names, codes, status values, dates (Oracle dates are returned as ISO 8601 strings, e.g. `"2024-01-15"`), and any free-form text field. `max_length` defines the character limit. The most common type in Oracle Fusion — covers everything from `InvoiceNumber` to `CurrencyCode` to `Status`. |
| `integer`   | A whole number with no decimal places. Used primarily for **surrogate key IDs** (e.g. `InvoiceId`, `SupplierId`, `PersonId`) and numeric foreign key references between resources. Values are exact with no rounding. |
| `number`    | A floating-point or fixed-decimal numeric value. Used for **monetary amounts** (e.g. `InvoiceAmount`, `OrderAmount`, `BudgetAmount`), quantities, and rates. May include decimal places. |
| `boolean`   | A `true` / `false` value. Used for flag attributes (e.g. `CostingEnabled`, `TrackingEnabled`). Serialized as JSON `true` or `false` (not as strings). |

> **Note on dates:** Oracle Fusion REST APIs return date and datetime values as `"string"` type in ISO 8601 format (e.g. `"2024-01-15"` for dates, `"2024-01-15T10:30:00+00:00"` for datetimes). There is no separate `date` or `datetime` type in the attribute metadata — the field naming convention (`CreationDate`, `InvoiceDate`, `HireDate`) is the indicator.

---

## 7. Module & Resource Reference

The 6 Oracle ERP modules and their resources available in this backend (demo and live mode).

### Financials
*Accounts Payable, Accounts Receivable, General Ledger, Fixed Assets, Cash Management*

| Resource                 | Title            | Key Attribute            | Children |
|--------------------------|------------------|--------------------------|----------|
| `invoices`               | AP Invoices      | `InvoiceId`              | `invoiceLines`, `invoicePayments` |
| `receivablesInvoices`    | AR Invoices      | `CustomerTransactionId`  | `receivablesInvoiceLines` |
| `generalLedgerJournals`  | GL Journals      | `JournalId`              | `generalLedgerJournalLines` |

### Procurement
*Purchase Orders, Suppliers, Purchasing Contracts, Requisitions*

| Resource         | Title           | Key Attribute  | Children |
|------------------|-----------------|----------------|----------|
| `purchaseOrders` | Purchase Orders | `POHeaderId`   | `purchaseOrderLines`, `purchaseOrderSchedules`, `purchaseOrderDistributions` |
| `suppliers`      | Suppliers       | `SupplierId`   | `supplierAddresses`, `supplierContacts`, `supplierSites` |

### Order Management
*Sales Orders, Customers, Pricing, Fulfillment*

| Resource             | Title        | Key Attribute  | Children |
|----------------------|--------------|----------------|----------|
| `salesOrders`        | Sales Orders | `OrderId`      | `salesOrderLines`, `fulfillmentLines` |
| `customers`          | Customers    | `PartyId`      | `customerAccounts`, `customerAddresses`, `customerContacts` |

### Human Capital Management (HCM)
*Employees, Jobs, Departments, Payroll, Absence*

| Resource      | Title                | Key Attribute    | Children |
|---------------|----------------------|------------------|----------|
| `workers`     | Workers / Employees  | `PersonId`       | `assignments`, `salaries`, `absences` |
| `departments` | Departments          | `DepartmentId`   | *(none)* |

### Project Management
*Projects, Tasks, Resources, Budgets, Costs*

| Resource   | Title    | Key Attribute | Children |
|------------|----------|---------------|----------|
| `projects` | Projects | `ProjectId`   | `tasks`, `projectResources`, `projectCosts` |

### Supply Chain Management
*Inventory, Items, Work Orders, Shipments*

| Resource         | Title            | Key Attribute      | Children |
|------------------|------------------|--------------------|----------|
| `inventoryItems` | Inventory Items  | `InventoryItemId`  | `itemRevisions`, `itemCategories` |

---

*Generated from backend source: `backend/oracle/service.py` — `test_connection()`, `list_modules()`, `get_module_resources()`, `get_all_resources()`, and `get_resource_describe()`*

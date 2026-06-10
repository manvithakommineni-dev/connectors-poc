# HubSpot API — Response Schema Documentation

This document describes every key-value pair returned by the four primary HubSpot endpoints exposed by this backend.

---

## Table of Contents

1. [GET /api/v1/hubspot/connect](#1-get-apiv1hubspotconnect)
2. [GET /api/v1/hubspot/objects](#2-get-apiv1hubspotobjects)
   - [Top-Level Response](#21-top-level-response)
   - [Each Object Entry](#22-each-object-entry-inside-objects-array)
3. [GET /api/v1/hubspot/objects/{object_type}/properties](#3-get-apiv1hubspotobjectsobject_typeproperties)
   - [Top-Level Response](#31-top-level-response)
   - [Each Property Entry](#32-each-property-entry-inside-properties-array)
4. [GET /api/v1/hubspot/objects/{object_type}/sample](#4-get-apiv1hubspotobjectsobject_typesample)
   - [Top-Level Response](#41-top-level-response)
   - [Each Record Entry](#42-each-record-entry-inside-records-array)
   - [Paging Object](#43-paging-object)
5. [Property Type & Field Type Reference](#5-property-type--field-type-reference)
6. [Standard Object Types Reference](#6-standard-object-types-reference)

---

## 1. GET /api/v1/hubspot/connect

Tests connectivity to HubSpot and returns account/portal information using the Personal Access Key (`HS_ACCESS_TOKEN`) configured in the backend `.env`.

**Authentication:** Personal Access Key (Bearer Token) — no browser login needed, unlike Salesforce OAuth.

**Example Response**

```json
{
  "connected": true,
  "portal_id": 12345678,
  "account_type": "MARKETING_HUB_ENTERPRISE",
  "time_zone": "America/New_York",
  "company_currency": "USD",
  "ui_domain": "app.hubspot.com",
  "data_hosting_location": "na1",
  "auth_method": "Personal Access Key (Bearer Token)"
}
```

---

### Response Fields

| Key                    | Type      | Description |
|------------------------|-----------|-------------|
| `connected`            | `boolean` | Always `true` when this response is returned. Confirms the token is valid and the HubSpot API is reachable. A `401` HTTP error is raised instead if authentication fails. |
| `portal_id`            | `integer` | The unique numeric identifier of the HubSpot portal (also called Hub ID). Every HubSpot account has exactly one portal ID. Used to scope API calls and identify the org in HubSpot's system. |
| `account_type`         | `string`  | The subscription tier and product hub of the connected account (e.g., `"MARKETING_HUB_ENTERPRISE"`, `"SALES_HUB_PROFESSIONAL"`, `"CRM_SUITE_STARTER"`). Determines which features and API endpoints are available. |
| `time_zone`            | `string`  | The IANA timezone configured for this portal (e.g., `"America/New_York"`, `"Europe/London"`). Dates/times returned by HubSpot APIs are interpreted in this timezone in the UI. |
| `company_currency`     | `string`  | The ISO 4217 currency code set as the primary currency for this portal (e.g., `"USD"`, `"EUR"`, `"GBP"`). Used as the default for all deal amounts and revenue properties. |
| `ui_domain`            | `string`  | The domain used to access this portal's HubSpot UI (e.g., `"app.hubspot.com"` for standard portals, or a custom domain for enterprise accounts). |
| `data_hosting_location`| `string`  | The data residency region where this portal's data is stored (e.g., `"na1"` = North America, `"eu1"` = Europe). Relevant for GDPR and data sovereignty compliance. |
| `auth_method`          | `string`  | A fixed descriptive label indicating how the backend authenticates with HubSpot. Always `"Personal Access Key (Bearer Token)"` for this connector. |

---

## 2. GET /api/v1/hubspot/objects

Lists all available CRM object types in the connected HubSpot portal — both standard built-in objects and any custom objects created in the portal.

> **Note:** HubSpot does not have a single API endpoint that lists all standard objects, so standard objects (`contacts`, `companies`, `deals`, etc.) are hardcoded in the backend. Custom objects are dynamically fetched from `/crm/v3/schemas`.

**Example Response**

```json
{
  "total": 14,
  "objects": [
    {
      "name": "contacts",
      "label": "Contacts",
      "object_type_id": "contacts",
      "type": "standard"
    },
    {
      "name": "my_custom_object",
      "label": "My Custom Object",
      "object_type_id": "2-8675309",
      "type": "custom"
    }
  ]
}
```

---

### 2.1 Top-Level Response

| Key       | Type            | Description |
|-----------|-----------------|-------------|
| `total`   | `integer`       | Total count of object types returned (standard + custom combined). |
| `objects` | `array<object>` | The list of all CRM object type descriptors. See [2.2](#22-each-object-entry-inside-objects-array) for the structure of each entry. |

---

### 2.2 Each Object Entry (inside `objects` array)

| Key              | Type                       | Description |
|------------------|----------------------------|-------------|
| `name`           | `string`                   | The **API name** used to reference this object in all other endpoint URL paths (e.g., `"contacts"`, `"deals"`, `"my_custom_object"`). This is the value to pass as `{object_type}` in `/properties`, `/schema`, and `/sample` endpoints. |
| `label`          | `string`                   | The **human-readable display name** for this object type. For standard objects, it is the title-cased version of the name (e.g., `"Line Items"`). For custom objects, it is the singular label configured in HubSpot. |
| `object_type_id` | `string`                   | The identifier HubSpot uses internally to reference this object type. For standard objects this is the same as `name` (e.g., `"contacts"`). For custom objects it is a numeric string in the format `"2-XXXXXXX"` (e.g., `"2-8675309"`). Used when building associations and schema relationships. |
| `type`           | `"standard"` \| `"custom"` | Whether this is a **built-in HubSpot object** (`"standard"`) or a **user-created custom object** (`"custom"`). Standard objects are always present in every HubSpot portal; custom objects depend on the account's subscription and configuration. |

---

## 3. GET /api/v1/hubspot/objects/{object_type}/properties

Returns all properties (fields/columns) defined for a given HubSpot object type. This is the HubSpot equivalent of Salesforce's field describe endpoint.

**Path Parameter**

| Parameter     | Type     | Description |
|---------------|----------|-------------|
| `object_type` | `string` | The API name of the object (e.g., `contacts`, `companies`, `deals`). Must match the `name` from the `/objects` list. |

**Example Response**

```json
{
  "object_type": "contacts",
  "properties_count": 172,
  "properties": [
    {
      "name": "firstname",
      "label": "First Name",
      "type": "string",
      "field_type": "text",
      "description": "A contact's first name.",
      "group_name": "contactinformation",
      "options": [],
      "created_at": null,
      "updated_at": "2024-01-15T10:30:00.000Z",
      "calculated": false,
      "external_options": false,
      "hidden": false,
      "hubspot_defined": true,
      "show_currency_symbol": false,
      "modification_metadata": {
        "archivable": true,
        "readOnlyDefinition": false,
        "readOnlyValue": false
      },
      "form_field": true
    }
  ]
}
```

---

### 3.1 Top-Level Response

| Key                | Type            | Description |
|--------------------|-----------------|-------------|
| `object_type`      | `string`        | Echoes back the `{object_type}` path parameter that was requested. Useful for confirming which object's properties are in the response. |
| `properties_count` | `integer`       | Total number of properties returned for this object. Standard objects like `contacts` typically have 100–200+ properties; custom objects have as many as defined by the portal admin. |
| `properties`       | `array<object>` | The complete list of property descriptors. Each entry fully describes one field/column of the object. See [3.2](#32-each-property-entry-inside-properties-array). |

---

### 3.2 Each Property Entry (inside `properties` array)

| Key                     | Type              | Description |
|-------------------------|-------------------|-------------|
| `name`                  | `string`          | The **API name** of the property. Used in API payloads, SOQL-equivalent filters, and as the key in record `properties` objects (e.g., `"firstname"`, `"hs_deal_stage"`, `"my_custom_prop__c"`). Custom properties created in the UI have snake_case names. |
| `label`                 | `string`          | The **human-readable display label** shown in HubSpot's UI forms, list views, and reports (e.g., `"First Name"`, `"Deal Stage"`). May differ significantly from `name`. |
| `type`                  | `string`          | The **data type** of the property value. Determines how the value is stored and validated. See the [Property Type Reference](#5-property-type--field-type-reference) for all possible values (e.g., `"string"`, `"number"`, `"bool"`, `"enumeration"`, `"date"`, `"datetime"`). |
| `field_type`            | `string`          | The **UI input widget type** used to render and edit this property in HubSpot forms and record views (e.g., `"text"`, `"select"`, `"checkbox"`, `"date"`, `"textarea"`, `"number"`). A property's `type` and `field_type` are related but distinct — `type` is the data model, `field_type` is the UI representation. |
| `description`           | `string`          | A plain-text explanation of what this property represents. HubSpot-defined properties have concise descriptions; custom properties may have empty strings if no description was provided during creation. |
| `group_name`            | `string`          | The **property group** this property belongs to. Properties are organized into groups for display in the UI sidebar (e.g., `"contactinformation"`, `"dealinformation"`, `"socialmediainformation"`). Useful for grouping properties in your own UI. |
| `options`               | `array<string>`   | For `enumeration` type properties (dropdowns, radio buttons, checkboxes), this is the list of allowed **option values** (e.g., `["new", "open", "in_progress", "closed"]`). Empty array for all non-enumeration types. |
| `created_at`            | `string \| null`  | ISO 8601 timestamp of when this property was **first created**. `null` for built-in HubSpot-defined properties that predate timestamp tracking. Custom properties always have a `created_at` value. |
| `updated_at`            | `string \| null`  | ISO 8601 timestamp of the **last modification** to this property's definition (label, options, description, etc.). `null` for properties that have never been modified since creation. |
| `calculated`            | `boolean`         | Whether this property's value is **automatically computed** by HubSpot rather than being set by a user or integration (e.g., `hs_email_last_open_date`, `num_associated_deals`). Calculated properties are read-only and cannot be written via API. |
| `external_options`      | `boolean`         | Whether the allowed values for this property are sourced from an **external system** (via a connected integration) rather than being a static list defined in HubSpot. When `true`, the `options` array may be empty even for enumeration-type properties. |
| `hidden`                | `boolean`         | Whether this property is **hidden from the standard HubSpot UI**. Hidden properties are not shown in record views or forms by default but are still accessible via the API. Often used for internal/technical fields. |
| `hubspot_defined`       | `boolean`         | Whether this property was **created and managed by HubSpot** (`true`) as part of the standard product, vs. being created by a portal admin or developer (`false`). HubSpot-defined properties cannot be deleted. |
| `show_currency_symbol`  | `boolean`         | For `number` type properties, whether the value should be **displayed with a currency symbol** in the UI (e.g., deal amount fields). Has no effect on non-numeric properties. |
| `modification_metadata` | `object`          | A nested object describing the **editability constraints** of this property. Contains: `archivable` (can be deleted/archived), `readOnlyDefinition` (can its metadata be changed), `readOnlyValue` (can its value be changed on records). All are `boolean`. |
| `form_field`            | `boolean`         | Whether this property can be **used in HubSpot forms** (landing page forms, pop-up forms, etc.) for data capture. `false` for internal system properties, calculated fields, and fields not suitable for form input. |

---

## 4. GET /api/v1/hubspot/objects/{object_type}/sample

Fetches a small set of real CRM records for a given object type. Returns actual record data with the first 10 properties of each record populated.

**Path Parameter**

| Parameter     | Type     | Description |
|---------------|----------|-------------|
| `object_type` | `string` | The API name of the object (e.g., `contacts`, `deals`, `companies`). |

**Query Parameter**

| Parameter | Type      | Default | Range  | Description |
|-----------|-----------|---------|--------|-------------|
| `limit`   | `integer` | `5`     | 1 – 50 | Number of sample records to return. |

**Example Response**

```json
{
  "object_type": "contacts",
  "total": 4821,
  "records": [
    {
      "id": "101",
      "properties": {
        "firstname": "Jane",
        "lastname": "Doe",
        "email": "jane.doe@example.com",
        "createdate": "2023-06-01T09:00:00.000Z",
        "lastmodifieddate": "2024-01-10T14:22:00.000Z"
      },
      "createdAt": "2023-06-01T09:00:00.000Z",
      "updatedAt": "2024-01-10T14:22:00.000Z",
      "archived": false
    }
  ],
  "paging": {
    "next": {
      "after": "101",
      "link": "https://api.hubapi.com/crm/v3/objects/contacts?after=101&limit=5"
    }
  }
}
```

---

### 4.1 Top-Level Response

| Key           | Type              | Description |
|---------------|-------------------|-------------|
| `object_type` | `string`          | Echoes back the `{object_type}` path parameter. Confirms which object's records are in the response. |
| `total`       | `integer`         | The **total number of records** that exist for this object type in the portal (not just the number returned in this response). Useful for showing record counts in a UI. |
| `records`     | `array<object>`   | The list of sample CRM record objects. Each entry is one record. See [4.2](#42-each-record-entry-inside-records-array). |
| `paging`      | `object \| null`  | Pagination cursor information returned by the HubSpot API. `null` if there are no more pages. See [4.3](#43-paging-object). |

---

### 4.2 Each Record Entry (inside `records` array)

| Key          | Type      | Description |
|--------------|-----------|-------------|
| `id`         | `string`  | The **unique numeric ID** of this CRM record as a string (e.g., `"101"`). This is the record's permanent identifier within HubSpot. Used to fetch, update, or delete the specific record via the HubSpot CRM API. |
| `properties` | `object`  | A flat key-value map of the record's **property values**. Each key is a property `name` (from the `/properties` endpoint) and the value is the current stored value as a string. Only the first 10 properties of the object are included in sample responses to keep payload size manageable. |
| `createdAt`  | `string`  | ISO 8601 UTC timestamp of when this record was **first created** in HubSpot (e.g., `"2023-06-01T09:00:00.000Z"`). Equivalent to Salesforce's `CreatedDate`. |
| `updatedAt`  | `string`  | ISO 8601 UTC timestamp of the **most recent modification** to any property of this record. Equivalent to Salesforce's `LastModifiedDate`. |
| `archived`   | `boolean` | Whether this record has been **soft-deleted (archived)** in HubSpot. Archived records are hidden from the standard UI and most API queries but can be retrieved with `archived=true`. Always `false` in sample responses since archived records are excluded by default. |

---

### 4.3 Paging Object

| Key    | Type             | Description |
|--------|------------------|-------------|
| `next` | `object \| null` | Present when there is a next page of results. Contains `after` (the cursor token — the last record ID from the current page) and `link` (the full URL to fetch the next page from the HubSpot API directly). `null` or absent when the current page is the last page. |

---

## 5. Property Type & Field Type Reference

HubSpot properties have two separate type concepts: `type` (data model) and `field_type` (UI widget).

### Property `type` values

| Type            | Description |
|-----------------|-------------|
| `string`        | A plain text value. Can hold any character sequence up to the field's length limit. |
| `number`        | A numeric value. Can be integer or decimal. Used for quantities, scores, revenue, counts, etc. |
| `bool`          | A boolean true/false value. Stored as `"true"` or `"false"` as strings in the properties map. |
| `enumeration`   | A value constrained to a predefined set of options. The `options` array lists the allowed values. Used for dropdown selects, radio buttons, and checkboxes. |
| `date`          | A calendar date with no time component, stored in `YYYY-MM-DD` format. Displayed in the portal's configured timezone. |
| `datetime`      | A date + time value stored as a Unix timestamp in milliseconds (epoch ms). Used for event times, activity timestamps, etc. |
| `phone_number`  | A text value formatted and normalized as a phone number. HubSpot may validate format depending on region settings. |
| `object_coordinates` | An internal type used for cross-object relationship metadata. Not typically user-facing. |

### Property `field_type` values

| Field Type    | Description |
|---------------|-------------|
| `text`        | A single-line text input. Used for names, identifiers, short strings. |
| `textarea`    | A multi-line text input. Used for notes, descriptions, longer content. |
| `number`      | A numeric input field. Renders with numeric keyboard on mobile. |
| `select`      | A single-select dropdown. Always paired with `type: "enumeration"` and a non-empty `options` list. |
| `radio`       | A radio button group for single-select enumeration values. Displays all options inline. |
| `checkbox`    | A multi-select checkboxes group. Paired with `type: "enumeration"`. Selected values are stored semicolon-delimited. |
| `booleancheckbox` | A single true/false checkbox. Always paired with `type: "bool"`. |
| `date`        | A date picker widget. Always paired with `type: "date"`. |
| `file`        | A file attachment input. Stores a reference to a HubSpot file manager URL. |
| `html`        | A rich text / HTML editor widget. |
| `phonenumber` | A phone number input with country code selector. Paired with `type: "phone_number"`. |

---

## 6. Standard Object Types Reference

These are the 12 standard object types hardcoded in this backend. They are available in every HubSpot portal regardless of subscription.

| `name`       | `label`      | Description |
|--------------|--------------|-------------|
| `contacts`   | Contacts     | Individual people — prospects, leads, customers, partners. The core CRM entity. |
| `companies`  | Companies    | Organizations or businesses associated with contacts and deals. |
| `deals`      | Deals        | Sales opportunities tracked through a pipeline with stages and close dates. |
| `tickets`    | Tickets      | Customer support/service requests managed through a help desk pipeline. |
| `products`   | Products     | Items or services sold, stored in the product library. Used in quotes and line items. |
| `line_items` | Line Items   | Individual products/services attached to a deal or quote, with quantities and prices. |
| `quotes`     | Quotes       | Sales proposals sent to contacts, containing line items and pricing. |
| `calls`      | Calls        | Logged phone call activities associated with contacts, companies, or deals. |
| `emails`     | Emails       | Logged or sent email activities tracked in the CRM timeline. |
| `meetings`   | Meetings     | Scheduled or logged meeting activities linked to CRM records. |
| `notes`      | Notes        | Free-text notes logged against CRM records. |
| `tasks`      | Tasks        | To-do items and follow-up actions assigned to users, associated with CRM records. |

---

*Generated from backend source: `backend/hubspot/service.py` — `test_connection()`, `get_all_object_types()`, `get_object_properties()`, and `get_object_sample_data()`*

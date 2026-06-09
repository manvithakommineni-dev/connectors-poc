# Salesforce API — Response Schema Documentation

This document describes every key-value pair returned by the two primary Salesforce metadata endpoints exposed by this backend.

---

## Table of Contents

1. [GET /api/v1/salesforce/objects](#1-get-apiv1salesforceobjects)
   - [Top-Level Response](#11-top-level-response)
   - [Each Object Entry](#12-each-object-entry-inside-objects-array)
2. [GET /api/v1/salesforce/objects/{object_name}/metadata](#2-get-apiv1salesforceobjectsobject_namemetadata)
   - [Top-Level Response](#21-top-level-response)
   - [Field Entries](#22-each-field-entry-inside-fields-array)
   - [Child Relationship Entries](#23-each-entry-inside-child_relationships-array)
   - [Record Type Entries](#24-each-entry-inside-record_types-array)
3. [Field Type Reference](#3-field-type-reference)

---

## 1. GET /api/v1/salesforce/objects

Lists all SObjects (tables/entities) available in the connected Salesforce org.

**Query Parameters**

| Parameter      | Type    | Default | Description                                    |
|----------------|---------|---------|------------------------------------------------|
| `queryable_only` | boolean | `true`  | When `true`, only objects that can be queried via SOQL are returned. |
| `custom_only`    | boolean | `false` | When `true`, only custom (user-created) objects are returned.         |

**Example Response**

```json
{
  "total": 1055,
  "objects": [
    {
      "name": "AIApplication",
      "label": "AI Application",
      "label_plural": "AI Applications",
      "queryable": true,
      "createable": false,
      "updateable": false,
      "deletable": false,
      "custom": false,
      "key_prefix": "0Pp"
    }
  ]
}
```

---

### 1.1 Top-Level Response

| Key       | Type            | Description |
|-----------|-----------------|-------------|
| `total`   | `integer`       | The total count of objects returned after applying any query parameter filters (`queryable_only`, `custom_only`). Useful for pagination awareness and summary display in a UI. |
| `objects` | `array<object>` | The list of Salesforce SObject descriptors. Each element represents one table/entity in the org. See [1.2](#12-each-object-entry-inside-objects-array) for the structure of each entry. |

---

### 1.2 Each Object Entry (inside `objects` array)

| Key            | Type              | Description |
|----------------|-------------------|-------------|
| `name`         | `string`          | The **API name** of the SObject. This is the exact identifier used in SOQL queries (`SELECT Id FROM AIApplication`), REST API calls, and in the metadata endpoint URL path parameter. Always camelCase, no spaces. |
| `label`        | `string`          | The **human-readable singular label** for the object as displayed in the Salesforce UI (e.g., "AI Application"). Used for display purposes in UI dropdowns and tables. |
| `label_plural` | `string`          | The **human-readable plural label** for the object (e.g., "AI Applications"). Used when displaying multiple records or navigating to a list view. |
| `queryable`    | `boolean`         | Whether this object can be retrieved using a SOQL `SELECT` statement. If `false`, the object cannot be read through standard queries. Many internal/system objects are not queryable. |
| `createable`   | `boolean`         | Whether new records of this object can be created via the API. If `false`, records can only be created internally by Salesforce (e.g., system-managed objects like audit logs). |
| `updateable`   | `boolean`         | Whether existing records of this object can be modified via the API. If `false`, the object is read-only and its records cannot be changed through external integrations. |
| `deletable`    | `boolean`         | Whether records of this object can be permanently deleted via the API. If `false`, records are either archived, or deletion is not supported (e.g., some metadata objects). |
| `custom`       | `boolean`         | Whether this object was created by a user/developer inside the Salesforce org (`true`) vs. being a standard Salesforce-provided object (`false`). Custom objects always have `__c` in their actual Salesforce API name. |
| `key_prefix`   | `string \| null`  | A 3-character prefix (e.g., `"0Pp"`) that is prepended to every record ID of this object type. All Salesforce record IDs are 18 characters: 3-char prefix + 15-char unique identifier. Useful for programmatically determining the object type from any record ID. May be `null` for objects that do not produce individual records. |

---

## 2. GET /api/v1/salesforce/objects/{object_name}/metadata

Returns comprehensive metadata for a single Salesforce SObject — including all its fields, child relationship links, and record types.

**Path Parameter**

| Parameter     | Type     | Description |
|---------------|----------|-------------|
| `object_name` | `string` | The API name of the SObject (e.g., `AIApplication`, `Account`, `Contact`, `My_Custom_Object__c`). Must match the `name` field from the `/objects` list exactly. |

**Example Response**

```json
{
  "name": "AIApplication",
  "label": "AI Application",
  "label_plural": "AI Applications",
  "custom": false,
  "fields_count": 12,
  "fields": [
    {
      "name": "Id",
      "label": "AI Application ID",
      "type": "id",
      "length": 18,
      "precision": 0,
      "scale": 0,
      "nillable": false,
      "unique": false,
      "custom": false,
      "default_value": null,
      "picklist_values": [],
      "reference_to": [],
      "relationship_name": null,
      "createable": false,
      "updateable": false,
      "filterable": true,
      "sortable": true,
      "groupable": true
    }
  ],
  "child_relationships": [
    {
      "child_sobject": "AIApplicationConfig",
      "field": "AIApplicationId",
      "relationship_name": "AIApplicationConfigs",
      "cascade_delete": true
    }
  ],
  "record_types": [
    {
      "id": "0124W000001aXYZAA2",
      "name": "Premium",
      "developer_name": "Premium"
    }
  ]
}
```

---

### 2.1 Top-Level Response

| Key                   | Type            | Description |
|-----------------------|-----------------|-------------|
| `name`                | `string`        | The API name of the SObject being described. Same value as used in the URL path parameter. |
| `label`               | `string`        | The singular human-readable label for this object as shown in the Salesforce UI. |
| `label_plural`        | `string`        | The plural human-readable label used in list views and navigation. |
| `custom`              | `boolean`       | Indicates whether this is a custom (user-defined) object (`true`) or a standard Salesforce object (`false`). |
| `fields_count`        | `integer`       | The total number of fields (columns) returned for this object. Useful for summary display without iterating the full `fields` array. |
| `fields`              | `array<object>` | The complete list of field descriptors for this object. Each entry fully describes one column/attribute. See [2.2](#22-each-field-entry-inside-fields-array). |
| `child_relationships` | `array<object>` | Describes other SObjects that reference this object as a parent (i.e., foreign key relationships pointing *to* this object). Useful for understanding how to traverse related data. See [2.3](#23-each-entry-inside-child_relationships-array). |
| `record_types`        | `array<object>` | Named variants of this object that can have different page layouts, picklist values, or business processes. The default/master record type is excluded. See [2.4](#24-each-entry-inside-record_types-array). |

---

### 2.2 Each Field Entry (inside `fields` array)

| Key                | Type              | Description |
|--------------------|-------------------|-------------|
| `name`             | `string`          | The **API name** of the field. Used in SOQL (`SELECT Name FROM Account`), REST API payloads, and data mapping. Standard fields use PascalCase (e.g., `FirstName`); custom fields end in `__c` (e.g., `My_Field__c`). |
| `label`            | `string`          | The **human-readable label** for the field as displayed in Salesforce UI forms and list views. May differ from `name` (e.g., name = `"OwnerId"`, label = `"Owner"`). |
| `type`             | `string`          | The **data type** of the field. Determines how values should be parsed, validated, and rendered. See the [Field Type Reference](#3-field-type-reference) section for all possible values. |
| `length`           | `integer \| null` | Maximum character length for text-based fields (e.g., `string`, `textarea`, `id`). For numeric fields, this may represent total digit capacity. `null` for types where length is not applicable (e.g., `boolean`, `date`). |
| `precision`        | `integer \| null` | For numeric fields (`double`, `currency`, `percent`), the total number of significant digits (integer + decimal). `0` for non-numeric types. |
| `scale`            | `integer \| null` | For numeric fields, the number of digits to the **right of the decimal point**. `0` for integer-type fields or non-numeric types. |
| `nillable`         | `boolean`         | Whether the field accepts `null` (empty) values. `true` = optional field; `false` = required field that must have a value on record creation/update. |
| `unique`           | `boolean`         | Whether the field enforces a uniqueness constraint across all records in the org. `true` means no two records can have the same value for this field. |
| `custom`           | `boolean`         | Whether this field was created by a user/developer (`true`) or is a standard Salesforce-provided field (`false`). Custom fields always end with `__c` in their `name`. |
| `default_value`    | `any \| null`     | The default value automatically assigned to this field when a new record is created and no explicit value is provided. `null` if no default is configured. Can be a string, number, boolean, or formula result depending on the field type. |
| `picklist_values`  | `array<string>`   | Available option values for `picklist` and `multipicklist` fields. This is a flat list of the allowed string values (e.g., `["Open", "Closed", "Pending"]`). Empty array (`[]`) for all other field types. |
| `reference_to`     | `array<string>`   | For `reference` (lookup/master-detail) fields, lists the API names of the SObjects this field can point to (e.g., `["Account", "Contact"]`). A field can be polymorphic and reference multiple object types. Empty array for non-reference fields. |
| `relationship_name`| `string \| null`  | The relationship traversal name for `reference` fields, used in SOQL relationship queries (e.g., `SELECT Account.Name FROM Contact`). `null` for non-reference fields. |
| `createable`       | `boolean`         | Whether a value for this field can be set when creating a new record via the API. `false` for system-managed fields like `Id`, `CreatedDate`, and `SystemModstamp`. |
| `updateable`       | `boolean`         | Whether a value for this field can be changed after the record is created. `false` for immutable fields like `Id`, `CreatedDate`, and `OwnerId` (in some contexts). |
| `filterable`       | `boolean`         | Whether this field can be used in a SOQL `WHERE` clause to filter records. `false` for compound fields (like `Address`) or fields not indexed for filtering. |
| `sortable`         | `boolean`         | Whether this field can be used in a SOQL `ORDER BY` clause. `false` for large text area fields, encrypted fields, and other non-sortable types. |
| `groupable`        | `boolean`         | Whether this field can be used in a SOQL `GROUP BY` clause for aggregation queries. `false` for fields like `textarea`, `base64`, and non-groupable reference fields. |

---

### 2.3 Each Entry (inside `child_relationships` array)

Child relationships describe other SObjects that have a **foreign key pointing to this object** — i.e., this object is the parent, and the listed SObject is the child.

| Key                 | Type              | Description |
|---------------------|-------------------|-------------|
| `child_sobject`     | `string`          | The API name of the **child object** that holds the foreign key reference. For example, if you are describing `Account`, a child might be `Contact` (since `Contact` has an `AccountId` field). |
| `field`             | `string`          | The API name of the **field on the child object** that stores the reference (foreign key) to this parent object's `Id`. For example, on `Contact`, the field would be `"AccountId"`. |
| `relationship_name` | `string \| null`  | The relationship name used in SOQL to traverse from parent to children using a **subquery** (e.g., `SELECT Id, (SELECT Id FROM Contacts) FROM Account`). `null` if no traversal name is defined. |
| `cascade_delete`    | `boolean`         | Whether deleting a record of this parent object will **automatically delete** all related child records. `true` for master-detail relationships; `false` for standard lookup relationships. |

---

### 2.4 Each Entry (inside `record_types` array)

Record types allow a single SObject to behave differently for different business processes — different page layouts, picklist values, and approval processes. The default "Master" record type is excluded from this list.

| Key              | Type     | Description |
|------------------|----------|-------------|
| `id`             | `string` | The **18-character Salesforce record ID** of the RecordType record itself (e.g., `"0124W000001aXYZAA2"`). Used when creating or updating records that must be assigned to a specific record type via `RecordTypeId`. |
| `name`           | `string` | The **human-readable name** of the record type as shown in the Salesforce UI (e.g., `"Premium"`, `"Enterprise"`, `"Standard"`). Displayed in page layout assignments and record creation flows. |
| `developer_name` | `string` | The **API/developer name** of the record type, used in code, metadata, and deployments. No spaces allowed. Typically matches or closely resembles `name` but uses underscores instead of spaces. |

---

## 3. Field Type Reference

The `type` field in each field entry is one of the following Salesforce field types:

| Type             | Description |
|------------------|-------------|
| `id`             | The unique 18-character Salesforce record identifier. Every SObject has exactly one `Id` field of this type. |
| `string`         | A single-line plain text field. Length is capped by the `length` property (typically 80–255 characters). |
| `textarea`       | A multi-line plain text field. Long text areas can hold up to 131,072 characters. Not sortable or groupable. |
| `richTextArea`   | A multi-line HTML-formatted text field rendered as a rich text editor in the UI. |
| `boolean`        | A true/false checkbox field. In SOQL, filter with `WHERE IsActive = true`. |
| `integer`        | A whole number field with no decimal places. |
| `double`         | A floating-point number field. Precision and scale determine total digits and decimal places. |
| `currency`       | A monetary value field. Automatically formatted with the org's default currency symbol in the UI. |
| `percent`        | A numeric percentage field. Stored as a number (e.g., `25.5` for 25.5%). |
| `date`           | A calendar date field (no time component), stored in `YYYY-MM-DD` format. |
| `datetime`       | A date + time field stored in UTC (`YYYY-MM-DDTHH:MM:SS.000Z`). Displayed in the user's local timezone in the UI. |
| `time`           | A time-of-day field with no date component. |
| `phone`          | A text field pre-formatted for phone numbers. No formatting is enforced at the API level. |
| `email`          | A text field validated as an email address format. Enables click-to-email in the UI. |
| `url`            | A text field validated as a URL. Renders as a clickable hyperlink in the UI. |
| `picklist`       | A single-select dropdown field. The `picklist_values` array contains all allowed options. |
| `multipicklist`  | A multi-select picklist field. Multiple values are stored as a semicolon-delimited string (e.g., `"Red;Blue;Green"`). The `picklist_values` array lists all allowed options. |
| `reference`      | A lookup or master-detail relationship field. Stores the `Id` of a record in another (or the same) SObject. `reference_to` lists the target objects; `relationship_name` enables SOQL traversal. |
| `base64`         | A binary/file attachment field (used in Document and Attachment objects). Not sortable or filterable. |
| `encryptedstring`| An encrypted text field whose value is masked in the UI and API responses unless the user has the "View Encrypted Data" permission. |
| `address`        | A compound field that aggregates multiple address sub-fields (Street, City, State, PostalCode, Country, Latitude, Longitude). Not directly filterable as a compound unit. |
| `location`       | A geolocation compound field storing latitude/longitude coordinates. Used with `DISTANCE()` and `GEOLOCATION()` SOQL functions. |
| `anyType`        | A polymorphic field that can hold values of different types depending on context (used in some formula and metadata fields). |
| `complexvalue`   | A structured/complex value type used in some internal Salesforce system fields. |

---

*Generated from backend source: `backend/salesforce/service.py` — `get_all_objects()` and `get_object_metadata()`*

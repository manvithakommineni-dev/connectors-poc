# SAP OData API — Response Schema Documentation

This document describes every key-value pair returned by the SAP OData metadata endpoints exposed by this backend.

---

## Background — How SAP Exposes Metadata

SAP uses **OData (Open Data Protocol)**. Unlike Salesforce (REST describe) or HubSpot (CRM Properties API), SAP metadata is delivered as a single **EDMX XML document** via a `$metadata` endpoint. The backend fetches and parses this XML and converts it into clean JSON responses.

**Key OData concepts:**

| OData Term            | Equivalent In              | Description |
|-----------------------|---------------------------|-------------|
| Service               | Database / Schema         | One OData service = one logical domain (e.g. Business Partner, Sales Orders) |
| EntityType            | Table / SObject / Object  | The schema definition of one entity (fields, keys, relationships) |
| EntitySet             | Queryable View / Endpoint | The actual URL collection you query — bound to an EntityType |
| Property              | Column / Field            | One field on an EntityType |
| Key Property          | Primary Key               | The field(s) that uniquely identify a record |
| NavigationProperty    | Foreign Key / Relationship| Links one EntityType to another |
| Namespace             | Schema prefix             | Unique identifier for the service schema (e.g. `API_BUSINESS_PARTNER`) |

---

## Table of Contents

1. [GET /api/v1/sap/connect](#1-get-apiv1sapconnect)
2. [GET /api/v1/sap/services](#2-get-apiv1sapservices)
3. [GET /api/v1/sap/services/{service_name}/entities](#3-get-apiv1sapservicesservice_nameentities)
   - [Top-Level Response](#31-top-level-response)
   - [Each Entity Entry](#32-each-entity-entry-inside-entities-array)
4. [GET /api/v1/sap/services/{service_name}/entities/{entity_name}/fields](#4-get-apiv1sapservicesservice_nameentitiesentity_namefields)
   - [Top-Level Response](#41-top-level-response)
   - [Each Field Entry](#42-each-field-entry-inside-fields-array)
   - [Each Navigation Property Entry](#43-each-entry-inside-navigation_properties-array)
5. [GET /api/v1/sap/services/{service_name}/metadata](#5-get-apiv1sapservicesservice_namemetadata)
6. [EDM Field Type Reference](#6-edm-field-type-reference)
7. [Pre-Configured SAP OData Services Reference](#7-pre-configured-sap-odata-services-reference)

---

## 1. GET /api/v1/sap/connect

Tests SAP connectivity by fetching the `$metadata` endpoint of `API_BUSINESS_PARTNER` as a health check. Returns a summary of the connection configuration and confirmation that the OData service is reachable.

**Authentication:**
- `apikey` mode — sends `APIKey: <key>` header (used with SAP Business Accelerator Hub sandbox)
- `basic` mode — sends HTTP Basic Auth username/password (used with on-premise SAP or SAP BTP)

**Example Response**

```json
{
  "connected": true,
  "base_url": "https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap",
  "auth_type": "apikey",
  "test_service": "API_BUSINESS_PARTNER",
  "entity_types_found": 43,
  "entity_sets_found": 43,
  "namespace": "API_BUSINESS_PARTNER"
}
```

---

### Response Fields

| Key                  | Type      | Description |
|----------------------|-----------|-------------|
| `connected`          | `boolean` | Always `true` when this response is returned. Confirms the SAP API key/credentials are valid and the OData `$metadata` endpoint is reachable. A `401` HTTP error is raised instead on auth failure. |
| `base_url`           | `string`  | The root URL prefix used for all SAP OData requests. For the sandbox this is `https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap`. For production it is the on-premise or BTP system URL configured in `SAP_BASE_URL`. |
| `auth_type`          | `string`  | The authentication method in use: `"apikey"` (SAP Business Accelerator Hub sandbox) or `"basic"` (on-premise/BTP with username + password). Controlled by `SAP_AUTH_TYPE` in `.env`. |
| `test_service`       | `string`  | The OData service name used as the connectivity test. Always `"API_BUSINESS_PARTNER"` — this service was used to validate that the connection is alive. |
| `entity_types_found` | `integer` | The count of `EntityType` definitions found in the `API_BUSINESS_PARTNER` EDMX metadata. Confirms that parsing the XML response succeeded and returned meaningful data. |
| `entity_sets_found`  | `integer` | The count of `EntitySet` entries found in the `EntityContainer` of the metadata. Each EntitySet is a queryable OData collection. Usually equals `entity_types_found`. |
| `namespace`          | `string`  | The XML schema `Namespace` attribute from the EDMX document (e.g. `"API_BUSINESS_PARTNER"`). Acts as a prefix for all type names in OData queries and relationships within this service. |

---

## 2. GET /api/v1/sap/services

Returns the list of pre-configured SAP OData services known to this backend. These are hardcoded well-known S/4HANA services available on the SAP Business Accelerator Hub sandbox.

**Example Response**

```json
{
  "total": 6,
  "services": [
    {
      "name": "API_BUSINESS_PARTNER",
      "label": "Business Partner",
      "description": "Master data for business partners (customers, vendors, contacts)"
    }
  ]
}
```

---

### Top-Level Response

| Key        | Type            | Description |
|------------|-----------------|-------------|
| `total`    | `integer`       | Count of pre-configured OData services available. |
| `services` | `array<object>` | List of service descriptors. Each entry identifies one SAP OData domain. |

---

### Each Service Entry (inside `services` array)

| Key           | Type     | Description |
|---------------|----------|-------------|
| `name`        | `string` | The **OData service name** — used as the `{service_name}` path parameter in all other endpoints (e.g. `"API_BUSINESS_PARTNER"`, `"API_SALES_ORDER_SRV"`). This is the exact name appended to the base URL to reach the service's `$metadata` endpoint. |
| `label`       | `string` | A short **human-readable name** for the service (e.g. `"Business Partner"`, `"Sales Orders"`). Used for display in UI dropdowns and navigation lists. |
| `description` | `string` | A brief plain-English explanation of what business domain this OData service covers and what kinds of data it contains (e.g. `"Master data for business partners (customers, vendors, contacts)"`). |

---

## 3. GET /api/v1/sap/services/{service_name}/entities

Returns a **lightweight summary** of all EntityTypes in the given SAP OData service — without the full field details. Use this to populate the object/entity list in a UI before the user drills into a specific entity.

**Path Parameter**

| Parameter      | Type     | Description |
|----------------|----------|-------------|
| `service_name` | `string` | The OData service identifier (e.g. `API_BUSINESS_PARTNER`, `API_SALES_ORDER_SRV`, `API_PRODUCT_SRV`). Must match a value from the `name` field in the `/services` list. |

**Example Response**

```json
{
  "service_name": "API_BUSINESS_PARTNER",
  "namespace": "API_BUSINESS_PARTNER",
  "total": 43,
  "entities": [
    {
      "name": "A_BusinessPartnerType",
      "entity_set_name": "A_BusinessPartner",
      "fields_count": 88,
      "key_fields": ["BusinessPartner"],
      "nav_properties_count": 14
    }
  ]
}
```

---

### 3.1 Top-Level Response

| Key            | Type            | Description |
|----------------|-----------------|-------------|
| `service_name` | `string`        | Echoes back the `{service_name}` path parameter that was requested. Confirms which OData service's entities are in the response. |
| `namespace`    | `string`        | The XML schema namespace for this OData service, extracted from the EDMX `<Schema Namespace="...">` attribute. Used as a prefix in fully-qualified type references (e.g. `API_BUSINESS_PARTNER.A_BusinessPartnerType`). |
| `total`        | `integer`       | Total count of EntityType definitions found in this service's `$metadata`. |
| `entities`     | `array<object>` | Lightweight summary list of all entity types. See [3.2](#32-each-entity-entry-inside-entities-array) for the structure of each entry. |

---

### 3.2 Each Entity Entry (inside `entities` array)

| Key                    | Type            | Description |
|------------------------|-----------------|-------------|
| `name`                 | `string`        | The **EntityType name** as defined in the EDMX XML `<EntityType Name="...">` element (e.g. `"A_BusinessPartnerType"`, `"A_SalesOrderType"`). This is the schema definition name — not the URL-queryable name. Use `entity_set_name` for OData URL queries. |
| `entity_set_name`      | `string`        | The **EntitySet name** bound to this EntityType in the `EntityContainer` (e.g. `"A_BusinessPartner"`, `"A_SalesOrder"`). This is the name used in OData query URLs: `GET /API_BUSINESS_PARTNER/A_BusinessPartner`. Can be the same as `name` or an abbreviated version. Empty string if no EntitySet binding was found. |
| `fields_count`         | `integer`       | Total number of `<Property>` elements (fields/columns) defined on this EntityType. Useful for displaying a field count badge in the UI without fetching full field details. |
| `key_fields`           | `array<string>` | List of property names that form the **primary key** of this entity (extracted from the `<Key><PropertyRef>` elements in the EDMX). Most SAP entities have a single key field (e.g. `["BusinessPartner"]`), but composite keys are possible (e.g. `["SalesOrder", "SalesOrderItem"]`). |
| `nav_properties_count` | `integer`       | Count of `<NavigationProperty>` elements on this EntityType. NavigationProperties represent relationships to other EntityTypes (foreign key links). A high count indicates a richly connected entity. |

---

## 4. GET /api/v1/sap/services/{service_name}/entities/{entity_name}/fields

Returns **complete field-level metadata** for one specific EntityType — including all property definitions, their OData/EDM types, SAP-specific annotations, and navigation property (relationship) descriptors.

**Path Parameters**

| Parameter      | Type     | Description |
|----------------|----------|-------------|
| `service_name` | `string` | The OData service identifier (e.g. `API_BUSINESS_PARTNER`). |
| `entity_name`  | `string` | Either the **EntityType name** (e.g. `A_BusinessPartnerType`) or the **EntitySet name** (e.g. `A_BusinessPartner`). Both are accepted — the backend resolves EntitySet names to their corresponding EntityType automatically. |

**Example Response**

```json
{
  "service_name": "API_BUSINESS_PARTNER",
  "entity_type": "A_BusinessPartnerType",
  "entity_set": "A_BusinessPartner",
  "key_fields": ["BusinessPartner"],
  "fields_count": 88,
  "fields": [
    {
      "name": "BusinessPartner",
      "type": "Edm.String",
      "simple_type": "String",
      "nullable": false,
      "max_length": "10",
      "precision": null,
      "scale": null,
      "is_key": true,
      "label": "Business Partner Number",
      "creatable": "true",
      "updatable": "false",
      "filterable": "true",
      "sortable": "true"
    }
  ],
  "navigation_properties": [
    {
      "name": "to_BusinessPartnerAddress",
      "relationship": "API_BUSINESS_PARTNER.to_BusinessPartnerAddress",
      "from_role": "FromRole_to_BusinessPartnerAddress",
      "to_role": "ToRole_to_BusinessPartnerAddress"
    }
  ]
}
```

---

### 4.1 Top-Level Response

| Key                     | Type            | Description |
|-------------------------|-----------------|-------------|
| `service_name`          | `string`        | Echoes back the OData service name from the URL path. Useful for traceability in multi-service UIs. |
| `entity_type`           | `string`        | The resolved **EntityType name** (the EDMX schema definition name). If `entity_name` in the request was an EntitySet name, this shows the resolved EntityType it maps to. |
| `entity_set`            | `string`        | The **EntitySet name** (the queryable URL collection name) associated with this EntityType. Use this name when building OData `GET` queries against the live SAP system. |
| `key_fields`            | `array<string>` | List of field names that form the **primary key** for records of this entity. Key fields are required when constructing a single-record OData URL (e.g. `A_BusinessPartner('10000001')`). |
| `fields_count`          | `integer`       | Total number of fields (Properties) returned for this entity. |
| `fields`                | `array<object>` | Full list of field descriptors. Each entry describes one column of the entity in detail. See [4.2](#42-each-field-entry-inside-fields-array). |
| `navigation_properties` | `array<object>` | List of relationship links from this entity to other entities. See [4.3](#43-each-entry-inside-navigation_properties-array). |

---

### 4.2 Each Field Entry (inside `fields` array)

| Key           | Type              | Description |
|---------------|-------------------|-------------|
| `name`        | `string`          | The **OData property name** as defined in the EDMX XML `<Property Name="...">` attribute (e.g. `"BusinessPartner"`, `"FirstName"`, `"CreationDate"`). This is the exact name used in OData `$select`, `$filter`, and `$orderby` query options, and in JSON request/response payloads. |
| `type`        | `string`          | The **fully-qualified EDM type** including the `Edm.` namespace prefix (e.g. `"Edm.String"`, `"Edm.Decimal"`, `"Edm.DateTime"`). This is the raw value from the EDMX XML `Type` attribute. See the [EDM Field Type Reference](#6-edm-field-type-reference) for all possible values. |
| `simple_type` | `string`          | A **shortened version of `type`** with the `Edm.` prefix stripped (e.g. `"String"`, `"Decimal"`, `"DateTime"`). Provided for convenience when displaying types in a UI without the namespace prefix. |
| `nullable`    | `boolean`         | Whether this field accepts `null` (empty) values. `true` = the field is optional; `false` = the field is mandatory and must have a value. Derived from the EDMX `Nullable="false"` attribute — if absent, defaults to `true` (nullable). |
| `max_length`  | `string \| null`  | Maximum allowed character length for `Edm.String` fields (e.g. `"10"`, `"255"`, `"1333"`). `null` for non-string types or fields with no explicit length constraint. Returned as a string because it comes directly from the XML attribute. |
| `precision`   | `string \| null`  | For `Edm.Decimal` fields, the total number of significant digits (integer + decimal digits combined, e.g. `"23"`). `null` for non-decimal types. Returned as a string from the XML attribute. |
| `scale`       | `string \| null`  | For `Edm.Decimal` fields, the number of digits **to the right of the decimal point** (e.g. `"2"` for a 2-decimal-place currency amount). `null` for non-decimal types. Returned as a string from the XML attribute. |
| `is_key`      | `boolean`         | Whether this field is part of the entity's **primary key**. `true` for fields listed under `<Key><PropertyRef>` in the EDMX. Key fields are required in single-record OData URL address patterns (e.g. `A_BusinessPartner('10000001')`). |
| `label`       | `string`          | The **SAP human-readable label** for this field, extracted from the SAP-specific annotation `sap:label` in the EDMX XML (e.g. `"Business Partner Number"`, `"First Name"`). Falls back to the field `name` if no `sap:label` annotation is present. Used for display in UI column headers and forms. |
| `creatable`   | `string`          | SAP annotation (`sap:creatable`) indicating whether this field can be set when **creating** a new record via OData `POST`. Value is `"true"` or `"false"` as a string (from the XML attribute). `"false"` for system-managed fields like document numbers assigned by SAP. |
| `updatable`   | `string`          | SAP annotation (`sap:updatable`) indicating whether this field can be changed on an **existing record** via OData `PUT`/`PATCH`. `"false"` for immutable fields like primary keys, creation timestamps, and document numbers. |
| `filterable`  | `string`          | SAP annotation (`sap:filterable`) indicating whether this field can be used in an OData `$filter` expression (e.g. `$filter=BusinessPartner eq '10000001'`). `"false"` for blob fields, internal system fields, and fields not indexed for filtering. |
| `sortable`    | `string`          | SAP annotation (`sap:sortable`) indicating whether this field can be used in an OData `$orderby` expression (e.g. `$orderby=CreationDate desc`). `"false"` for large text fields, binary fields, and fields the SAP system does not index for sorting. |

---

### 4.3 Each Entry (inside `navigation_properties` array)

NavigationProperties define **relationships between EntityTypes** — equivalent to foreign keys in a relational database, or Salesforce Relationships / HubSpot Associations.

| Key            | Type     | Description |
|----------------|----------|-------------|
| `name`         | `string` | The **navigation property name** as defined in the EDMX XML (e.g. `"to_BusinessPartnerAddress"`, `"to_SalesOrderItem"`). This is the name used in OData `$expand` queries to fetch related entities in a single request (e.g. `$expand=to_BusinessPartnerAddress`). SAP navigation property names conventionally start with `"to_"`. |
| `relationship` | `string` | The **fully-qualified association name** in the format `Namespace.AssociationName` (e.g. `"API_BUSINESS_PARTNER.to_BusinessPartnerAddress"`). Refers to an `<Association>` element in the EDMX that defines the multiplicity (1-to-1, 1-to-many) and referential constraints for this link. |
| `from_role`    | `string` | The **role name representing the source end** of the relationship (i.e. the current entity). Convention: `"FromRole_<NavigationPropertyName>"`. Corresponds to the `<AssociationEnd>` in the EDMX that has the `Role` matching this string. |
| `to_role`      | `string` | The **role name representing the target end** of the relationship (i.e. the related entity being navigated to). Convention: `"ToRole_<NavigationPropertyName>"`. The entity type of the target is defined in the `<AssociationEnd>` element matching this role in the EDMX. |

---

## 5. GET /api/v1/sap/services/{service_name}/metadata

Returns the **complete parsed EDMX metadata** for an entire OData service in one response — all EntityTypes with full field definitions, all EntitySets, and the namespace. This is the "full describe" equivalent and is the heaviest endpoint.

**Example Response Structure**

```json
{
  "service_name": "API_BUSINESS_PARTNER",
  "namespace": "API_BUSINESS_PARTNER",
  "total_entity_types": 43,
  "total_entity_sets": 43,
  "entity_types": [ /* full entity objects same as /fields response */ ],
  "entity_sets": [
    {
      "name": "A_BusinessPartner",
      "entity_type": "A_BusinessPartnerType"
    }
  ]
}
```

---

### Additional Fields in Full Metadata Response

| Key                  | Type            | Description |
|----------------------|-----------------|-------------|
| `service_name`       | `string`        | The OData service name requested. |
| `namespace`          | `string`        | The XML schema namespace of this service. |
| `total_entity_types` | `integer`       | Total count of `<EntityType>` definitions in the EDMX schema. |
| `total_entity_sets`  | `integer`       | Total count of `<EntitySet>` entries in the `<EntityContainer>`. Usually equal to `total_entity_types`. |
| `entity_types`       | `array<object>` | Complete list of all entities — each with full `fields` and `navigation_properties` arrays (same structure as the `/fields` response). |
| `entity_sets`        | `array<object>` | Flat list of all EntitySet bindings. Each entry has `name` (EntitySet name) and `entity_type` (the EntityType it is bound to). |

---

## 6. EDM Field Type Reference

SAP OData uses **Entity Data Model (EDM)** types. All types are prefixed with `Edm.` in the `type` field; the `simple_type` field contains the name without the prefix.

| `type` (`simple_type`)       | Description |
|------------------------------|-------------|
| `Edm.String` (`String`)      | A variable-length Unicode text string. The most common SAP field type. `max_length` defines the character limit (e.g. 10 for a Business Partner number, 255 for a description). |
| `Edm.Decimal` (`Decimal`)    | A fixed-point decimal number. `precision` gives total significant digits; `scale` gives decimal places. Used for quantities, amounts, prices, and rates. |
| `Edm.DateTime` (`DateTime`)  | A date and time value. In SAP OData v2, serialized as `/Date(<epoch_milliseconds>)/` (e.g. `/Date(1704067200000)/`). |
| `Edm.DateTimeOffset` (`DateTimeOffset`) | A date + time value with timezone offset. Used in newer S/4HANA APIs. Serialized as an ISO 8601 string with offset. |
| `Edm.Time` (`Time`)          | A time-of-day duration value (no date component). Serialized as `PT<H>H<M>M<S>S` (ISO 8601 duration). |
| `Edm.Boolean` (`Boolean`)    | A true/false value. Serialized as JSON `true` or `false`. |
| `Edm.Byte` (`Byte`)          | An unsigned 8-bit integer (0–255). Used for small status codes or flags. |
| `Edm.Int16` (`Int16`)        | A 16-bit signed integer (−32,768 to 32,767). |
| `Edm.Int32` (`Int32`)        | A 32-bit signed integer. Used for counts, quantities, and numeric identifiers. |
| `Edm.Int64` (`Int64`)        | A 64-bit signed integer. Used for large numeric values. |
| `Edm.Single` (`Single`)      | A 32-bit single-precision floating-point number. |
| `Edm.Double` (`Double`)      | A 64-bit double-precision floating-point number. |
| `Edm.Guid` (`Guid`)          | A 128-bit globally unique identifier (UUID), formatted as `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`. Used as surrogate keys in some SAP entities. |
| `Edm.Binary` (`Binary`)      | Raw binary data (byte array). Used for file content or encoded data. Not filterable or sortable. |

---

## 7. Pre-Configured SAP OData Services Reference

These are the 6 SAP S/4HANA OData services pre-configured in this backend, all accessible on the SAP Business Accelerator Hub sandbox with a free API key.

| `name`                           | `label`              | Key Entities | Description |
|----------------------------------|----------------------|--------------|-------------|
| `API_BUSINESS_PARTNER`           | Business Partner     | `A_BusinessPartner`, `A_BusinessPartnerAddress`, `A_Customer`, `A_Supplier` | Master data for all business partners — customers, vendors, and contact persons. Central entity in SAP S/4HANA. |
| `API_SALES_ORDER_SRV`            | Sales Orders         | `A_SalesOrder`, `A_SalesOrderItem`, `A_SalesOrderScheduleLine` | Sales order headers, line items, delivery schedules, and business partners involved in the sales process. |
| `API_PRODUCT_SRV`                | Products / Materials | `A_Product`, `A_ProductPlant`, `A_ProductStorage`, `A_ProductValuation` | Product/material master data across plants, storage locations, and valuation areas. |
| `API_PURCHASEORDER_PROCESS_SRV`  | Purchase Orders      | `A_PurchaseOrder`, `A_PurchaseOrderItem`, `A_PurchaseOrderScheduleLine` | Purchase order process including items, account assignments, and delivery scheduling. |
| `API_SUPPLIER_SRV`               | Suppliers            | `A_Supplier`, `A_SupplierPurchasingOrg`, `A_SupplierCompany` | Supplier master data including purchasing organization and company code level data. |
| `API_ODATA_SAP_FINANCIAL_SRV`    | Financial Data       | GL Accounts, Financial Postings | General ledger account master data and financial document postings. |

---

*Generated from backend source: `backend/sap/service.py` — `test_connection()`, `list_services()`, `get_service_entities()`, `get_entity_fields()`, and `_parse_metadata()`*

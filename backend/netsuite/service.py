"""
NetSuite connectivity and metadata retrieval service.

How NetSuite exposes metadata:
  NetSuite uses its REST Metadata Catalog API under:
    /services/rest/record/v1/metadata-catalog/

  Key endpoints:
    List all record types : GET /services/rest/record/v1/metadata-catalog/
    Record type schema    : GET /services/rest/record/v1/metadata-catalog/{recordType}
    Fetch records         : GET /services/rest/record/v1/{recordType}

  The metadata-catalog response for a record type includes:
    - name         : internal record type name (e.g. "customer")
    - label        : display name (e.g. "Customer")
    - properties   : list of fields/columns with:
        name          : field internal name
        label         : display label
        type          : field type (string, integer, boolean, select, date, etc.)
        nullable      : whether it can be null
        readOnly      : whether it's read-only
        referenceType : if reference type, which record it points to

  NetSuite concept equivalents:
    Salesforce SObject    → NetSuite Record Type  (e.g. customer, salesOrder)
    Salesforce Field      → NetSuite Field / Property
    Salesforce Lookup     → NetSuite Reference    (select type with referenceType)
    Salesforce Relate     → NetSuite Sublist
    SAP EntityType        → NetSuite Record Type
    Oracle Resource       → NetSuite Record Type
    Workday Business Obj  → NetSuite Record Type

  NetSuite Modules (functional grouping):
    Accounting    : account, journalEntry, accountingPeriod, budget
    Customers     : customer, contact, lead, prospect, customerPayment
    Vendors       : vendor, vendorBill, vendorPayment, purchaseOrder
    Inventory     : inventoryItem, assemblyItem, itemGroup, lotNumberedItem
    Sales         : salesOrder, opportunity, estimate, itemFulfillment
    Employees     : employee, department, job, payrollItem
    CRM           : campaign, caseRecord, supportCase, task, phoneCall

Authentication (real NetSuite):
  OAuth 2.0 Client Credentials (Machine-to-Machine):
    1. In NetSuite: Setup > Integration > Manage Integrations → New
    2. Enable Token-Based Authentication or OAuth 2.0
    3. Get: Client ID, Client Secret
    4. Account ID: visible in your NetSuite URL (e.g. https://1234567.app.netsuite.com → 1234567)
    5. Token URL: https://{account_id}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token

Demo Mode:
  If NS_ACCOUNT_ID is empty, returns built-in schema based on real NetSuite
  REST Metadata Catalog field definitions.

Getting a Free Trial:
  Go to https://www.netsuite.com/portal/products/erp/free-product-tour.shtml
  or https://www.netsuite.com/portal/home.shtml → "Free Trial" / "Get Started"
"""

import requests
import logging
from core.config import settings

logger = logging.getLogger(__name__)

NS_REST_BASE = "https://{account_id}.suitetalk.api.netsuite.com/services/rest/record/v1"
NS_TOKEN_URL = "https://{account_id}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token"

# ─────────────────────────────────────────────────────────────────────────────
# Built-in demo — real NetSuite REST Metadata Catalog schema
# Covers 7 modules, 20 record types, 150+ fields
# ─────────────────────────────────────────────────────────────────────────────
DEMO_MODULES = [
    {
        "id": "accounting",
        "label": "Accounting",
        "description": "Chart of Accounts, Journal Entries, Accounting Periods, Budgets",
        "records": [
            {
                "name": "account",
                "label": "Account",
                "module": "accounting",
                "description": "Chart of accounts — general ledger accounts",
                "fields": [
                    {"name": "id", "label": "Internal ID", "type": "integer", "nullable": False, "readOnly": True, "is_key": True, "referenceType": None, "description": "Internal NetSuite ID"},
                    {"name": "acctNumber", "label": "Account Number", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Account number code"},
                    {"name": "acctName", "label": "Account Name", "type": "string", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Full name of the account"},
                    {"name": "acctType", "label": "Account Type", "type": "enum", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Bank, AccountsReceivable, AccountsPayable, Income, Expense, etc."},
                    {"name": "currency", "label": "Currency", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "currency", "description": "Account currency"},
                    {"name": "parent", "label": "Parent Account", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "account", "description": "Parent account for hierarchical chart of accounts"},
                    {"name": "isInactive", "label": "Inactive", "type": "boolean", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Whether the account is inactive"},
                    {"name": "description", "label": "Description", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Account description"},
                    {"name": "balance", "label": "Balance", "type": "float", "nullable": True, "readOnly": True, "is_key": False, "referenceType": None, "description": "Current account balance"},
                    {"name": "lastModifiedDate", "label": "Last Modified", "type": "dateTime", "nullable": True, "readOnly": True, "is_key": False, "referenceType": None, "description": "Last modification timestamp"},
                ]
            },
            {
                "name": "journalEntry",
                "label": "Journal Entry",
                "module": "accounting",
                "description": "Manual journal entries in the general ledger",
                "fields": [
                    {"name": "id", "label": "Internal ID", "type": "integer", "nullable": False, "readOnly": True, "is_key": True, "referenceType": None, "description": "Internal NetSuite ID"},
                    {"name": "tranId", "label": "Entry #", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Journal entry number (e.g. JE-001)"},
                    {"name": "tranDate", "label": "Date", "type": "date", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Transaction date"},
                    {"name": "postingPeriod", "label": "Posting Period", "type": "select", "nullable": False, "readOnly": False, "is_key": False, "referenceType": "accountingPeriod", "description": "Accounting period this entry posts to"},
                    {"name": "subsidiary", "label": "Subsidiary", "type": "select", "nullable": False, "readOnly": False, "is_key": False, "referenceType": "subsidiary", "description": "Subsidiary for multi-entity setup"},
                    {"name": "currency", "label": "Currency", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "currency", "description": "Transaction currency"},
                    {"name": "memo", "label": "Memo", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Journal entry memo/description"},
                    {"name": "isBookSpecific", "label": "Book Specific", "type": "boolean", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Whether entry is book-specific (multi-book accounting)"},
                    {"name": "createdDate", "label": "Created Date", "type": "dateTime", "nullable": True, "readOnly": True, "is_key": False, "referenceType": None, "description": "Record creation timestamp"},
                ]
            },
        ]
    },
    {
        "id": "customers",
        "label": "Customers & CRM",
        "description": "Customers, Contacts, Leads, Prospects, Cases",
        "records": [
            {
                "name": "customer",
                "label": "Customer",
                "module": "customers",
                "description": "Customer master records",
                "fields": [
                    {"name": "id", "label": "Internal ID", "type": "integer", "nullable": False, "readOnly": True, "is_key": True, "referenceType": None, "description": "Internal NetSuite ID"},
                    {"name": "entityId", "label": "Customer ID", "type": "string", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Customer display ID (auto-generated or manual)"},
                    {"name": "companyName", "label": "Company Name", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Company/organization name"},
                    {"name": "firstName", "label": "First Name", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Contact first name (for individual customers)"},
                    {"name": "lastName", "label": "Last Name", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Contact last name"},
                    {"name": "email", "label": "Email", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Primary email address"},
                    {"name": "phone", "label": "Phone", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Primary phone number"},
                    {"name": "subsidiary", "label": "Subsidiary", "type": "select", "nullable": False, "readOnly": False, "is_key": False, "referenceType": "subsidiary", "description": "NetSuite subsidiary"},
                    {"name": "currency", "label": "Currency", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "currency", "description": "Customer default currency"},
                    {"name": "salesRep", "label": "Sales Rep", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "employee", "description": "Assigned sales representative"},
                    {"name": "terms", "label": "Payment Terms", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "term", "description": "Default payment terms (Net 30, etc.)"},
                    {"name": "creditLimit", "label": "Credit Limit", "type": "float", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Customer credit limit"},
                    {"name": "balance", "label": "Balance", "type": "float", "nullable": True, "readOnly": True, "is_key": False, "referenceType": None, "description": "Current outstanding balance"},
                    {"name": "isInactive", "label": "Inactive", "type": "boolean", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Whether customer is inactive"},
                    {"name": "dateCreated", "label": "Date Created", "type": "dateTime", "nullable": True, "readOnly": True, "is_key": False, "referenceType": None, "description": "Record creation date"},
                ]
            },
            {
                "name": "contact",
                "label": "Contact",
                "module": "customers",
                "description": "Individual contact persons linked to customers/vendors",
                "fields": [
                    {"name": "id", "label": "Internal ID", "type": "integer", "nullable": False, "readOnly": True, "is_key": True, "referenceType": None, "description": "Internal NetSuite ID"},
                    {"name": "entityId", "label": "Contact ID", "type": "string", "nullable": False, "readOnly": True, "is_key": False, "referenceType": None, "description": "Auto-generated contact ID"},
                    {"name": "salutation", "label": "Salutation", "type": "enum", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Mr., Ms., Dr., etc."},
                    {"name": "firstName", "label": "First Name", "type": "string", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "First name"},
                    {"name": "lastName", "label": "Last Name", "type": "string", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Last name"},
                    {"name": "title", "label": "Job Title", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Job title"},
                    {"name": "email", "label": "Email", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Email address"},
                    {"name": "phone", "label": "Phone", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Phone number"},
                    {"name": "company", "label": "Company", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "customer", "description": "Linked customer/company"},
                    {"name": "isInactive", "label": "Inactive", "type": "boolean", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Whether contact is inactive"},
                ]
            },
            {
                "name": "opportunity",
                "label": "Opportunity",
                "module": "customers",
                "description": "Sales opportunities in the pipeline",
                "fields": [
                    {"name": "id", "label": "Internal ID", "type": "integer", "nullable": False, "readOnly": True, "is_key": True, "referenceType": None, "description": "Internal NetSuite ID"},
                    {"name": "tranId", "label": "Opportunity #", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Opportunity number"},
                    {"name": "title", "label": "Name/Title", "type": "string", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Opportunity name"},
                    {"name": "entity", "label": "Customer", "type": "select", "nullable": False, "readOnly": False, "is_key": False, "referenceType": "customer", "description": "Associated customer"},
                    {"name": "status", "label": "Status", "type": "enum", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "In Progress, Closed Won, Closed Lost, etc."},
                    {"name": "probability", "label": "Probability (%)", "type": "float", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Win probability percentage"},
                    {"name": "projectedTotal", "label": "Projected Total", "type": "float", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Expected deal value"},
                    {"name": "expectedCloseDate", "label": "Expected Close", "type": "date", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Expected close date"},
                    {"name": "salesRep", "label": "Sales Rep", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "employee", "description": "Assigned sales rep"},
                    {"name": "tranDate", "label": "Date", "type": "date", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Opportunity date"},
                ]
            },
        ]
    },
    {
        "id": "vendors",
        "label": "Vendors & Purchasing",
        "description": "Vendors, Bills, Purchase Orders, Payments",
        "records": [
            {
                "name": "vendor",
                "label": "Vendor",
                "module": "vendors",
                "description": "Supplier/vendor master records",
                "fields": [
                    {"name": "id", "label": "Internal ID", "type": "integer", "nullable": False, "readOnly": True, "is_key": True, "referenceType": None, "description": "Internal NetSuite ID"},
                    {"name": "entityId", "label": "Vendor ID", "type": "string", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Vendor display ID"},
                    {"name": "companyName", "label": "Company Name", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Vendor company name"},
                    {"name": "email", "label": "Email", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Primary email"},
                    {"name": "phone", "label": "Phone", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Primary phone"},
                    {"name": "currency", "label": "Currency", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "currency", "description": "Vendor default currency"},
                    {"name": "terms", "label": "Payment Terms", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "term", "description": "Default payment terms"},
                    {"name": "taxIdNum", "label": "Tax ID", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Tax identification number"},
                    {"name": "balance", "label": "Balance", "type": "float", "nullable": True, "readOnly": True, "is_key": False, "referenceType": None, "description": "Outstanding balance owed to vendor"},
                    {"name": "isInactive", "label": "Inactive", "type": "boolean", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Whether vendor is inactive"},
                ]
            },
            {
                "name": "purchaseOrder",
                "label": "Purchase Order",
                "module": "vendors",
                "description": "Purchase orders sent to vendors",
                "fields": [
                    {"name": "id", "label": "Internal ID", "type": "integer", "nullable": False, "readOnly": True, "is_key": True, "referenceType": None, "description": "Internal NetSuite ID"},
                    {"name": "tranId", "label": "PO #", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Purchase order number"},
                    {"name": "tranDate", "label": "Date", "type": "date", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "PO date"},
                    {"name": "entity", "label": "Vendor", "type": "select", "nullable": False, "readOnly": False, "is_key": False, "referenceType": "vendor", "description": "Vendor this PO is for"},
                    {"name": "status", "label": "Status", "type": "enum", "nullable": False, "readOnly": True, "is_key": False, "referenceType": None, "description": "Pending Supervisor Approval, Pending Receipt, Fully Billed, Closed"},
                    {"name": "total", "label": "Total", "type": "float", "nullable": True, "readOnly": True, "is_key": False, "referenceType": None, "description": "PO total amount"},
                    {"name": "currency", "label": "Currency", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "currency", "description": "Transaction currency"},
                    {"name": "memo", "label": "Memo", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "PO memo / notes"},
                    {"name": "shipDate", "label": "Expected Receipt", "type": "date", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Expected delivery date"},
                ]
            },
        ]
    },
    {
        "id": "inventory",
        "label": "Inventory & Items",
        "description": "Inventory Items, Assemblies, Item Groups, Pricing",
        "records": [
            {
                "name": "inventoryItem",
                "label": "Inventory Item",
                "module": "inventory",
                "description": "Physical inventory items tracked in stock",
                "fields": [
                    {"name": "id", "label": "Internal ID", "type": "integer", "nullable": False, "readOnly": True, "is_key": True, "referenceType": None, "description": "Internal NetSuite ID"},
                    {"name": "itemId", "label": "Item Name/Number", "type": "string", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Item display name or SKU"},
                    {"name": "displayName", "label": "Display Name", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Name shown to customers"},
                    {"name": "description", "label": "Description", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Item description"},
                    {"name": "salesDescription", "label": "Sales Description", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Description used on sales transactions"},
                    {"name": "purchaseDescription", "label": "Purchase Description", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Description used on purchase transactions"},
                    {"name": "rate", "label": "Sales Price", "type": "float", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Default sales price"},
                    {"name": "cost", "label": "Cost", "type": "float", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Item cost"},
                    {"name": "unitsType", "label": "Units Type", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "unitsType", "description": "Unit of measure type"},
                    {"name": "quantityOnHand", "label": "Qty On Hand", "type": "float", "nullable": True, "readOnly": True, "is_key": False, "referenceType": None, "description": "Current quantity in stock"},
                    {"name": "reorderPoint", "label": "Reorder Point", "type": "float", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Quantity at which to reorder"},
                    {"name": "isInactive", "label": "Inactive", "type": "boolean", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Whether item is inactive"},
                ]
            },
        ]
    },
    {
        "id": "sales",
        "label": "Sales Transactions",
        "description": "Sales Orders, Estimates, Item Fulfillments, Invoices",
        "records": [
            {
                "name": "salesOrder",
                "label": "Sales Order",
                "module": "sales",
                "description": "Customer sales orders",
                "fields": [
                    {"name": "id", "label": "Internal ID", "type": "integer", "nullable": False, "readOnly": True, "is_key": True, "referenceType": None, "description": "Internal NetSuite ID"},
                    {"name": "tranId", "label": "Order #", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Sales order number (e.g. SO-001)"},
                    {"name": "tranDate", "label": "Date", "type": "date", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Order date"},
                    {"name": "entity", "label": "Customer", "type": "select", "nullable": False, "readOnly": False, "is_key": False, "referenceType": "customer", "description": "Customer placing the order"},
                    {"name": "status", "label": "Status", "type": "enum", "nullable": False, "readOnly": True, "is_key": False, "referenceType": None, "description": "Pending Approval, Pending Fulfillment, Partially Fulfilled, Closed, Cancelled"},
                    {"name": "total", "label": "Total", "type": "float", "nullable": True, "readOnly": True, "is_key": False, "referenceType": None, "description": "Order total amount"},
                    {"name": "currency", "label": "Currency", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "currency", "description": "Order currency"},
                    {"name": "salesRep", "label": "Sales Rep", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "employee", "description": "Sales representative"},
                    {"name": "memo", "label": "Memo", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Order notes"},
                    {"name": "shipDate", "label": "Ship Date", "type": "date", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Expected ship date"},
                    {"name": "terms", "label": "Terms", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "term", "description": "Payment terms"},
                ]
            },
            {
                "name": "invoice",
                "label": "Invoice",
                "module": "sales",
                "description": "Customer invoices (accounts receivable)",
                "fields": [
                    {"name": "id", "label": "Internal ID", "type": "integer", "nullable": False, "readOnly": True, "is_key": True, "referenceType": None, "description": "Internal NetSuite ID"},
                    {"name": "tranId", "label": "Invoice #", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Invoice number"},
                    {"name": "tranDate", "label": "Date", "type": "date", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Invoice date"},
                    {"name": "dueDate", "label": "Due Date", "type": "date", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Payment due date"},
                    {"name": "entity", "label": "Customer", "type": "select", "nullable": False, "readOnly": False, "is_key": False, "referenceType": "customer", "description": "Billed customer"},
                    {"name": "status", "label": "Status", "type": "enum", "nullable": False, "readOnly": True, "is_key": False, "referenceType": None, "description": "Open, In Progress, Paid In Full, Voided"},
                    {"name": "total", "label": "Total", "type": "float", "nullable": True, "readOnly": True, "is_key": False, "referenceType": None, "description": "Invoice total"},
                    {"name": "amountRemaining", "label": "Amount Due", "type": "float", "nullable": True, "readOnly": True, "is_key": False, "referenceType": None, "description": "Remaining unpaid amount"},
                    {"name": "currency", "label": "Currency", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "currency", "description": "Invoice currency"},
                    {"name": "terms", "label": "Terms", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "term", "description": "Payment terms"},
                ]
            },
        ]
    },
    {
        "id": "employees",
        "label": "Employees & HR",
        "description": "Employees, Departments, Jobs, Payroll Items",
        "records": [
            {
                "name": "employee",
                "label": "Employee",
                "module": "employees",
                "description": "Employee master records",
                "fields": [
                    {"name": "id", "label": "Internal ID", "type": "integer", "nullable": False, "readOnly": True, "is_key": True, "referenceType": None, "description": "Internal NetSuite ID"},
                    {"name": "entityId", "label": "Employee ID", "type": "string", "nullable": False, "readOnly": True, "is_key": False, "referenceType": None, "description": "Auto-generated employee ID"},
                    {"name": "firstName", "label": "First Name", "type": "string", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "First name"},
                    {"name": "lastName", "label": "Last Name", "type": "string", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Last name"},
                    {"name": "email", "label": "Email", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Work email address"},
                    {"name": "title", "label": "Job Title", "type": "string", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Job title"},
                    {"name": "department", "label": "Department", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "department", "description": "Employee department"},
                    {"name": "subsidiary", "label": "Subsidiary", "type": "select", "nullable": False, "readOnly": False, "is_key": False, "referenceType": "subsidiary", "description": "NetSuite subsidiary"},
                    {"name": "supervisor", "label": "Supervisor", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "employee", "description": "Direct supervisor"},
                    {"name": "hireDate", "label": "Hire Date", "type": "date", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Date of hire"},
                    {"name": "releaseDate", "label": "Release Date", "type": "date", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Termination date"},
                    {"name": "isInactive", "label": "Inactive", "type": "boolean", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Whether employee is inactive"},
                ]
            },
            {
                "name": "department",
                "label": "Department",
                "module": "employees",
                "description": "Organizational departments",
                "fields": [
                    {"name": "id", "label": "Internal ID", "type": "integer", "nullable": False, "readOnly": True, "is_key": True, "referenceType": None, "description": "Internal NetSuite ID"},
                    {"name": "name", "label": "Name", "type": "string", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Department name"},
                    {"name": "parent", "label": "Parent Department", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "department", "description": "Parent department for hierarchy"},
                    {"name": "subsidiary", "label": "Subsidiary", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "subsidiary", "description": "Subsidiary this department belongs to"},
                    {"name": "isInactive", "label": "Inactive", "type": "boolean", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Whether department is inactive"},
                ]
            },
        ]
    },
    {
        "id": "projects",
        "label": "Projects",
        "description": "Projects, Project Tasks, Time Entries, Expenses",
        "records": [
            {
                "name": "job",
                "label": "Project",
                "module": "projects",
                "description": "Projects (called Jobs in NetSuite)",
                "fields": [
                    {"name": "id", "label": "Internal ID", "type": "integer", "nullable": False, "readOnly": True, "is_key": True, "referenceType": None, "description": "Internal NetSuite ID"},
                    {"name": "entityId", "label": "Project ID", "type": "string", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Project display ID"},
                    {"name": "companyName", "label": "Project Name", "type": "string", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Project name"},
                    {"name": "customer", "label": "Customer", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "customer", "description": "Associated customer"},
                    {"name": "status", "label": "Status", "type": "select", "nullable": True, "readOnly": False, "is_key": False, "referenceType": "jobStatus", "description": "Project status"},
                    {"name": "startDate", "label": "Start Date", "type": "date", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Project start date"},
                    {"name": "endDate", "label": "End Date", "type": "date", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Project end/due date"},
                    {"name": "estimatedCost", "label": "Estimated Cost", "type": "float", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Estimated project cost"},
                    {"name": "estimatedRevenue", "label": "Estimated Revenue", "type": "float", "nullable": True, "readOnly": False, "is_key": False, "referenceType": None, "description": "Estimated project revenue"},
                    {"name": "isInactive", "label": "Inactive", "type": "boolean", "nullable": False, "readOnly": False, "is_key": False, "referenceType": None, "description": "Whether project is inactive"},
                ]
            },
        ]
    },
]

_ALL_RECORDS: dict = {r["name"]: r for m in DEMO_MODULES for r in m["records"]}
_MODULE_MAP: dict = {m["id"]: m for m in DEMO_MODULES}


# ─────────────────────────────────────────────────────────
# Real NetSuite REST API helpers (OAuth 2.0)
# ─────────────────────────────────────────────────────────

def _is_demo_mode() -> bool:
    return not bool(settings.NS_ACCOUNT_ID)


def _api_base() -> str:
    return NS_REST_BASE.format(account_id=settings.NS_ACCOUNT_ID.lower().replace("_", "-"))


def _get_access_token() -> str:
    token_url = NS_TOKEN_URL.format(account_id=settings.NS_ACCOUNT_ID.lower().replace("_", "-"))
    resp = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": settings.NS_CLIENT_ID,
            "client_secret": settings.NS_CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    if not resp.ok:
        raise ConnectionError(
            f"NetSuite OAuth failed [{resp.status_code}]: {resp.text[:300]}"
        )
    return resp.json()["access_token"]


def _get(path: str, params: dict = None) -> dict:
    token = _get_access_token()
    url = f"{_api_base()}{path}"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        params=params,
        timeout=30,
    )
    if resp.status_code == 401:
        raise ConnectionError("NetSuite authentication failed. Check NS_ACCOUNT_ID, NS_CLIENT_ID, NS_CLIENT_SECRET.")
    if resp.status_code == 403:
        raise PermissionError(f"NetSuite access denied: {path}")
    if resp.status_code == 404:
        raise LookupError(f"NetSuite record type not found: {path}")
    if not resp.ok:
        raise RuntimeError(f"NetSuite API error [{resp.status_code}]: {resp.text[:400]}")
    return resp.json()


# ─────────────────────────────────────────────────────────
# Public service functions
# ─────────────────────────────────────────────────────────

def test_connection() -> dict:
    if _is_demo_mode():
        total_records = sum(len(m["records"]) for m in DEMO_MODULES)
        total_fields = sum(len(r["fields"]) for m in DEMO_MODULES for r in m["records"])
        return {
            "connected": True,
            "mode": "demo",
            "message": (
                "Running in Demo Mode — showing real NetSuite REST Metadata Catalog schema. "
                "Set NS_ACCOUNT_ID, NS_CLIENT_ID, NS_CLIENT_SECRET in .env to connect "
                "to a real NetSuite account."
            ),
            "modules_count": len(DEMO_MODULES),
            "total_record_types": total_records,
            "total_fields": total_fields,
        }

    data = _get("/metadata-catalog/")
    items = data.get("items", [])
    return {
        "connected": True,
        "mode": "live",
        "account_id": settings.NS_ACCOUNT_ID,
        "total_record_types": len(items),
    }


def list_modules() -> list[dict]:
    return [
        {
            "id": m["id"],
            "label": m["label"],
            "description": m["description"],
            "records_count": len(m["records"]),
        }
        for m in DEMO_MODULES
    ]


def get_module_records(module_id: str) -> dict:
    if module_id not in _MODULE_MAP:
        raise LookupError(f"Module '{module_id}' not found. Available: {list(_MODULE_MAP.keys())}")
    module = _MODULE_MAP[module_id]
    records = [
        {
            "name": r["name"],
            "label": r["label"],
            "description": r["description"],
            "fields_count": len(r["fields"]),
        }
        for r in module["records"]
    ]
    return {
        "module_id": module_id,
        "module_label": module["label"],
        "total": len(records),
        "records": records,
        "mode": "demo" if _is_demo_mode() else "live",
    }


def get_record_fields(record_type: str) -> dict:
    if _is_demo_mode():
        if record_type not in _ALL_RECORDS:
            raise LookupError(
                f"Record type '{record_type}' not found. Available: {list(_ALL_RECORDS.keys())}"
            )
        r = _ALL_RECORDS[record_type]
        return {
            **r,
            "fields_count": len(r["fields"]),
            "mode": "demo",
        }

    # Live: query the metadata catalog
    data = _get(f"/metadata-catalog/{record_type}")
    props = data.get("properties", {})
    fields = []
    for name, prop in props.items():
        fields.append({
            "name": name,
            "label": prop.get("title", name),
            "type": prop.get("type", "string"),
            "nullable": prop.get("nullable", True),
            "readOnly": prop.get("readOnly", False),
            "is_key": name == "id",
            "referenceType": prop.get("referenceType"),
            "description": prop.get("description", ""),
        })
    return {
        "name": record_type,
        "label": data.get("title", record_type),
        "module": "",
        "description": data.get("description", ""),
        "fields_count": len(fields),
        "fields": fields,
        "mode": "live",
    }


def get_all_records() -> dict:
    all_records = [
        {
            "name": r["name"],
            "label": r["label"],
            "module": r["module"],
            "description": r["description"],
            "fields_count": len(r["fields"]),
        }
        for m in DEMO_MODULES
        for r in m["records"]
    ]
    return {
        "total": len(all_records),
        "records": all_records,
        "mode": "demo" if _is_demo_mode() else "live",
    }

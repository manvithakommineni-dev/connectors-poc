"""
Oracle Fusion Cloud ERP connectivity and metadata retrieval service.

How Oracle Fusion exposes metadata:
  Oracle Fusion Cloud ERP uses REST APIs under /fscmRestApi/resources/latest/.
  Every resource (table/business object) has a /describe endpoint that returns:
    - Attributes (columns/fields): name, type, required, queryable, updatable
    - Child resources (related sub-tables / nested collections)
    - Links (navigation, HATEOAS)

  Equivalent concepts:
    Salesforce SObject     → Oracle Resource
    Salesforce Field       → Oracle Attribute
    Salesforce Relationship→ Oracle Child Resource
    SAP EntityType         → Oracle Resource
    SAP NavigationProperty → Oracle Child Resource

Authentication:
  Basic Auth: ORACLE_USERNAME + ORACLE_PASSWORD  (most common for Oracle Cloud)
  The base URL is your Oracle Cloud instance hostname.

Setup (real Oracle Cloud):
  1. Get your Oracle Cloud ERP hostname (e.g. abc-test.fa.oc1.oraclecloud.com)
  2. Use your Oracle Cloud username and password
  3. Set ORACLE_BASE_URL, ORACLE_USERNAME, ORACLE_PASSWORD in backend/.env

Demo Mode (no Oracle instance needed):
  If ORACLE_BASE_URL is empty, the service returns built-in demo metadata based on
  real Oracle Fusion ERP schema. Covers Financials, Procurement, HCM, Order Mgmt,
  Projects, and Supply Chain modules. Use this to explore the structure without
  needing an Oracle subscription.
"""

import requests
import logging
from requests.auth import HTTPBasicAuth
from core.config import settings
from typing import Optional

logger = logging.getLogger(__name__)

# Oracle Fusion Cloud ERP REST API base path
ORACLE_API_PATH = "/fscmRestApi/resources/latest"

# ─────────────────────────────────────────────────────────────────
# Built-in demo metadata — real Oracle Fusion ERP schema structure
# Covers the 6 major modules with representative resources + fields
# ─────────────────────────────────────────────────────────────────
DEMO_MODULES = [
    {
        "id": "financials",
        "label": "Financials",
        "description": "Accounts Payable, Accounts Receivable, General Ledger, Fixed Assets, Cash Management",
        "resources": [
            {
                "name": "invoices",
                "title": "AP Invoices",
                "module": "financials",
                "description": "Supplier invoices in Accounts Payable",
                "attributes": [
                    {"name": "InvoiceId", "title": "Invoice ID", "type": "integer", "required": True, "queryable": True, "updatable": False, "is_key": True, "max_length": None},
                    {"name": "InvoiceNumber", "title": "Invoice Number", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 50},
                    {"name": "InvoiceDate", "title": "Invoice Date", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "SupplierId", "title": "Supplier ID", "type": "integer", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "SupplierName", "title": "Supplier Name", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": 360},
                    {"name": "InvoiceAmount", "title": "Invoice Amount", "type": "number", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "CurrencyCode", "title": "Currency Code", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 15},
                    {"name": "PaymentStatus", "title": "Payment Status", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": 25},
                    {"name": "DueDate", "title": "Due Date", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "InvoiceStatus", "title": "Invoice Status", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": 25},
                    {"name": "LegalEntityId", "title": "Legal Entity ID", "type": "integer", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "BusinessUnit", "title": "Business Unit", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 240},
                    {"name": "Description", "title": "Description", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": 240},
                    {"name": "CreationDate", "title": "Creation Date", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": None},
                    {"name": "LastUpdateDate", "title": "Last Update Date", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": None},
                ],
                "children": [
                    {"name": "invoiceLines", "title": "Invoice Lines", "description": "Line items on an AP Invoice"},
                    {"name": "invoicePayments", "title": "Invoice Payments", "description": "Payment records for an invoice"},
                ]
            },
            {
                "name": "receivablesInvoices",
                "title": "AR Invoices",
                "module": "financials",
                "description": "Customer invoices in Accounts Receivable",
                "attributes": [
                    {"name": "CustomerTransactionId", "title": "Transaction ID", "type": "integer", "required": True, "queryable": True, "updatable": False, "is_key": True, "max_length": None},
                    {"name": "TransactionNumber", "title": "Transaction Number", "type": "string", "required": True, "queryable": True, "updatable": False, "is_key": False, "max_length": 20},
                    {"name": "CustomerId", "title": "Customer ID", "type": "integer", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "CustomerName", "title": "Customer Name", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": 360},
                    {"name": "TransactionDate", "title": "Transaction Date", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "DueDate", "title": "Due Date", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "Amount", "title": "Amount", "type": "number", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "CurrencyCode", "title": "Currency", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 15},
                    {"name": "Status", "title": "Status", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": 30},
                    {"name": "BusinessUnit", "title": "Business Unit", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 240},
                ],
                "children": [
                    {"name": "receivablesInvoiceLines", "title": "Invoice Lines", "description": "AR Invoice line items"},
                ]
            },
            {
                "name": "generalLedgerJournals",
                "title": "GL Journals",
                "module": "financials",
                "description": "General Ledger journal entries",
                "attributes": [
                    {"name": "JournalId", "title": "Journal ID", "type": "integer", "required": True, "queryable": True, "updatable": False, "is_key": True, "max_length": None},
                    {"name": "JournalName", "title": "Journal Name", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 100},
                    {"name": "JournalSource", "title": "Journal Source", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 25},
                    {"name": "LedgerId", "title": "Ledger ID", "type": "integer", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "AccountingDate", "title": "Accounting Date", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "TotalDebitAmount", "title": "Total Debit", "type": "number", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": None},
                    {"name": "TotalCreditAmount", "title": "Total Credit", "type": "number", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": None},
                    {"name": "Status", "title": "Status", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": 25},
                    {"name": "PeriodName", "title": "Period Name", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 15},
                    {"name": "CurrencyCode", "title": "Currency", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 15},
                ],
                "children": [
                    {"name": "generalLedgerJournalLines", "title": "Journal Lines", "description": "Individual debit/credit lines"},
                ]
            },
        ]
    },
    {
        "id": "procurement",
        "label": "Procurement",
        "description": "Purchase Orders, Suppliers, Purchasing Contracts, Requisitions",
        "resources": [
            {
                "name": "purchaseOrders",
                "title": "Purchase Orders",
                "module": "procurement",
                "description": "Purchase orders sent to suppliers",
                "attributes": [
                    {"name": "POHeaderId", "title": "PO Header ID", "type": "integer", "required": True, "queryable": True, "updatable": False, "is_key": True, "max_length": None},
                    {"name": "PONumber", "title": "PO Number", "type": "string", "required": True, "queryable": True, "updatable": False, "is_key": False, "max_length": 20},
                    {"name": "SupplierId", "title": "Supplier ID", "type": "integer", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "SupplierName", "title": "Supplier Name", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": 360},
                    {"name": "OrderDate", "title": "Order Date", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "Status", "title": "Status", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": 25},
                    {"name": "Amount", "title": "Order Amount", "type": "number", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": None},
                    {"name": "CurrencyCode", "title": "Currency", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 15},
                    {"name": "BuyerId", "title": "Buyer ID", "type": "integer", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "BusinessUnitId", "title": "Business Unit ID", "type": "integer", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "ShipToLocationId", "title": "Ship-To Location", "type": "integer", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "Description", "title": "Description", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": 240},
                ],
                "children": [
                    {"name": "purchaseOrderLines", "title": "PO Lines", "description": "Line items on the purchase order"},
                    {"name": "purchaseOrderSchedules", "title": "Schedules", "description": "Delivery schedules"},
                    {"name": "purchaseOrderDistributions", "title": "Distributions", "description": "Account distributions"},
                ]
            },
            {
                "name": "suppliers",
                "title": "Suppliers",
                "module": "procurement",
                "description": "Supplier (vendor) master data",
                "attributes": [
                    {"name": "SupplierId", "title": "Supplier ID", "type": "integer", "required": True, "queryable": True, "updatable": False, "is_key": True, "max_length": None},
                    {"name": "SupplierNumber", "title": "Supplier Number", "type": "string", "required": True, "queryable": True, "updatable": False, "is_key": False, "max_length": 30},
                    {"name": "SupplierName", "title": "Supplier Name", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 360},
                    {"name": "Status", "title": "Status", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": 25},
                    {"name": "SupplierType", "title": "Supplier Type", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": 30},
                    {"name": "TaxRegistrationNumber", "title": "Tax Reg Number", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": 50},
                    {"name": "AlternateSupplierName", "title": "Alternate Name", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": 360},
                    {"name": "CreationDate", "title": "Creation Date", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": None},
                ],
                "children": [
                    {"name": "supplierAddresses", "title": "Supplier Addresses", "description": "Addresses for the supplier"},
                    {"name": "supplierContacts", "title": "Supplier Contacts", "description": "Contact persons at the supplier"},
                    {"name": "supplierSites", "title": "Supplier Sites", "description": "Transaction sites / locations"},
                ]
            },
        ]
    },
    {
        "id": "orderManagement",
        "label": "Order Management",
        "description": "Sales Orders, Customers, Pricing, Fulfillment",
        "resources": [
            {
                "name": "salesOrders",
                "title": "Sales Orders",
                "module": "orderManagement",
                "description": "Customer sales orders",
                "attributes": [
                    {"name": "OrderId", "title": "Order ID", "type": "integer", "required": True, "queryable": True, "updatable": False, "is_key": True, "max_length": None},
                    {"name": "OrderNumber", "title": "Order Number", "type": "string", "required": True, "queryable": True, "updatable": False, "is_key": False, "max_length": 40},
                    {"name": "CustomerId", "title": "Customer ID", "type": "integer", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "CustomerName", "title": "Customer Name", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": 360},
                    {"name": "OrderDate", "title": "Order Date", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "RequestedShipDate", "title": "Requested Ship Date", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "Status", "title": "Order Status", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": 30},
                    {"name": "OrderAmount", "title": "Order Amount", "type": "number", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": None},
                    {"name": "CurrencyCode", "title": "Currency", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 15},
                    {"name": "BusinessUnitId", "title": "Business Unit", "type": "integer", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "ShipToCustomerId", "title": "Ship-To Customer ID", "type": "integer", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "BillToCustomerId", "title": "Bill-To Customer ID", "type": "integer", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                ],
                "children": [
                    {"name": "salesOrderLines", "title": "Order Lines", "description": "Line items in the sales order"},
                    {"name": "fulfillmentLines", "title": "Fulfillment Lines", "description": "Fulfillment and shipping details"},
                ]
            },
            {
                "name": "customers",
                "title": "Customers",
                "module": "orderManagement",
                "description": "Customer master data (Trading Community Architecture)",
                "attributes": [
                    {"name": "PartyId", "title": "Party ID", "type": "integer", "required": True, "queryable": True, "updatable": False, "is_key": True, "max_length": None},
                    {"name": "CustomerNumber", "title": "Customer Number", "type": "string", "required": True, "queryable": True, "updatable": False, "is_key": False, "max_length": 30},
                    {"name": "CustomerName", "title": "Customer Name", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 360},
                    {"name": "Status", "title": "Status", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": 1},
                    {"name": "CustomerType", "title": "Customer Type", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": 30},
                    {"name": "TaxpayerIdentificationNumber", "title": "Tax ID", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": 20},
                    {"name": "CreationDate", "title": "Creation Date", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": None},
                    {"name": "LastUpdateDate", "title": "Last Update", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": None},
                ],
                "children": [
                    {"name": "customerAccounts", "title": "Customer Accounts", "description": "Billing accounts for the customer"},
                    {"name": "customerAddresses", "title": "Customer Addresses", "description": "Addresses and sites"},
                    {"name": "customerContacts", "title": "Customer Contacts", "description": "Contact persons"},
                ]
            },
        ]
    },
    {
        "id": "hcm",
        "label": "Human Capital Management",
        "description": "Employees, Jobs, Departments, Payroll, Absence",
        "resources": [
            {
                "name": "workers",
                "title": "Workers / Employees",
                "module": "hcm",
                "description": "Employee and contractor records",
                "attributes": [
                    {"name": "PersonId", "title": "Person ID", "type": "integer", "required": True, "queryable": True, "updatable": False, "is_key": True, "max_length": None},
                    {"name": "PersonNumber", "title": "Person Number", "type": "string", "required": True, "queryable": True, "updatable": False, "is_key": False, "max_length": 30},
                    {"name": "FirstName", "title": "First Name", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 150},
                    {"name": "LastName", "title": "Last Name", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 150},
                    {"name": "DisplayName", "title": "Display Name", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": 360},
                    {"name": "EmailAddress", "title": "Email", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": 240},
                    {"name": "WorkerType", "title": "Worker Type", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 30},
                    {"name": "DepartmentId", "title": "Department ID", "type": "integer", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "JobId", "title": "Job ID", "type": "integer", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "LocationId", "title": "Location ID", "type": "integer", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "HireDate", "title": "Hire Date", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "TerminationDate", "title": "Termination Date", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                ],
                "children": [
                    {"name": "assignments", "title": "Assignments", "description": "Current and historical job assignments"},
                    {"name": "salaries", "title": "Salaries", "description": "Salary components and history"},
                    {"name": "absences", "title": "Absences", "description": "Absence and leave records"},
                ]
            },
            {
                "name": "departments",
                "title": "Departments",
                "module": "hcm",
                "description": "Organizational departments",
                "attributes": [
                    {"name": "DepartmentId", "title": "Department ID", "type": "integer", "required": True, "queryable": True, "updatable": False, "is_key": True, "max_length": None},
                    {"name": "DepartmentName", "title": "Department Name", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 240},
                    {"name": "OrganizationId", "title": "Organization ID", "type": "integer", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "LocationId", "title": "Location ID", "type": "integer", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "ManagerId", "title": "Manager ID", "type": "integer", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "EffectiveStartDate", "title": "Effective Start Date", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "EffectiveEndDate", "title": "Effective End Date", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                ],
                "children": []
            },
        ]
    },
    {
        "id": "projects",
        "label": "Project Management",
        "description": "Projects, Tasks, Resources, Budgets, Costs",
        "resources": [
            {
                "name": "projects",
                "title": "Projects",
                "module": "projects",
                "description": "Project master records",
                "attributes": [
                    {"name": "ProjectId", "title": "Project ID", "type": "integer", "required": True, "queryable": True, "updatable": False, "is_key": True, "max_length": None},
                    {"name": "ProjectNumber", "title": "Project Number", "type": "string", "required": True, "queryable": True, "updatable": False, "is_key": False, "max_length": 25},
                    {"name": "ProjectName", "title": "Project Name", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 240},
                    {"name": "ProjectStatus", "title": "Status", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": 30},
                    {"name": "ProjectType", "title": "Project Type", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 20},
                    {"name": "StartDate", "title": "Start Date", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "CompletionDate", "title": "Completion Date", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "ProjectManagerId", "title": "Project Manager ID", "type": "integer", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "OrganizationId", "title": "Organization ID", "type": "integer", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "BudgetAmount", "title": "Budget Amount", "type": "number", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "CurrencyCode", "title": "Currency", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 15},
                ],
                "children": [
                    {"name": "tasks", "title": "Tasks", "description": "Project tasks and milestones"},
                    {"name": "projectResources", "title": "Resources", "description": "Team members assigned to the project"},
                    {"name": "projectCosts", "title": "Project Costs", "description": "Cost transactions for the project"},
                ]
            },
        ]
    },
    {
        "id": "supplyChain",
        "label": "Supply Chain Management",
        "description": "Inventory, Items, Work Orders, Shipments",
        "resources": [
            {
                "name": "inventoryItems",
                "title": "Inventory Items",
                "module": "supplyChain",
                "description": "Product/item master records",
                "attributes": [
                    {"name": "InventoryItemId", "title": "Item ID", "type": "integer", "required": True, "queryable": True, "updatable": False, "is_key": True, "max_length": None},
                    {"name": "ItemNumber", "title": "Item Number", "type": "string", "required": True, "queryable": True, "updatable": False, "is_key": False, "max_length": 300},
                    {"name": "ItemDescription", "title": "Description", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 240},
                    {"name": "ItemStatus", "title": "Item Status", "type": "string", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": 30},
                    {"name": "ItemType", "title": "Item Type", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 30},
                    {"name": "PrimaryUOMCode", "title": "Unit of Measure", "type": "string", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": 3},
                    {"name": "OrganizationId", "title": "Organization ID", "type": "integer", "required": True, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "CostingEnabled", "title": "Costing Enabled", "type": "boolean", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "TrackingEnabled", "title": "Tracking Enabled", "type": "boolean", "required": False, "queryable": True, "updatable": True, "is_key": False, "max_length": None},
                    {"name": "CreationDate", "title": "Creation Date", "type": "string", "required": False, "queryable": True, "updatable": False, "is_key": False, "max_length": None},
                ],
                "children": [
                    {"name": "itemRevisions", "title": "Item Revisions", "description": "Version history of the item"},
                    {"name": "itemCategories", "title": "Item Categories", "description": "Category assignments"},
                ]
            },
        ]
    },
]

# Flatten all resources for quick lookup
_ALL_RESOURCES = {r["name"]: r for m in DEMO_MODULES for r in m["resources"]}
_MODULE_MAP = {m["id"]: m for m in DEMO_MODULES}


# ─────────────────────────────────────────────
# Real Oracle Fusion REST API helpers
# ─────────────────────────────────────────────

def _is_demo_mode() -> bool:
    return not bool(settings.ORACLE_BASE_URL)


def _base_url() -> str:
    return settings.ORACLE_BASE_URL.rstrip("/")


def _auth() -> Optional[HTTPBasicAuth]:
    if settings.ORACLE_USERNAME and settings.ORACLE_PASSWORD:
        return HTTPBasicAuth(settings.ORACLE_USERNAME, settings.ORACLE_PASSWORD)
    return None


def _get(path: str) -> dict:
    url = f"{_base_url()}{ORACLE_API_PATH}{path}"
    resp = requests.get(
        url,
        auth=_auth(),
        headers={"Accept": "application/json"},
        timeout=30,
    )
    if resp.status_code == 401:
        raise ConnectionError(
            "Oracle authentication failed. Check ORACLE_USERNAME and ORACLE_PASSWORD in .env"
        )
    if resp.status_code == 403:
        raise PermissionError(f"Oracle access denied for {path}")
    if resp.status_code == 404:
        raise LookupError(f"Oracle resource not found: {path}")
    if not resp.ok:
        raise RuntimeError(f"Oracle API error [{resp.status_code}]: {resp.text[:400]}")
    return resp.json()


def _parse_real_resource(data: dict, resource_name: str, module_id: str = "") -> dict:
    """Parse Oracle Fusion REST describe response into our standard format."""
    attributes = []
    for attr in data.get("attributes", []):
        attributes.append({
            "name": attr.get("name", ""),
            "title": attr.get("title", attr.get("name", "")),
            "type": attr.get("type", "string"),
            "required": attr.get("required", False),
            "queryable": attr.get("queryable", True),
            "updatable": attr.get("updatable", True),
            "is_key": attr.get("idAttribute", False),
            "max_length": attr.get("maximum"),
        })
    children = [
        {"name": c.get("name", ""), "title": c.get("title", ""), "description": ""}
        for c in data.get("children", [])
    ]
    return {
        "name": resource_name,
        "title": data.get("title", resource_name),
        "module": module_id,
        "description": data.get("description", ""),
        "attributes": attributes,
        "children": children,
        "attributes_count": len(attributes),
        "children_count": len(children),
        "mode": "live",
    }


# ─────────────────────────────────────────────
# Public service functions
# ─────────────────────────────────────────────

def test_connection() -> dict:
    """Test Oracle connectivity. Returns demo info if no base URL configured."""
    if _is_demo_mode():
        total_resources = sum(len(m["resources"]) for m in DEMO_MODULES)
        return {
            "connected": True,
            "mode": "demo",
            "message": "Running in Demo Mode — showing real Oracle Fusion ERP schema structure. "
                       "Set ORACLE_BASE_URL, ORACLE_USERNAME, ORACLE_PASSWORD in .env to connect to a real Oracle Cloud instance.",
            "modules_count": len(DEMO_MODULES),
            "total_resources": total_resources,
            "oracle_api_path": ORACLE_API_PATH,
        }

    # Live mode
    data = _get("/")
    return {
        "connected": True,
        "mode": "live",
        "base_url": _base_url(),
        "items_count": len(data.get("items", [])),
    }


def list_modules() -> list[dict]:
    """List Oracle ERP modules (Financials, Procurement, HCM, etc.)."""
    if _is_demo_mode():
        return [
            {
                "id": m["id"],
                "label": m["label"],
                "description": m["description"],
                "resources_count": len(m["resources"]),
            }
            for m in DEMO_MODULES
        ]

    # Live: Oracle doesn't have a module concept in REST — return resource list grouped
    data = _get("/")
    items = data.get("items", [])
    return [{"id": it.get("name", ""), "label": it.get("title", ""), "description": "", "resources_count": 1} for it in items]


def get_module_resources(module_id: str) -> dict:
    """List all resources (tables) within a module."""
    if _is_demo_mode():
        if module_id not in _MODULE_MAP:
            raise LookupError(f"Module '{module_id}' not found. Available: {list(_MODULE_MAP.keys())}")
        module = _MODULE_MAP[module_id]
        resources = [
            {
                "name": r["name"],
                "title": r["title"],
                "description": r["description"],
                "attributes_count": len(r["attributes"]),
                "children_count": len(r["children"]),
            }
            for r in module["resources"]
        ]
        return {
            "module_id": module_id,
            "module_label": module["label"],
            "total": len(resources),
            "resources": resources,
            "mode": "demo",
        }

    # Live: describe the resource group
    data = _get(f"/{module_id}")
    items = data.get("items", [])
    resources = [
        {"name": it.get("name"), "title": it.get("title", ""), "description": "", "attributes_count": 0, "children_count": 0}
        for it in items
    ]
    return {"module_id": module_id, "module_label": module_id, "total": len(resources), "resources": resources, "mode": "live"}


def get_resource_describe(resource_name: str) -> dict:
    """
    Full metadata for an Oracle resource: attributes (fields), children (related tables).
    resource_name can be a top-level resource (e.g. 'invoices') or module/resource path.
    """
    if _is_demo_mode():
        if resource_name not in _ALL_RESOURCES:
            available = list(_ALL_RESOURCES.keys())
            raise LookupError(
                f"Resource '{resource_name}' not found in demo data. "
                f"Available: {available}"
            )
        r = _ALL_RESOURCES[resource_name]
        return {
            **r,
            "attributes_count": len(r["attributes"]),
            "children_count": len(r["children"]),
            "mode": "demo",
        }

    # Live
    data = _get(f"/{resource_name}/describe")
    return _parse_real_resource(data, resource_name)


def get_all_resources() -> dict:
    """Flat list of all resources across all modules."""
    if _is_demo_mode():
        all_resources = []
        for m in DEMO_MODULES:
            for r in m["resources"]:
                all_resources.append({
                    "name": r["name"],
                    "title": r["title"],
                    "module": r["module"],
                    "description": r["description"],
                    "attributes_count": len(r["attributes"]),
                    "children_count": len(r["children"]),
                })
        return {
            "total": len(all_resources),
            "resources": all_resources,
            "mode": "demo",
        }

    data = _get("/")
    items = data.get("items", [])
    return {
        "total": len(items),
        "resources": [{"name": it.get("name"), "title": it.get("title", ""), "module": "", "description": "", "attributes_count": 0, "children_count": 0} for it in items],
        "mode": "live",
    }

"""
Workday connectivity and metadata retrieval service.

How Workday exposes metadata:
  Workday uses REST APIs under /api/v1/{tenant}/.
  Every endpoint returns structured JSON objects with well-defined fields.
  Workday organises data into "Business Objects" grouped by functional areas (modules).

  Workday REST API equivalent concepts:
    Salesforce SObject      → Workday Business Object (e.g. Worker, Organization)
    Salesforce Field        → Workday Field (e.g. workerId, name, hireDate)
    Salesforce Relationship → Workday Nested Object / Related Resource
    SAP EntityType          → Workday Business Object
    Oracle Resource         → Workday Business Object

  Key Workday modules:
    Human Resources   → Workers, Positions, Job Profiles, Organizations, Locations
    Payroll           → Pay Groups, Payroll Results, Earnings, Deductions
    Recruiting        → Job Requisitions, Applications, Candidates, Offers
    Benefits          → Benefit Plans, Elections, Dependents
    Time & Absence    → Time Off Types, Absence Requests, Time Entries
    Learning          → Courses, Content, Enrollments

Authentication (real Workday):
  OAuth 2.0 Client Credentials grant:
    1. Register an API Client in Workday (Workday > Security > OAuth 2.0 Clients)
    2. Get: client_id, client_secret, tenant name
    3. Token URL: https://{tenant}.workday.com/oauth2/token
    4. API Base:  https://{tenant}.workday.com/api/v1/{tenant}

Demo Mode (no Workday instance needed):
  If WORKDAY_TENANT is empty, the service returns built-in demo metadata based on
  the real Workday REST API schema. Covers HCM, Payroll, Recruiting, Benefits,
  Time & Absence, and Learning modules.
"""

import requests
import logging
from requests.auth import HTTPBasicAuth
from core.config import settings

logger = logging.getLogger(__name__)

WORKDAY_TOKEN_PATH = "/oauth2/token"
WORKDAY_API_PATH = "/api/v1"

# ─────────────────────────────────────────────────────────────────────────────
# Built-in demo metadata — real Workday REST API schema structure
# ─────────────────────────────────────────────────────────────────────────────
DEMO_MODULES = [
    {
        "id": "humanResources",
        "label": "Human Resources",
        "description": "Workers, Positions, Job Profiles, Organizations, Locations, Compensation",
        "objects": [
            {
                "name": "workers",
                "title": "Workers",
                "module": "humanResources",
                "rest_path": "/workers",
                "description": "All workers (employees and contingent workers) in Workday",
                "fields": [
                    {"name": "workerId", "title": "Worker ID", "type": "string", "required": True, "filterable": True, "is_key": True, "description": "Unique identifier for the worker"},
                    {"name": "workerType", "title": "Worker Type", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Employee or Contingent Worker"},
                    {"name": "firstName", "title": "First Name", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Legal first name"},
                    {"name": "lastName", "title": "Last Name", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Legal last name"},
                    {"name": "preferredName", "title": "Preferred Name", "type": "string", "required": False, "filterable": True, "is_key": False, "description": "Name used in day-to-day work"},
                    {"name": "primaryEmail", "title": "Primary Email", "type": "string", "required": False, "filterable": True, "is_key": False, "description": "Primary work email address"},
                    {"name": "primaryPhone", "title": "Primary Phone", "type": "string", "required": False, "filterable": False, "is_key": False, "description": "Primary work phone number"},
                    {"name": "hireDate", "title": "Hire Date", "type": "date", "required": True, "filterable": True, "is_key": False, "description": "Date the worker was hired"},
                    {"name": "continuousServiceDate", "title": "Service Date", "type": "date", "required": False, "filterable": True, "is_key": False, "description": "Start of continuous service"},
                    {"name": "endEmploymentDate", "title": "End Date", "type": "date", "required": False, "filterable": True, "is_key": False, "description": "Termination or end date"},
                    {"name": "primarySupervisoryOrganization", "title": "Supervisory Org", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Primary supervisory organization"},
                    {"name": "primaryJob", "title": "Primary Job", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Current primary job assignment"},
                    {"name": "businessTitle", "title": "Business Title", "type": "string", "required": False, "filterable": True, "is_key": False, "description": "Worker's business title"},
                    {"name": "managementLevel", "title": "Management Level", "type": "string", "required": False, "filterable": True, "is_key": False, "description": "Worker's management level"},
                    {"name": "timeType", "title": "Time Type", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Full Time or Part Time"},
                    {"name": "location", "title": "Work Location", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Primary work location"},
                ],
                "related": [
                    {"name": "workers/{workerId}/jobHistory", "title": "Job History", "description": "Historical job positions for the worker"},
                    {"name": "workers/{workerId}/compensation", "title": "Compensation", "description": "Current and historical compensation"},
                    {"name": "workers/{workerId}/roles", "title": "Security Roles", "description": "Security roles assigned to the worker"},
                ]
            },
            {
                "name": "organizations",
                "title": "Organizations",
                "module": "humanResources",
                "rest_path": "/organizations",
                "description": "All organization types: Company, Cost Center, Region, Supervisory, Custom",
                "fields": [
                    {"name": "id", "title": "Organization ID", "type": "string", "required": True, "filterable": True, "is_key": True, "description": "Unique identifier"},
                    {"name": "organizationCode", "title": "Org Code", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Short code for the org"},
                    {"name": "organizationName", "title": "Org Name", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Full name of the organization"},
                    {"name": "organizationType", "title": "Org Type", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Supervisory, Cost Center, Company, etc."},
                    {"name": "organizationSubtype", "title": "Org Sub-Type", "type": "string", "required": False, "filterable": True, "is_key": False, "description": "Further classification"},
                    {"name": "includeOrganizationInHierarchy", "title": "In Hierarchy", "type": "boolean", "required": False, "filterable": True, "is_key": False, "description": "Part of org hierarchy"},
                    {"name": "topLevelOrganizationInHierarchy", "title": "Top Level", "type": "object", "required": False, "filterable": True, "is_key": False, "description": "Root org in the hierarchy"},
                    {"name": "manager", "title": "Manager", "type": "object", "required": False, "filterable": True, "is_key": False, "description": "Manager of this organization"},
                    {"name": "staffingModel", "title": "Staffing Model", "type": "string", "required": False, "filterable": True, "is_key": False, "description": "Position or Headcount model"},
                    {"name": "inactive", "title": "Inactive", "type": "boolean", "required": False, "filterable": True, "is_key": False, "description": "Whether org is inactive"},
                ],
                "related": [
                    {"name": "organizations/{id}/workers", "title": "Workers in Org", "description": "Workers assigned to this organization"},
                ]
            },
            {
                "name": "jobProfiles",
                "title": "Job Profiles",
                "module": "humanResources",
                "rest_path": "/jobProfiles",
                "description": "Job profiles defining roles, grades, and pay ranges",
                "fields": [
                    {"name": "id", "title": "Job Profile ID", "type": "string", "required": True, "filterable": True, "is_key": True, "description": "Unique identifier"},
                    {"name": "jobCode", "title": "Job Code", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Short code for the job"},
                    {"name": "jobTitle", "title": "Job Title", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Title of the job profile"},
                    {"name": "jobFamily", "title": "Job Family", "type": "object", "required": False, "filterable": True, "is_key": False, "description": "Job family grouping"},
                    {"name": "jobCategory", "title": "Job Category", "type": "object", "required": False, "filterable": True, "is_key": False, "description": "FLSA/exempt classification"},
                    {"name": "managementLevel", "title": "Management Level", "type": "string", "required": False, "filterable": True, "is_key": False, "description": "Individual Contributor, Manager, etc."},
                    {"name": "workShift", "title": "Work Shift", "type": "string", "required": False, "filterable": False, "is_key": False, "description": "Standard shift pattern"},
                    {"name": "inactive", "title": "Inactive", "type": "boolean", "required": False, "filterable": True, "is_key": False, "description": "Whether profile is inactive"},
                ],
                "related": []
            },
            {
                "name": "locations",
                "title": "Locations",
                "module": "humanResources",
                "rest_path": "/locations",
                "description": "Physical and remote work locations",
                "fields": [
                    {"name": "id", "title": "Location ID", "type": "string", "required": True, "filterable": True, "is_key": True, "description": "Unique identifier"},
                    {"name": "locationName", "title": "Location Name", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Name of the location"},
                    {"name": "locationType", "title": "Location Type", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Business Site, Remote, etc."},
                    {"name": "country", "title": "Country", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Country of the location"},
                    {"name": "addressLine1", "title": "Address Line 1", "type": "string", "required": False, "filterable": False, "is_key": False, "description": "Street address"},
                    {"name": "city", "title": "City", "type": "string", "required": False, "filterable": True, "is_key": False, "description": "City"},
                    {"name": "stateProvince", "title": "State / Province", "type": "string", "required": False, "filterable": True, "is_key": False, "description": "State or Province"},
                    {"name": "postalCode", "title": "Postal Code", "type": "string", "required": False, "filterable": False, "is_key": False, "description": "ZIP / Postal code"},
                    {"name": "timeZone", "title": "Time Zone", "type": "string", "required": False, "filterable": True, "is_key": False, "description": "Time zone of the location"},
                    {"name": "inactive", "title": "Inactive", "type": "boolean", "required": False, "filterable": True, "is_key": False, "description": "Whether location is inactive"},
                ],
                "related": []
            },
        ]
    },
    {
        "id": "payroll",
        "label": "Payroll",
        "description": "Pay Groups, Pay Period Calendars, Payroll Results, Earnings, Deductions",
        "objects": [
            {
                "name": "payGroups",
                "title": "Pay Groups",
                "module": "payroll",
                "rest_path": "/payGroups",
                "description": "Groups of workers processed together in a payroll run",
                "fields": [
                    {"name": "id", "title": "Pay Group ID", "type": "string", "required": True, "filterable": True, "is_key": True, "description": "Unique identifier"},
                    {"name": "payGroupName", "title": "Pay Group Name", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Name of the pay group"},
                    {"name": "currency", "title": "Currency", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Pay currency"},
                    {"name": "frequency", "title": "Frequency", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Weekly, Bi-Weekly, Semi-Monthly, Monthly"},
                    {"name": "country", "title": "Country", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Country for payroll processing"},
                    {"name": "inactive", "title": "Inactive", "type": "boolean", "required": False, "filterable": True, "is_key": False, "description": "Whether pay group is inactive"},
                ],
                "related": [
                    {"name": "payGroups/{id}/payPeriodCalendars", "title": "Pay Period Calendars", "description": "Calendar of pay periods for the group"},
                ]
            },
            {
                "name": "payrollResults",
                "title": "Payroll Results",
                "module": "payroll",
                "rest_path": "/payrollResults",
                "description": "Calculated payroll results for a pay period",
                "fields": [
                    {"name": "id", "title": "Result ID", "type": "string", "required": True, "filterable": True, "is_key": True, "description": "Unique payroll result ID"},
                    {"name": "worker", "title": "Worker", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Worker this result belongs to"},
                    {"name": "payGroup", "title": "Pay Group", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Pay group for this result"},
                    {"name": "payPeriodStartDate", "title": "Period Start Date", "type": "date", "required": True, "filterable": True, "is_key": False, "description": "Start of the pay period"},
                    {"name": "payPeriodEndDate", "title": "Period End Date", "type": "date", "required": True, "filterable": True, "is_key": False, "description": "End of the pay period"},
                    {"name": "checkDate", "title": "Check Date", "type": "date", "required": True, "filterable": True, "is_key": False, "description": "Date of payment"},
                    {"name": "grossPay", "title": "Gross Pay", "type": "number", "required": True, "filterable": False, "is_key": False, "description": "Total gross pay before deductions"},
                    {"name": "netPay", "title": "Net Pay", "type": "number", "required": True, "filterable": False, "is_key": False, "description": "Net pay after deductions and taxes"},
                    {"name": "currency", "title": "Currency", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Payment currency"},
                    {"name": "status", "title": "Status", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Completed, Void, Pending"},
                ],
                "related": [
                    {"name": "payrollResults/{id}/earningLines", "title": "Earning Lines", "description": "Individual earning components (salary, bonus, etc.)"},
                    {"name": "payrollResults/{id}/deductionLines", "title": "Deduction Lines", "description": "Tax and benefit deduction lines"},
                ]
            },
        ]
    },
    {
        "id": "recruiting",
        "label": "Recruiting",
        "description": "Job Requisitions, Job Applications, Candidates, Interview Feedback, Offers",
        "objects": [
            {
                "name": "jobRequisitions",
                "title": "Job Requisitions",
                "module": "recruiting",
                "rest_path": "/jobRequisitions",
                "description": "Open job requisitions (headcount requests)",
                "fields": [
                    {"name": "id", "title": "Requisition ID", "type": "string", "required": True, "filterable": True, "is_key": True, "description": "Unique identifier"},
                    {"name": "requisitionNumber", "title": "Req Number", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Human-readable requisition number"},
                    {"name": "jobProfile", "title": "Job Profile", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Job profile being recruited for"},
                    {"name": "jobTitle", "title": "Job Title", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Job title for the opening"},
                    {"name": "status", "title": "Status", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Open, Closed, On Hold, Filled"},
                    {"name": "hiringManager", "title": "Hiring Manager", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Worker responsible for hiring"},
                    {"name": "supervisoryOrganization", "title": "Supervisory Org", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Org the new hire will join"},
                    {"name": "targetHireDate", "title": "Target Hire Date", "type": "date", "required": False, "filterable": True, "is_key": False, "description": "Desired start date"},
                    {"name": "openDate", "title": "Open Date", "type": "date", "required": True, "filterable": True, "is_key": False, "description": "Date requisition was opened"},
                    {"name": "numberOfOpenings", "title": "Openings", "type": "integer", "required": True, "filterable": True, "is_key": False, "description": "Number of positions to fill"},
                    {"name": "location", "title": "Work Location", "type": "object", "required": False, "filterable": True, "is_key": False, "description": "Where the role is based"},
                    {"name": "workerType", "title": "Worker Type", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Employee or Contingent Worker"},
                ],
                "related": [
                    {"name": "jobRequisitions/{id}/jobApplications", "title": "Job Applications", "description": "Applications submitted for this requisition"},
                ]
            },
            {
                "name": "jobApplications",
                "title": "Job Applications",
                "module": "recruiting",
                "rest_path": "/jobApplications",
                "description": "Candidate applications for job requisitions",
                "fields": [
                    {"name": "id", "title": "Application ID", "type": "string", "required": True, "filterable": True, "is_key": True, "description": "Unique identifier"},
                    {"name": "candidate", "title": "Candidate", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "The candidate who applied"},
                    {"name": "jobRequisition", "title": "Job Requisition", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "The job they applied to"},
                    {"name": "applicationStatus", "title": "Status", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Applied, Interview, Offer, Hired, Rejected"},
                    {"name": "currentStage", "title": "Stage", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Current recruiting stage"},
                    {"name": "applicationDate", "title": "Applied Date", "type": "date", "required": True, "filterable": True, "is_key": False, "description": "Date the application was submitted"},
                    {"name": "source", "title": "Source", "type": "string", "required": False, "filterable": True, "is_key": False, "description": "How candidate found the job"},
                    {"name": "referredBy", "title": "Referred By", "type": "object", "required": False, "filterable": True, "is_key": False, "description": "Worker who referred this candidate"},
                ],
                "related": [
                    {"name": "jobApplications/{id}/interviewFeedback", "title": "Interview Feedback", "description": "Interview scores and feedback"},
                ]
            },
        ]
    },
    {
        "id": "benefits",
        "label": "Benefits",
        "description": "Benefit Plans, Benefit Elections, Dependents, Coverage",
        "objects": [
            {
                "name": "benefitPlans",
                "title": "Benefit Plans",
                "module": "benefits",
                "rest_path": "/benefitPlans",
                "description": "All benefit plans available to workers",
                "fields": [
                    {"name": "id", "title": "Plan ID", "type": "string", "required": True, "filterable": True, "is_key": True, "description": "Unique identifier"},
                    {"name": "planName", "title": "Plan Name", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Name of the benefit plan"},
                    {"name": "benefitType", "title": "Benefit Type", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Medical, Dental, Vision, 401k, Life, etc."},
                    {"name": "planDescription", "title": "Description", "type": "string", "required": False, "filterable": False, "is_key": False, "description": "Plan description"},
                    {"name": "benefitProvider", "title": "Provider", "type": "object", "required": False, "filterable": True, "is_key": False, "description": "Insurance provider"},
                    {"name": "coverageLevels", "title": "Coverage Levels", "type": "array", "required": False, "filterable": False, "is_key": False, "description": "Employee Only, Employee + Spouse, Family, etc."},
                    {"name": "enrollmentStartDate", "title": "Enrollment Start", "type": "date", "required": False, "filterable": True, "is_key": False, "description": "When enrollment opens"},
                    {"name": "enrollmentEndDate", "title": "Enrollment End", "type": "date", "required": False, "filterable": True, "is_key": False, "description": "When enrollment closes"},
                    {"name": "inactive", "title": "Inactive", "type": "boolean", "required": False, "filterable": True, "is_key": False, "description": "Whether plan is inactive"},
                ],
                "related": [
                    {"name": "benefitPlans/{id}/benefitElections", "title": "Benefit Elections", "description": "Worker elections for this plan"},
                ]
            },
        ]
    },
    {
        "id": "timeAndAbsence",
        "label": "Time & Absence",
        "description": "Time Off Types, Absence Requests, Time Entries, Accrual Balances",
        "objects": [
            {
                "name": "timeOffTypes",
                "title": "Time Off Types",
                "module": "timeAndAbsence",
                "rest_path": "/timeOffTypes",
                "description": "Types of time off available to workers (Vacation, Sick, etc.)",
                "fields": [
                    {"name": "id", "title": "Type ID", "type": "string", "required": True, "filterable": True, "is_key": True, "description": "Unique identifier"},
                    {"name": "timeOffTypeName", "title": "Type Name", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Name of the time off type"},
                    {"name": "timeOffTypeCode", "title": "Type Code", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Short code"},
                    {"name": "category", "title": "Category", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Vacation, Sick, FMLA, Personal, etc."},
                    {"name": "unit", "title": "Unit", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Days or Hours"},
                    {"name": "paidTimeOff", "title": "Paid", "type": "boolean", "required": True, "filterable": True, "is_key": False, "description": "Whether time off is paid"},
                    {"name": "inactive", "title": "Inactive", "type": "boolean", "required": False, "filterable": True, "is_key": False, "description": "Whether type is inactive"},
                ],
                "related": []
            },
            {
                "name": "absenceRequests",
                "title": "Absence Requests",
                "module": "timeAndAbsence",
                "rest_path": "/absenceRequests",
                "description": "Time off requests submitted by workers",
                "fields": [
                    {"name": "id", "title": "Request ID", "type": "string", "required": True, "filterable": True, "is_key": True, "description": "Unique identifier"},
                    {"name": "worker", "title": "Worker", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Worker who submitted the request"},
                    {"name": "timeOffType", "title": "Time Off Type", "type": "object", "required": True, "filterable": True, "is_key": False, "description": "Type of time off requested"},
                    {"name": "startDate", "title": "Start Date", "type": "date", "required": True, "filterable": True, "is_key": False, "description": "First day of absence"},
                    {"name": "endDate", "title": "End Date", "type": "date", "required": True, "filterable": True, "is_key": False, "description": "Last day of absence"},
                    {"name": "totalDays", "title": "Total Days", "type": "number", "required": True, "filterable": False, "is_key": False, "description": "Total days requested"},
                    {"name": "status", "title": "Status", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Submitted, Approved, Denied, Cancelled"},
                    {"name": "approver", "title": "Approver", "type": "object", "required": False, "filterable": True, "is_key": False, "description": "Worker who approved/denied"},
                    {"name": "comments", "title": "Comments", "type": "string", "required": False, "filterable": False, "is_key": False, "description": "Notes from worker or approver"},
                ],
                "related": []
            },
        ]
    },
    {
        "id": "learning",
        "label": "Learning",
        "description": "Courses, Learning Content, Programs, Enrollments, Completions",
        "objects": [
            {
                "name": "learningCourses",
                "title": "Learning Courses",
                "module": "learning",
                "rest_path": "/learningCourses",
                "description": "Courses available in the Workday Learning catalog",
                "fields": [
                    {"name": "id", "title": "Course ID", "type": "string", "required": True, "filterable": True, "is_key": True, "description": "Unique identifier"},
                    {"name": "courseTitle", "title": "Course Title", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Title of the course"},
                    {"name": "courseDescription", "title": "Description", "type": "string", "required": False, "filterable": False, "is_key": False, "description": "Course description"},
                    {"name": "courseFormat", "title": "Format", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "eLearning, Instructor-Led, Blended"},
                    {"name": "topic", "title": "Topic", "type": "object", "required": False, "filterable": True, "is_key": False, "description": "Learning topic/category"},
                    {"name": "durationMinutes", "title": "Duration (min)", "type": "integer", "required": False, "filterable": False, "is_key": False, "description": "Estimated duration in minutes"},
                    {"name": "language", "title": "Language", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Language of the course content"},
                    {"name": "status", "title": "Status", "type": "string", "required": True, "filterable": True, "is_key": False, "description": "Active, Inactive, Draft"},
                    {"name": "expirationDate", "title": "Expiration Date", "type": "date", "required": False, "filterable": True, "is_key": False, "description": "When course expires"},
                ],
                "related": [
                    {"name": "learningCourses/{id}/enrollments", "title": "Enrollments", "description": "Worker enrollments for this course"},
                ]
            },
        ]
    },
]

_ALL_OBJECTS = {obj["name"]: obj for m in DEMO_MODULES for obj in m["objects"]}
_MODULE_MAP = {m["id"]: m for m in DEMO_MODULES}


# ──────────────────────────────────────────────────────────────────
# Real Workday REST API helpers (OAuth 2.0 Client Credentials)
# ──────────────────────────────────────────────────────────────────

def _is_demo_mode() -> bool:
    return not bool(settings.WORKDAY_TENANT)


def _api_base() -> str:
    return f"https://{settings.WORKDAY_TENANT}.workday.com{WORKDAY_API_PATH}/{settings.WORKDAY_TENANT}"


def _get_access_token() -> str:
    token_url = f"https://{settings.WORKDAY_TENANT}.workday.com{WORKDAY_TOKEN_PATH}"
    resp = requests.post(
        token_url,
        auth=HTTPBasicAuth(settings.WORKDAY_CLIENT_ID, settings.WORKDAY_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=30,
    )
    if not resp.ok:
        raise ConnectionError(
            f"Workday OAuth failed [{resp.status_code}]: {resp.text[:300]}"
        )
    return resp.json()["access_token"]


def _get(path: str) -> dict:
    token = _get_access_token()
    url = f"{_api_base()}{path}"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=30,
    )
    if resp.status_code == 401:
        raise ConnectionError("Workday authentication failed. Check WORKDAY_CLIENT_ID and WORKDAY_CLIENT_SECRET.")
    if resp.status_code == 403:
        raise PermissionError(f"Workday access denied for {path}")
    if resp.status_code == 404:
        raise LookupError(f"Workday resource not found: {path}")
    if not resp.ok:
        raise RuntimeError(f"Workday API error [{resp.status_code}]: {resp.text[:400]}")
    return resp.json()


# ──────────────────────────────────────────────────────────────────
# Public service functions
# ──────────────────────────────────────────────────────────────────

def test_connection() -> dict:
    if _is_demo_mode():
        total_objects = sum(len(m["objects"]) for m in DEMO_MODULES)
        total_fields = sum(len(obj["fields"]) for m in DEMO_MODULES for obj in m["objects"])
        return {
            "connected": True,
            "mode": "demo",
            "message": (
                "Running in Demo Mode — showing real Workday REST API schema structure. "
                "Set WORKDAY_TENANT, WORKDAY_CLIENT_ID, WORKDAY_CLIENT_SECRET in .env "
                "to connect to a real Workday tenant."
            ),
            "modules_count": len(DEMO_MODULES),
            "total_objects": total_objects,
            "total_fields": total_fields,
            "workday_api_path": WORKDAY_API_PATH,
        }

    data = _get("/workers?limit=1")
    return {
        "connected": True,
        "mode": "live",
        "tenant": settings.WORKDAY_TENANT,
        "total_workers_sample": data.get("total", 0),
    }


def list_modules() -> list[dict]:
    return [
        {
            "id": m["id"],
            "label": m["label"],
            "description": m["description"],
            "objects_count": len(m["objects"]),
        }
        for m in DEMO_MODULES
    ]


def get_module_objects(module_id: str) -> dict:
    if module_id not in _MODULE_MAP:
        raise LookupError(f"Module '{module_id}' not found. Available: {list(_MODULE_MAP.keys())}")
    module = _MODULE_MAP[module_id]
    objects = [
        {
            "name": obj["name"],
            "title": obj["title"],
            "rest_path": obj["rest_path"],
            "description": obj["description"],
            "fields_count": len(obj["fields"]),
            "related_count": len(obj["related"]),
        }
        for obj in module["objects"]
    ]
    return {
        "module_id": module_id,
        "module_label": module["label"],
        "total": len(objects),
        "objects": objects,
        "mode": "demo" if _is_demo_mode() else "live",
    }


def get_object_describe(object_name: str) -> dict:
    if _is_demo_mode():
        if object_name not in _ALL_OBJECTS:
            raise LookupError(
                f"Object '{object_name}' not found. Available: {list(_ALL_OBJECTS.keys())}"
            )
        obj = _ALL_OBJECTS[object_name]
        return {
            **obj,
            "fields_count": len(obj["fields"]),
            "related_count": len(obj["related"]),
            "mode": "demo",
        }

    data = _get(f"/{object_name}?limit=1")
    return {
        "name": object_name,
        "title": object_name,
        "module": "",
        "rest_path": f"/{object_name}",
        "description": "",
        "fields": [],
        "related": [],
        "fields_count": 0,
        "related_count": 0,
        "mode": "live",
        "raw_sample": data,
    }


def get_all_objects() -> dict:
    all_objects = [
        {
            "name": obj["name"],
            "title": obj["title"],
            "module": obj["module"],
            "rest_path": obj["rest_path"],
            "description": obj["description"],
            "fields_count": len(obj["fields"]),
            "related_count": len(obj["related"]),
        }
        for m in DEMO_MODULES
        for obj in m["objects"]
    ]
    return {
        "total": len(all_objects),
        "objects": all_objects,
        "mode": "demo" if _is_demo_mode() else "live",
    }

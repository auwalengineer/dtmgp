import re

import frappe

from dtmgp.permissions.scope import get_allowed_companies, get_user_roles

STATE = {"State Administrator", "State Executive Viewer", "State Auditor"}
GOVERNANCE = STATE | {"LGA Administrator", "LGA Chairman", "LGA Secretary", "Treasurer", "HR Officer", "Procurement Officer", "Project Officer", "Traditional Affairs Officer", "Internal Auditor", "Read-only Officer"}
HR = STATE | {"LGA Administrator", "LGA Chairman", "LGA Secretary", "HR Officer", "Internal Auditor", "Read-only Officer"}
FINANCE = STATE | {"LGA Administrator", "LGA Chairman", "Treasurer", "Revenue Officer", "Procurement Officer", "Internal Auditor", "Read-only Officer"}
PROJECTS = STATE | {"LGA Administrator", "LGA Chairman", "LGA Secretary", "Treasurer", "Procurement Officer", "Project Officer", "Internal Auditor", "Read-only Officer"}
TRADITIONAL = STATE | {"LGA Administrator", "LGA Chairman", "LGA Secretary", "Traditional Affairs Officer", "Internal Auditor", "Read-only Officer"}
ANALYTICS = STATE | {"LGA Administrator", "LGA Chairman", "LGA Secretary", "Treasurer", "Revenue Officer", "HR Officer", "Procurement Officer", "Project Officer", "Traditional Affairs Officer", "Internal Auditor", "Read-only Officer"}
SYSTEM_ADMIN = {"System Manager", "State Administrator", "LGA Administrator"}
STATE_ONLY = {"System Manager", "State Administrator"}


def _slug(label):
	return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def _section(domain, label, items="", roles=None, to=None):
	section_id = _slug(label)
	children = [
		{"id": _slug(item), "label": item, "to": f"/workspace/{domain}/{section_id}/{_slug(item)}"}
		for item in items.split("|") if item
	]
	return {
		"id": section_id,
		"label": label,
		"to": to or (f"/workspace/{domain}/{section_id}" if not children else None),
		"roles": roles,
		"children": children,
	}


NAVIGATION = (
	{
		"id": "governance", "label": "Administration & Governance", "icon": "landmark", "roles": GOVERNANCE,
		"children": [
			_section("governance", "Overview", to="/governance"),
			_section("governance", "Correspondence", "Incoming Correspondence|Outgoing Correspondence|Internal Memos|Dispatch Register|Assigned Correspondence"),
			_section("governance", "Meetings", "Meeting Calendar|Council Meetings|Committee Meetings|Meeting Agendas|Attendance|Minutes"),
			_section("governance", "Resolutions", "Resolution Register|Assigned Actions|Action Progress|Overdue Actions"),
			_section("governance", "Statutory Returns", "Return Requirements|Prepare Returns|Submitted Returns|Overdue Returns|State Review"),
			_section("governance", "Compliance", "Compliance Requirements|Compliance Submissions|Compliance Calendar|Compliance Scorecard"),
			_section("governance", "Approvals", "Pending Approvals|Approved Requests|Rejected Requests|Delegated Approvals"),
			_section("governance", "Departments & Units"),
			_section("governance", "Reports", "Governance Reports|Meeting Reports|Resolution Reports|Compliance Reports|Statutory Return Reports"),
		],
	},
	{
		"id": "hr", "label": "Human Resources & Staff", "icon": "users", "roles": HR,
		"children": [
			_section("hr", "HR Overview", to="/people"),
			_section("hr", "Employee Dashboard", to="/people/dashboard"),
			_section("hr", "Staff", "Staff Directory|Staff Profiles|Digital Personnel Files|Employment History|Next of Kin|Staff Documents"),
			_section("hr", "Verification & Biometrics", "Verification Exercises|Pending Verification|Verified Staff|Biometric Enrolment|Verification Exceptions|Verification Reports"),
			_section("hr", "Establishment Control", "Approved Establishment|Establishment Positions|Vacant Positions|Occupied Positions|Overstaffing|Staffing Shortages"),
			_section("hr", "Posting & Transfers", "Posting Requests|Transfer Requests|Posting Orders|Transfer Orders|Posting History|Transfer History|Assumption of Duty"),
			_section("hr", "Promotions", "Promotion Eligibility|Promotion Requests|Promotion Reviews|Approved Promotions|Promotion History"),
			_section("hr", "Leave", "Leave Requests|Leave Approvals|Leave Balances|Leave Calendar|Staff on Leave"),
			_section("hr", "Attendance", "Attendance Records|Shift Assignments|Late Arrivals|Absent Staff|Attendance Reports"),
			_section("hr", "Retirement & Exit", "Upcoming Retirements|Retirement Processing|Resignations|Terminations|Exit Clearance|Former Staff"),
			_section("hr", "Payroll", "Salary Structures|Payroll Processing|Salary Slips|Deductions|Payroll Reports", roles=STATE | {"Treasurer"}),
			_section("hr", "Staff Audit", "Audit Exercises|Audit Exceptions|Duplicate Records|Staff Audit Reports", roles=STATE | {"Internal Auditor"}),
			_section("hr", "HR Reports", "Staff Strength Report|Staff Distribution Report|Retirement Forecast|Leave Report|Establishment Report"),
		],
	},
	{
		"id": "finance", "label": "Finance, Revenue & Procurement", "icon": "circle-dollar-sign", "roles": FINANCE,
		"children": [
			_section("finance", "Finance Overview", to="/finance"),
			_section("finance", "Budget", "Budget Preparation|Budget Proposals|Budget Review|Approved Budget|Budget Revisions|Budget Performance|Variance Analysis"),
			_section("finance", "Revenue", "Revenue Sources|Revenue Targets|Revenue Collections|Collection Channels|Revenue Officers|Daily Collections|Revenue Performance|Revenue Reconciliation"),
			_section("finance", "Allocations", "Allocation Register|Allocation Receipts|Allocation Distribution|Allocation Utilization"),
			_section("finance", "Expenditure", "Payment Requests|Expense Claims|Expenditure Approvals|Payment Vouchers|Expenditure Register"),
			_section("finance", "Accounting", "Chart of Accounts|Journal Entries|General Ledger|Accounts Receivable|Accounts Payable|Bank Reconciliation|Trial Balance"),
			_section("finance", "Procurement", "Procurement Plans|Purchase Requests|Requests for Quotation|Supplier Quotations|Bid Evaluation|Purchase Orders|Goods Received|Procurement Approvals"),
			_section("finance", "Contracts", "Contract Register|Contractor Profiles|Contract Milestones|Certificates & Payments|Contract Variations|Contract Completion"),
			_section("finance", "Audit & Control", "Audit Queries|Audit Responses|Financial Exceptions|Approval History|Financial Audit Trail"),
			_section("finance", "Financial Reports", "Budget Performance Report|Revenue Performance Report|Expenditure Report|Cash Flow Report|Trial Balance|General Ledger Report"),
		],
	},
	{
		"id": "projects", "label": "Projects, Assets & Field Monitoring", "icon": "folder-kanban", "roles": PROJECTS,
		"children": [
			_section("projects", "Projects Overview", to="/projects"),
			_section("projects", "Projects", "Project Register|New Projects|Ongoing Projects|Completed Projects|Delayed Projects|Suspended Projects|Abandoned Projects"),
			_section("projects", "Project Planning", "Project Proposals|Work Plans|Project Locations|Project Milestones|Funding Sources"),
			_section("projects", "Contractors", "Contractor Register|Contractor Documents|Contractor Performance|Blacklisted Contractors"),
			_section("projects", "Field Monitoring", "Inspection Schedule|Assigned Inspections|Mobile Inspections|Inspection Reports|GPS & Photo Evidence|Inspection Exceptions"),
			_section("projects", "Progress Monitoring", "Physical Progress|Financial Progress|Milestone Status|Delayed Milestones|Variation Requests"),
			_section("projects", "Assets", "Asset Register|Asset Categories|Asset Locations|Asset Assignments|Asset Transfers|Asset Maintenance|Asset Disposal|Asset Verification"),
			_section("projects", "Fleet Management", "Vehicle Register|Vehicle Assignments|Trip Records|Fuel Records|Vehicle Maintenance|Insurance & Licensing|Driver Records"),
			_section("projects", "Maps", "Project Map|Asset Map|Inspection Map"),
			_section("projects", "Reports", "Project Status Report|Project Performance Report|Inspection Report|Asset Report|Fleet Report"),
		],
	},
	{
		"id": "traditional", "label": "Chieftaincy & Traditional Institutions", "icon": "crown", "roles": TRADITIONAL,
		"children": [
			_section("traditional", "Chieftaincy Overview", to="/traditional-affairs"),
			_section("traditional", "Traditional Institutions", "Institution Register|Traditional Councils|Districts & Chiefdoms|Institutional Profiles|Historical Records"),
			_section("traditional", "Traditional Rulers", "Rulers Register|Current Rulers|Former Rulers|Vacant Stools|Ruler Profiles"),
			_section("traditional", "Appointments", "Appointment Applications|Selection Processes|Appointment Reviews|Pending Recognition|Approved Appointments|Installation Records"),
			_section("traditional", "Succession", "Succession Cases|Ruling Houses|Eligible Candidates|Selection Records|Succession History"),
			_section("traditional", "Recognition & Certification", "Recognition Requests|Recognition Approvals|Certificate Register|Issue Certificates|Suspended Recognition|Withdrawn Recognition"),
			_section("traditional", "Petitions & Disputes", "New Petitions|Petition Register|Dispute Cases|Hearings|Evidence & Documents|Decisions & Resolutions|Appeals"),
			_section("traditional", "Allowances & Entitlements", "Entitlement Register|Allowance Processing|Payment History"),
			_section("traditional", "Reports", "Traditional Institution Report|Traditional Ruler Report|Appointment Report|Succession Report|Petition & Dispute Report"),
		],
	},
	{
		"id": "analytics", "label": "Executive Dashboard & Analytics", "icon": "chart-no-axes-combined", "roles": ANALYTICS,
		"children": [
			_section("analytics", "Statewide Overview", to="/analytics", roles=STATE),
			_section("analytics", "LGA Performance", "LGA Scorecards|LGA Comparison|Performance Ranking|Performance Trends|Data Completeness"),
			_section("analytics", "Domain Analytics", "Governance Analytics|Workforce Analytics|Finance Analytics|Revenue Analytics|Project Analytics|Asset Analytics|Chieftaincy Analytics"),
			_section("analytics", "Geographic View", "Statewide Map|Projects Map|Revenue Map|Compliance Map"),
			_section("analytics", "Alerts & Early Warnings", "Active Alerts|Critical Alerts|Overdue Actions|Revenue Shortfalls|Budget Variances|Delayed Projects|Compliance Defaults|Staff Exceptions"),
			_section("analytics", "Executive Reports", "Executive Summary|Scheduled Reports|Saved Reports|Report Subscriptions|Data Export"),
			_section("analytics", "Interoperability", "Connected Systems|API Clients|Webhooks|Import Jobs|Export Jobs|Synchronization History|Failed Transactions|Integration Logs|Data Exchange Audit", roles=STATE_ONLY),
		],
	},
	{
		"id": "system", "label": "System Administration", "icon": "settings", "roles": SYSTEM_ADMIN,
		"children": [
			_section("system", "Administration Overview", to="/administration"),
			_section("system", "User Management", "Users|Roles|Role Profiles|LGA Access|User Sessions"),
			_section("system", "Organization Setup", "LGAs|Departments|Units|Designations|Fiscal Years"),
			_section("system", "Workflow Setup", "Workflows|Workflow States|Approval Limits|Approval Delegation|Escalation Rules", roles=STATE_ONLY),
			_section("system", "Communication Setup", "Notifications|Email Templates|SMS Templates|Notification Preferences", roles=STATE_ONLY),
			_section("system", "Reference Data", "Document Numbering|Status Definitions|Categories|Locations|Other Reference Data", roles=STATE_ONLY),
			_section("system", "Security & Audit", "Audit Logs|Login History|Permission Changes|Data Export History|Security Events", roles=STATE_ONLY),
			_section("system", "System Operations", "Background Jobs|Scheduled Tasks|Error Logs|System Health|Application Settings", roles={"System Manager"}),
		],
	},
)

GLOBAL_MENU = (
	("My Dashboard", "/"), ("My Tasks", "/workspace/global/my-tasks"),
	("My Approvals", "/workspace/global/my-approvals"), ("Inbox", "/workspace/global/inbox"),
	("Notifications", "/workspace/global/notifications"), ("Calendar", "/workspace/global/calendar"),
	("Recently Viewed", "/workspace/global/recently-viewed"), ("Saved Items", "/workspace/global/saved-items"),
	("Help & Support", "/workspace/global/help-support"), ("My Profile", "/workspace/global/my-profile"),
)


def get_navigation(user=None):
	user = user or frappe.session.user
	roles = get_user_roles(user)
	if user == "Administrator":
		roles |= STATE | {"System Manager"}
	if user != "Administrator" and "System Manager" not in roles and not get_allowed_companies(user):
		return {"modules": [], "global": [{"id": _slug(label), "label": label, "to": route} for label, route in GLOBAL_MENU]}
	modules = []
	for module in NAVIGATION:
		if not roles.intersection(module["roles"]):
			continue
		children = []
		for section in module["children"]:
			if section["roles"] and not roles.intersection(section["roles"]):
				continue
			children.append({key: value for key, value in section.items() if key != "roles"})
		modules.append({key: value for key, value in module.items() if key != "roles"} | {"children": children})
	return {
		"modules": modules,
		"global": [{"id": _slug(label), "label": label, "to": route} for label, route in GLOBAL_MENU],
	}

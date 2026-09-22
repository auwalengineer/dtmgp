import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from dtmgp.setup.organization import BENUE_LGAS, PARENT_COMPANY

ADMIN_ROLES = ("State Administrator", "LGA Administrator")
DEFAULT_HOLIDAY_LIST = "Benue LGA Standard Holidays"
USER_LGA_FIELD = "dtmgp_lga"
EMPLOYEE_GRADE_FIELD = "dtmgp_grade_level"
EMPLOYEE_VERIFICATION_FIELD = "dtmgp_verification_status"
EMPLOYEE_SEPARATION_EXIT_TYPE_FIELD = "dtmgp_exit_type"
PROJECT_LOCATION_FIELD = "dtmgp_location"
PROJECT_FUNDING_SOURCE_FIELD = "dtmgp_funding_source"
VEHICLE_COMPANY_FIELD = "company"
PLATFORM_ROLES = (
	"State Administrator",
	"State Executive Viewer",
	"State Auditor",
	"LGA Administrator",
	"LGA Chairman",
	"LGA Secretary",
	"Treasurer",
	"Revenue Officer",
	"HR Officer",
	"Procurement Officer",
	"Project Officer",
	"Traditional Affairs Officer",
	"Internal Auditor",
	"Read-only Officer",
)


def seed_security_setup():
	for role_name in PLATFORM_ROLES:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert()

	for role_name in ADMIN_ROLES:
		_ensure_user_permission(role_name)

	_ensure_user_lga_field()
	_ensure_employee_fields()
	_ensure_employee_separation_fields()
	_ensure_hr_permissions()
	_ensure_hrms_extension_permissions()
	_ensure_employee_transfer_property_setters()
	_ensure_default_holiday_list()
	_ensure_erpnext_finance_permissions()
	_ensure_project_custom_fields()
	_ensure_projects_permissions()
	_ensure_organization_setup_permissions()
	seed_role_profiles()


def seed_role_profiles():
	"""Create a one-role Role Profile per platform role so onboarding can pick a single
	profile instead of assembling the Roles table by hand. Kept 1:1 with PLATFORM_ROLES
	because every platform role is assigned exclusively (see api/v1/users.py)."""
	created = []
	for role_name in PLATFORM_ROLES:
		if frappe.db.exists("Role Profile", role_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Role Profile",
				"role_profile": role_name,
				"roles": [{"role": role_name}],
			}
		).insert()
		# Role Profile.on_update queues a background "sync roles to users" action and
		# locks the document for it; the lock is only released once that action runs.
		# A brand-new profile has no users yet, so unlock immediately rather than
		# leaving a stale lock file for repeated/test seeding to trip over.
		frappe.get_doc("Role Profile", role_name).unlock()
		created.append(role_name)
	return {"created": created}


def _ensure_user_permission(role_name):
	filters = {"parent": "User", "role": role_name, "permlevel": 0}
	if frappe.db.exists("Custom DocPerm", filters):
		return
	frappe.get_doc(
		{
			"doctype": "Custom DocPerm",
			**filters,
			"read": 1,
			"write": 1,
			"create": 1,
		}
	).insert()


def _ensure_user_lga_field():
	if frappe.db.exists("Custom Field", {"dt": "User", "fieldname": USER_LGA_FIELD}):
		return
	frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": "User",
			"fieldname": USER_LGA_FIELD,
			"label": "Local Government Area",
			"fieldtype": "Link",
			"options": "Company",
			"insert_after": "role_profile_name",
			"in_list_view": 1,
			"description": "Controls the user's LGA data access.",
		}
	).insert()


def _ensure_employee_fields():
	fields = (
		{
			"fieldname": EMPLOYEE_GRADE_FIELD,
			"label": "Grade Level",
			"fieldtype": "Data",
			"insert_after": "designation",
			"in_list_view": 1,
		},
		{
			"fieldname": EMPLOYEE_VERIFICATION_FIELD,
			"label": "Verification Status",
			"fieldtype": "Select",
			"options": "Pending\nVerified\nReview Due",
			"default": "Pending",
			"insert_after": EMPLOYEE_GRADE_FIELD,
			"in_list_view": 1,
		},
	)
	for field in fields:
		if not frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": field["fieldname"]}):
			frappe.get_doc({"doctype": "Custom Field", "dt": "Employee", **field}).insert()


def _ensure_employee_separation_fields():
	"""Employee Separation has no native resignation/retirement/termination
	distinction; add it as a Custom Field rather than a parallel DocType so the
	Retirement & Exit nav's Resignations/Terminations/Retirement Processing views
	can filter on it."""
	if frappe.db.exists("Custom Field", {"dt": "Employee Separation", "fieldname": EMPLOYEE_SEPARATION_EXIT_TYPE_FIELD}):
		return
	frappe.get_doc({
		"doctype": "Custom Field", "dt": "Employee Separation", "fieldname": EMPLOYEE_SEPARATION_EXIT_TYPE_FIELD,
		"label": "Exit Type", "fieldtype": "Select", "options": "Resignation\nRetirement\nTermination",
		"default": "Resignation", "insert_after": "resignation_letter_date", "in_list_view": 1,
	}).insert()


def _ensure_hr_permissions():
	permissions = {
		"Employee": {
			"State Administrator": (1, 1, 1),
			"LGA Administrator": (1, 1, 1),
			"HR Officer": (1, 1, 1),
			"LGA Chairman": (1, 0, 0),
			"LGA Secretary": (1, 0, 0),
			"Internal Auditor": (1, 0, 0),
			"Read-only Officer": (1, 0, 0),
		},
		# Department also backs the Governance module's "Departments & Units" section
		# (dtmgp/api/v1/governance.py) — it's a plain ERPNext DocType with no dtmgp
		# permission hook, so LGA scoping comes entirely from Frappe's native
		# Company User Permission filtering; these Custom DocPerm rows only grant the
		# base read/write/create rights matching GOVERNANCE_MANAGE_ROLES/GOVERNANCE_VIEW_ROLES.
		"Department": {
			"State Administrator": (1, 1, 1),
			"LGA Administrator": (1, 1, 1),
			"HR Officer": (1, 1, 1),
			"LGA Chairman": (1, 1, 1),
			"LGA Secretary": (1, 1, 1),
			"Treasurer": (1, 0, 0),
			"Procurement Officer": (1, 0, 0),
			"Project Officer": (1, 0, 0),
			"Traditional Affairs Officer": (1, 0, 0),
			"Internal Auditor": (1, 0, 0),
			"Read-only Officer": (1, 0, 0),
		},
		"Leave Application": {
			"State Administrator": (1, 1, 1),
			"LGA Administrator": (1, 1, 0),
			"HR Officer": (1, 1, 1),
			"LGA Chairman": (1, 0, 0),
		},
		# Project/Task back the Employee Separation exit-clearance checklist
		# (see hrms.controllers.employee_boarding_controller); scoped through
		# dtmgp.permissions.hr.project_query/task_query since Task has no company field.
		"Project": {
			"State Administrator": (1, 1, 1),
			"LGA Administrator": (1, 1, 1),
			"HR Officer": (1, 1, 1),
			"Internal Auditor": (1, 0, 0),
			"State Auditor": (1, 0, 0),
			"Read-only Officer": (1, 0, 0),
		},
		"Task": {
			"State Administrator": (1, 1, 1),
			"LGA Administrator": (1, 1, 1),
			"HR Officer": (1, 1, 1),
			"Internal Auditor": (1, 0, 0),
			"State Auditor": (1, 0, 0),
			"Read-only Officer": (1, 0, 0),
		},
		"Shift Assignment": {
			"State Administrator": (1, 1, 1),
			"LGA Administrator": (1, 1, 1),
			"HR Officer": (1, 1, 1),
			"Internal Auditor": (1, 0, 0),
			"Read-only Officer": (1, 0, 0),
		},
	}
	for doctype, roles in permissions.items():
		for role, (read, write, create) in roles.items():
			filters = {"parent": doctype, "role": role, "permlevel": 0}
			if not frappe.db.exists("Custom DocPerm", filters):
				frappe.get_doc(
					{
						"doctype": "Custom DocPerm",
						**filters,
						"read": read,
						"write": write,
						"create": create,
						# Task needs "share" too: HRMS's own Employee Separation activity flow
						# (hrms.controllers.employee_boarding_controller.assign_task_to_users)
						# assigns each generated Task via frappe.share.add(), which requires it.
						"share": write,
					}
				).insert()


def _ensure_hrms_extension_permissions():
	"""Grant platform roles access to the native HRMS doctypes that cover establishment
	planning, postings/transfers, promotions and exit clearance, instead of duplicating
	them as dtmgp DocTypes. Read-only roles mirror the Employee/Department pattern above."""
	permissions = {
		"Staffing Plan": ("State Administrator", "LGA Administrator", "HR Officer", "LGA Chairman", "LGA Secretary", "Internal Auditor", "State Auditor", "Read-only Officer"),
		"Employee Transfer": ("State Administrator", "LGA Administrator", "HR Officer", "LGA Chairman", "LGA Secretary", "Internal Auditor", "State Auditor", "Read-only Officer"),
		"Employee Promotion": ("State Administrator", "LGA Administrator", "HR Officer", "LGA Chairman", "LGA Secretary", "Internal Auditor", "State Auditor", "Read-only Officer"),
		"Employee Separation": ("State Administrator", "LGA Administrator", "HR Officer", "LGA Chairman", "LGA Secretary", "Internal Auditor", "State Auditor", "Read-only Officer"),
	}
	write_roles = {"State Administrator", "LGA Administrator", "HR Officer"}
	for doctype, roles in permissions.items():
		for role in roles:
			filters = {"parent": doctype, "role": role, "permlevel": 0}
			if frappe.db.exists("Custom DocPerm", filters):
				continue
			write = role in write_roles
			frappe.get_doc({
				"doctype": "Custom DocPerm", **filters, "read": 1, "report": 1, "export": 1,
				"create": int(write), "write": int(write), "submit": int(write), "cancel": int(write),
			}).insert()


def _ensure_employee_transfer_property_setters():
	"""Employee Transfer has two Company-Link fields: `company` (the employee's LGA
	at request time) and `new_company` (the transfer destination). Left alone,
	Frappe's automatic per-field User Permission filtering ANDs both fields together,
	so neither a single-LGA preparer (who only holds `company`) nor the receiving
	LGA's own officer (who only holds `new_company`) could ever satisfy both at once —
	the destination side would be permission-denied on `doc.submit()` even though our
	custom has_permission hook allows it, because core's per-field check is a
	separate, always-applied restriction it can't override. Exempting both fields via
	Property Setters (the supported way to customize a standard DocType's field
	without editing HRMS source) leaves scoping entirely to the explicit OR condition
	in dtmgp.permissions.hr.employee_transfer_query/has_permission."""
	for fieldname in ("company", "new_company"):
		if frappe.db.exists("Property Setter", {"doc_type": "Employee Transfer", "field_name": fieldname, "property": "ignore_user_permissions"}):
			continue
		make_property_setter("Employee Transfer", fieldname, "ignore_user_permissions", "1", "Check")


def _ensure_default_holiday_list():
	"""Employee Separation's native submit flow (hrms.controllers.EmployeeBoardingController)
	requires a holiday list for the employee or their Company, or it throws. Seed one
	shared list and default it on every LGA Company so exit clearances aren't blocked
	on a per-LGA holiday calendar that hasn't been approved/entered yet."""
	if not frappe.db.exists("Holiday List", DEFAULT_HOLIDAY_LIST):
		frappe.get_doc({
			"doctype": "Holiday List",
			"holiday_list_name": DEFAULT_HOLIDAY_LIST,
			"from_date": "2020-01-01",
			"to_date": "2035-12-31",
		}).insert()
	for company in (PARENT_COMPANY, *(lga.company_name for lga in BENUE_LGAS)):
		if frappe.db.exists("Company", company) and not frappe.db.get_value("Company", company, "default_holiday_list"):
			frappe.db.set_value("Company", company, "default_holiday_list", DEFAULT_HOLIDAY_LIST)


def _ensure_erpnext_finance_permissions():
	permissions = {
		"Account": ("Treasurer", "Internal Auditor", "State Auditor"),
		"Budget": ("Treasurer", "Internal Auditor", "State Auditor"),
		"Journal Entry": ("Treasurer", "Internal Auditor", "State Auditor"),
		# System-generated ledger rows -- read-only for every role regardless of the
		# write-role check below, see `read_only_doctypes`.
		"GL Entry": ("Treasurer", "Internal Auditor", "State Auditor"),
		"Payment Entry": ("Treasurer", "Revenue Officer", "Internal Auditor", "State Auditor"),
		"Bank Transaction": ("Treasurer", "Internal Auditor", "State Auditor"),
		# Also read by the Projects module's Contractor Register/Blacklisted views
		# (dtmgp/api/v1/projects.py) -- Supplier has no `company` field, so it's shared
		# statewide, same as it's already treated in DTMGPProcurementCase above.
		"Supplier": ("Procurement Officer", "Treasurer", "Internal Auditor", "State Auditor", "Project Officer", "LGA Administrator", "LGA Chairman"),
		"Material Request": ("Procurement Officer", "Treasurer", "Internal Auditor", "State Auditor"),
		"Request for Quotation": ("Procurement Officer", "Treasurer", "Internal Auditor", "State Auditor"),
		"Supplier Quotation": ("Procurement Officer", "Treasurer", "Internal Auditor", "State Auditor"),
		"Purchase Order": ("Procurement Officer", "Treasurer", "Internal Auditor", "State Auditor"),
		"Purchase Receipt": ("Procurement Officer", "Treasurer", "Internal Auditor", "State Auditor"),
		"Purchase Invoice": ("Treasurer", "Procurement Officer", "Internal Auditor", "State Auditor"),
	}
	read_only_doctypes = {"GL Entry"}
	for doctype, roles in permissions.items():
		for role in roles:
			filters = {"parent": doctype, "role": role, "permlevel": 0}
			if frappe.db.exists("Custom DocPerm", filters):
				continue
			write = doctype not in read_only_doctypes and role not in {"Internal Auditor", "State Auditor"}
			frappe.get_doc({
				"doctype": "Custom DocPerm", **filters, "read": 1, "report": 1, "export": 1,
				"create": int(write), "write": int(write), "submit": int(write), "cancel": int(write),
			}).insert()


def _ensure_project_custom_fields():
	"""ERPNext's Project already carries `company` natively (used for LGA scoping via
	the existing dtmgp.permissions.hr.project_query/has_permission hooks), but has no
	site/funding fields for the Projects, Assets & Field Monitoring module's Project
	Locations/Funding Sources views -- add them as Custom Fields rather than a parallel
	DocType, same reasoning as the HR Exit Type field above."""
	if not frappe.db.exists("Custom Field", {"dt": "Project", "fieldname": PROJECT_LOCATION_FIELD}):
		frappe.get_doc({
			"doctype": "Custom Field", "dt": "Project", "fieldname": PROJECT_LOCATION_FIELD,
			"label": "Project Location", "fieldtype": "Link", "options": "Location", "insert_after": "department",
		}).insert()
	if not frappe.db.exists("Custom Field", {"dt": "Project", "fieldname": PROJECT_FUNDING_SOURCE_FIELD}):
		frappe.get_doc({
			"doctype": "Custom Field", "dt": "Project", "fieldname": PROJECT_FUNDING_SOURCE_FIELD,
			"label": "Funding Source", "fieldtype": "Select", "options": "State\nFederal\nDonor\nLGA Counterpart\nOther",
			"insert_after": PROJECT_LOCATION_FIELD, "in_list_view": 1,
		}).insert()
	# ERPNext's Vehicle (fleet register) has no `company` field at all -- add one so
	# dtmgp.permissions.projects.vehicle_query/has_permission can scope it per LGA the
	# same way Project already is.
	if not frappe.db.exists("Custom Field", {"dt": "Vehicle", "fieldname": VEHICLE_COMPANY_FIELD}):
		frappe.get_doc({
			"doctype": "Custom Field", "dt": "Vehicle", "fieldname": VEHICLE_COMPANY_FIELD,
			"label": "LGA", "fieldtype": "Link", "options": "Company", "insert_after": "license_plate",
			"in_list_view": 1, "reqd": 1,
		}).insert()


def _ensure_projects_permissions():
	"""Grant the Projects, Assets & Field Monitoring roles access to the native
	ERPNext/HRMS doctypes this module is built on, instead of duplicating them as
	dtmgp DocTypes. Matches docs/role-permission-matrix.md's "Projects/assets" column:
	Project Officer is the sole CRUSA (create+write) role; State Administrator also
	gets create+write, matching the cross-cutting override precedent already used for
	every other DTMGP doctype's permissions (e.g. dtmgp_procurement_case.json), even
	though the matrix's letter for State Administrator here is narrower (RA); LGA
	Chairman/LGA Secretary are write-only (approve an existing record, not create) on
	Project specifically, where dtmgp/api/v1/projects.py's TRANSITIONS map gives them
	an approval step (cancelling a project) -- they have no approval step on the other
	doctypes here, so they're read-only there; everyone else in PROJECTS_VIEW_ROLES is
	read-only, even roles (LGA Administrator, Treasurer, Procurement Officer) that
	write elsewhere (HR, Finance). Project/Task already have HR-owned Custom DocPerm
	rows (see _ensure_hr_permissions) for State Administrator/LGA Administrator/HR
	Officer/Internal Auditor/State Auditor/Read-only Officer -- those are left alone;
	this only *adds* the remaining Projects-module roles that don't have a row yet."""
	create_roles = {"State Administrator", "Project Officer"}
	approve_only_roles = {"LGA Chairman", "LGA Secretary"}
	view_only_roles = {"LGA Administrator", "Treasurer", "Procurement Officer", "State Executive Viewer", "Internal Auditor", "State Auditor", "Read-only Officer"}
	permissions = {
		"Project": create_roles | approve_only_roles | view_only_roles,
		"Task": create_roles | approve_only_roles | view_only_roles,
		"Asset": create_roles | view_only_roles,
		"Asset Category": create_roles | view_only_roles,
		"Location": create_roles | view_only_roles,
		"Asset Movement": create_roles | view_only_roles,
		"Asset Maintenance": create_roles | view_only_roles,
		"Asset Maintenance Log": create_roles | view_only_roles,
		"Vehicle": create_roles | view_only_roles,
		"Vehicle Log": create_roles | view_only_roles,
	}
	for doctype, roles in permissions.items():
		for role in roles:
			filters = {"parent": doctype, "role": role, "permlevel": 0}
			if frappe.db.exists("Custom DocPerm", filters):
				continue
			create = role in create_roles
			write = create or role in approve_only_roles
			frappe.get_doc({
				"doctype": "Custom DocPerm", **filters, "read": 1, "report": 1, "export": 1,
				"create": int(create), "write": int(write), "submit": int(create), "cancel": int(create),
				"share": int(write),
			}).insert()


def _ensure_organization_setup_permissions():
	"""Designation and Fiscal Year back System Administration's Organization Setup
	section (Location is already granted by _ensure_projects_permissions above).
	Designation is shared statewide with no `company` field, same treatment as
	Supplier elsewhere, so every System Administration role (System Manager, State
	Administrator, LGA Administrator) can manage it. Fiscal Year is also global but
	defines the accounting calendar every LGA's Budget/Procurement Plan/Allocation
	runs on -- letting any of 23 LGA Administrators edit or disable it would affect
	every other LGA's ledger, so its write stays state-admin only even though read
	is shared with the rest of Organization Setup (enforced again in
	dtmgp.api.v1.administration.save_reference_record's STATE_ONLY_RECORD_TYPES)."""
	permissions = {
		"Designation": {
			"State Administrator": (1, 1, 1),
			"LGA Administrator": (1, 1, 1),
			"HR Officer": (1, 1, 1),
			"LGA Chairman": (1, 0, 0),
			"LGA Secretary": (1, 0, 0),
			"Internal Auditor": (1, 0, 0),
			"Read-only Officer": (1, 0, 0),
		},
		"Fiscal Year": {
			"State Administrator": (1, 1, 1),
			"LGA Administrator": (1, 0, 0),
			"Treasurer": (1, 0, 0),
			"Internal Auditor": (1, 0, 0),
			"State Auditor": (1, 0, 0),
		},
	}
	for doctype, roles in permissions.items():
		for role, (read, write, create) in roles.items():
			filters = {"parent": doctype, "role": role, "permlevel": 0}
			if not frappe.db.exists("Custom DocPerm", filters):
				frappe.get_doc({"doctype": "Custom DocPerm", **filters, "read": read, "write": write, "create": create}).insert()

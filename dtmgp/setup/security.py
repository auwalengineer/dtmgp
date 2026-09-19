import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from dtmgp.setup.organization import BENUE_LGAS, PARENT_COMPANY

ADMIN_ROLES = ("State Administrator", "LGA Administrator")
DEFAULT_HOLIDAY_LIST = "Benue LGA Standard Holidays"
USER_LGA_FIELD = "dtmgp_lga"
EMPLOYEE_GRADE_FIELD = "dtmgp_grade_level"
EMPLOYEE_VERIFICATION_FIELD = "dtmgp_verification_status"
EMPLOYEE_SEPARATION_EXIT_TYPE_FIELD = "dtmgp_exit_type"
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
		"Payment Entry": ("Treasurer", "Revenue Officer", "Internal Auditor", "State Auditor"),
		"Bank Transaction": ("Treasurer", "Internal Auditor", "State Auditor"),
		"Supplier": ("Procurement Officer", "Treasurer", "Internal Auditor", "State Auditor"),
		"Material Request": ("Procurement Officer", "Treasurer", "Internal Auditor", "State Auditor"),
		"Request for Quotation": ("Procurement Officer", "Treasurer", "Internal Auditor", "State Auditor"),
		"Supplier Quotation": ("Procurement Officer", "Treasurer", "Internal Auditor", "State Auditor"),
		"Purchase Order": ("Procurement Officer", "Treasurer", "Internal Auditor", "State Auditor"),
		"Purchase Receipt": ("Procurement Officer", "Treasurer", "Internal Auditor", "State Auditor"),
		"Purchase Invoice": ("Treasurer", "Procurement Officer", "Internal Auditor", "State Auditor"),
	}
	for doctype, roles in permissions.items():
		for role in roles:
			filters = {"parent": doctype, "role": role, "permlevel": 0}
			if frappe.db.exists("Custom DocPerm", filters):
				continue
			write = role not in {"Internal Auditor", "State Auditor"}
			frappe.get_doc({
				"doctype": "Custom DocPerm", **filters, "read": 1, "report": 1, "export": 1,
				"create": int(write), "write": int(write), "submit": int(write), "cancel": int(write),
			}).insert()

import frappe

ADMIN_ROLES = ("State Administrator", "LGA Administrator")
USER_LGA_FIELD = "dtmgp_lga"
EMPLOYEE_GRADE_FIELD = "dtmgp_grade_level"
EMPLOYEE_VERIFICATION_FIELD = "dtmgp_verification_status"
PLATFORM_ROLES = (
	"State Administrator",
	"State Executive Viewer",
	"State Auditor",
	"LGA Administrator",
	"LGA Chairman",
	"LGA Secretary",
	"Treasurer",
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
	_ensure_hr_permissions()


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
		"Department": {
			"State Administrator": (1, 1, 1),
			"LGA Administrator": (1, 1, 1),
			"HR Officer": (1, 1, 1),
		},
		"Leave Application": {
			"State Administrator": (1, 1, 1),
			"LGA Administrator": (1, 1, 0),
			"HR Officer": (1, 1, 1),
			"LGA Chairman": (1, 0, 0),
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
					}
				).insert()

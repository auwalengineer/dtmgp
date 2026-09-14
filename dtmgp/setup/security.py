import frappe

ADMIN_ROLES = ("State Administrator", "LGA Administrator")
USER_LGA_FIELD = "dtmgp_lga"
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

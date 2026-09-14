import frappe

from dtmgp.permissions.scope import can_manage_users, get_allowed_companies, is_state_user
from dtmgp.setup.security import USER_LGA_FIELD

STATE_ONLY_ROLES = {"State Administrator", "State Auditor", "State Executive Viewer"}


def validate_user_scope(doc, method=None):
	actor = frappe.session.user
	if actor in {"Administrator", "Guest"} or is_state_user(actor):
		return
	if not can_manage_users(actor):
		return

	company = doc.get(USER_LGA_FIELD)
	if not company or company not in get_allowed_companies(actor):
		frappe.throw("Select a Local Government Area within your permitted scope", frappe.PermissionError)

	roles = {row.role for row in doc.roles}
	if roles & STATE_ONLY_ROLES or "System Manager" in roles:
		frappe.throw("You cannot assign state administration roles", frappe.PermissionError)


def sync_user_lga_permission(doc, method=None):
	company = doc.get(USER_LGA_FIELD)
	if not company:
		return

	existing = frappe.get_all(
		"User Permission",
		filters={"user": doc.name, "allow": "Company"},
		pluck="name",
	)
	for permission_name in existing:
		frappe.delete_doc("User Permission", permission_name, ignore_permissions=True)

	frappe.get_doc(
		{
			"doctype": "User Permission",
			"user": doc.name,
			"allow": "Company",
			"for_value": company,
			"is_default": 1,
			"apply_to_all_doctypes": 1,
		}
	).insert(ignore_permissions=True)

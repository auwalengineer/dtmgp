import frappe
from frappe.core.doctype.user_permission.user_permission import get_user_permissions

from dtmgp.setup.organization import PARENT_COMPANY

STATE_ROLES = {"System Manager", "State Administrator", "State Executive Viewer", "State Auditor"}
USER_ADMIN_ROLES = {"System Manager", "State Administrator", "LGA Administrator"}


def get_user_roles(user=None):
	user = user or frappe.session.user
	return set(frappe.get_roles(user))


def is_state_user(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & STATE_ROLES)


def can_manage_users(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & USER_ADMIN_ROLES)


def get_allowed_companies(user=None):
	user = user or frappe.session.user
	if user == "Guest":
		return []
	if is_state_user(user):
		return frappe.get_all(
			"Company",
			filters={"parent_company": PARENT_COMPANY, "is_group": 0},
			pluck="name",
			order_by="company_name asc",
		)
	permissions = get_user_permissions(user).get("Company", [])
	allowed = {permission.doc for permission in permissions}
	return sorted(
		company
		for company in allowed
		if frappe.db.get_value("Company", company, "parent_company") == PARENT_COMPANY
	)


def require_user_admin():
	if not can_manage_users():
		frappe.throw("You are not permitted to manage users", frappe.PermissionError)

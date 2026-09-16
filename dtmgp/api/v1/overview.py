import frappe

from dtmgp.permissions.scope import get_requested_companies, get_scoped_user_names, is_state_user, require_authenticated_user
from dtmgp.setup.security import PLATFORM_ROLES


@frappe.whitelist()
def get_overview(company=None):
	require_authenticated_user()
	companies = get_requested_companies(company)
	user_names = get_scoped_user_names(companies=companies)
	users = _get_users(user_names)
	roles = set(frappe.get_roles())
	admin_roles = {"System Manager", "State Administrator", "LGA Administrator"}

	return {
		"scope": "Statewide" if is_state_user() and not company else (companies[0] if companies else "No LGA assigned"),
		"lga_count": len(companies),
		"user_count": len(users),
		"active_user_count": sum(1 for user in users if user.enabled),
		"disabled_user_count": sum(1 for user in users if not user.enabled),
		"unassigned_role_count": sum(1 for user in users if not _platform_roles(user.name)),
		"can_manage_users": bool(roles & admin_roles) or frappe.session.user == "Administrator",
		"is_statewide": is_state_user(),
	}


def _get_users(user_names):
	if not user_names:
		return []
	return frappe.get_all(
		"User",
		filters={"name": ["in", user_names], "user_type": "System User"},
		fields=["name", "enabled"],
	)


def _platform_roles(user):
	return set(frappe.get_roles(user)) & set(PLATFORM_ROLES)

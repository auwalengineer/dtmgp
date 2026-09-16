import frappe

from dtmgp.navigation import get_navigation

from dtmgp.permissions.scope import (
	can_manage_hr,
	can_manage_users,
	can_view_hr,
	get_allowed_companies,
	is_state_user,
	require_authenticated_user,
)


@frappe.whitelist()
def get_current_user_context():
	require_authenticated_user()
	user = frappe.get_cached_doc("User", frappe.session.user)
	companies = get_allowed_companies()
	default_company = frappe.defaults.get_user_default("Company")
	active_company = default_company if default_company in companies else (companies[0] if companies else None)
	return {
		"user": {"email": user.name, "full_name": user.full_name, "roles": frappe.get_roles()},
		"allowed_lgas": companies,
		"active_lga": active_company,
		"can_change_lga": is_state_user() and len(companies) > 1,
		"can_manage_users": can_manage_users(),
		"can_view_hr": can_view_hr(),
		"can_manage_hr": can_manage_hr(),
		"navigation": get_navigation(),
		"csrf_token": frappe.session.data.csrf_token,
	}

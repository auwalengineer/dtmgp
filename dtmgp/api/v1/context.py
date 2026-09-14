import frappe

from dtmgp.permissions.scope import can_manage_users, get_allowed_companies, is_state_user


@frappe.whitelist()
def get_current_user_context():
	if frappe.session.user == "Guest":
		frappe.throw("Authentication required", frappe.AuthenticationError)
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
		"csrf_token": frappe.session.data.csrf_token,
	}

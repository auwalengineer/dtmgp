import frappe

from dtmgp.permissions.scope import can_manage_users, get_allowed_companies, is_state_user


def get_permission_query_conditions(user=None):
	user = user or frappe.session.user
	if is_state_user(user):
		return ""
	if not can_manage_users(user):
		return f"`tabUser`.`name` = {frappe.db.escape(user)}"
	companies = get_allowed_companies(user)
	if not companies:
		return "1 = 0"
	company_values = ", ".join(frappe.db.escape(company) for company in companies)
	return (
		"(`tabUser`.`name` = {user} or exists (select 1 from `tabUser Permission` up "
		"where up.user = `tabUser`.`name` and up.allow = 'Company' "
		"and up.for_value in ({companies})))"
	).format(user=frappe.db.escape(user), companies=company_values)


def has_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if is_state_user(user) or doc.name == user:
		return True
	if not can_manage_users(user):
		return False
	if permission_type == "create" or doc.is_new():
		return True
	allowed = set(get_allowed_companies(user))
	target = set(
		frappe.get_all(
			"User Permission",
			filters={"user": doc.name, "allow": "Company"},
			pluck="for_value",
		)
	)
	return bool(target) and target.issubset(allowed)

import frappe
from frappe.core.doctype.user_permission.user_permission import get_user_permissions

from dtmgp.setup.organization import PARENT_COMPANY

STATE_ROLES = {"System Manager", "State Administrator", "State Executive Viewer", "State Auditor"}
USER_ADMIN_ROLES = {"System Manager", "State Administrator", "LGA Administrator"}
HR_VIEW_ROLES = {
	"System Manager", "State Administrator", "State Executive Viewer", "State Auditor",
	"LGA Administrator", "LGA Chairman", "LGA Secretary", "HR Officer", "Internal Auditor", "Read-only Officer",
}
HR_MANAGE_ROLES = {"System Manager", "State Administrator", "LGA Administrator", "HR Officer"}


def get_user_roles(user=None):
	user = user or frappe.session.user
	return set(frappe.get_roles(user))


def is_state_user(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & STATE_ROLES)


def can_manage_users(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & USER_ADMIN_ROLES)


def can_view_hr(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & HR_VIEW_ROLES)


def can_manage_hr(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & HR_MANAGE_ROLES)


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


def get_requested_companies(company=None, user=None):
	companies = get_allowed_companies(user)
	if not company:
		return companies
	if company not in companies:
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "Requested LGA is outside the user's scope", company=company)
		frappe.throw("LGA is outside your permitted scope", frappe.PermissionError)
	return [company]


def get_scoped_user_names(user=None, companies=None):
	companies = companies if companies is not None else get_allowed_companies(user)
	if not companies:
		return []
	return list(
		dict.fromkeys(
			frappe.get_all(
				"User Permission",
				filters={"allow": "Company", "for_value": ["in", companies]},
				pluck="user",
			)
		)
	)


def require_authenticated_user():
	if frappe.session.user == "Guest":
		from dtmgp.audit import record_denial

		record_denial("authentication_required", "Guest attempted to access an authenticated service")
		frappe.throw("Authentication required", frappe.AuthenticationError)


def require_user_admin():
	require_authenticated_user()
	if not can_manage_users():
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "User administration access denied")
		frappe.throw("You are not permitted to manage users", frappe.PermissionError)


def require_hr_access(write=False):
	require_authenticated_user()
	allowed = can_manage_hr() if write else can_view_hr()
	if not allowed:
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "People and HR access denied")
		frappe.throw("You are not permitted to access People and HR", frappe.PermissionError)

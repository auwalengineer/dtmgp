import frappe
from frappe.core.doctype.user_permission.user_permission import get_user_permissions

from dtmgp.setup.organization import PARENT_COMPANY

STATE_ROLES = {"System Manager", "State Administrator", "State Executive Viewer", "State Auditor"}
USER_ADMIN_ROLES = {"System Manager", "State Administrator", "LGA Administrator"}
# Narrower than STATE_ROLES: excludes State Executive Viewer/State Auditor, matching
# navigation.py's STATE_ONLY nav-role set for System Administration's Workflow Setup,
# Communication Setup, Reference Data and Security & Audit sections.
STATE_ONLY_ROLES = {"System Manager", "State Administrator"}
HR_VIEW_ROLES = {
	"System Manager", "State Administrator", "State Executive Viewer", "State Auditor",
	"LGA Administrator", "LGA Chairman", "LGA Secretary", "HR Officer", "Internal Auditor", "Read-only Officer",
}
HR_MANAGE_ROLES = {"System Manager", "State Administrator", "LGA Administrator", "HR Officer"}
RESTRICTED_HR_VIEW_ROLES = {"System Manager", "State Administrator", "State Auditor", "LGA Administrator", "HR Officer", "Internal Auditor"}
STAFF_AUDIT_ROLES = {"System Manager", "State Administrator", "State Auditor", "Internal Auditor"}
PAYROLL_ROLES = STATE_ROLES | {"Treasurer"}
FINANCE_VIEW_ROLES = STATE_ROLES | {
	"LGA Administrator", "LGA Chairman", "LGA Secretary", "Treasurer", "Revenue Officer",
	"Procurement Officer", "Internal Auditor", "Read-only Officer",
}
FINANCE_MANAGE_ROLES = {"System Manager", "State Administrator", "LGA Administrator", "LGA Chairman", "Treasurer", "Revenue Officer", "Procurement Officer", "Internal Auditor", "State Auditor"}
GOVERNANCE_VIEW_ROLES = STATE_ROLES | {
	"LGA Administrator", "LGA Chairman", "LGA Secretary", "Treasurer", "HR Officer",
	"Procurement Officer", "Project Officer", "Traditional Affairs Officer", "Internal Auditor", "Read-only Officer",
}
GOVERNANCE_MANAGE_ROLES = {"System Manager", "State Administrator", "LGA Administrator", "LGA Chairman", "LGA Secretary"}
TRADITIONAL_VIEW_ROLES = STATE_ROLES | {
	"LGA Administrator", "LGA Chairman", "LGA Secretary", "Traditional Affairs Officer", "Internal Auditor", "Read-only Officer",
}
TRADITIONAL_MANAGE_ROLES = {"System Manager", "State Administrator", "LGA Administrator", "LGA Chairman", "LGA Secretary", "Traditional Affairs Officer"}
PROJECTS_VIEW_ROLES = STATE_ROLES | {
	"LGA Administrator", "LGA Chairman", "LGA Secretary", "Treasurer",
	"Procurement Officer", "Project Officer", "Internal Auditor", "Read-only Officer",
}
# Per docs/role-permission-matrix.md's "Projects/assets" column: Project Officer is
# the sole CRUSA (full) role; State Administrator, LGA Chairman and LGA Secretary are
# RA (approve existing records, not create); LGA Administrator, Treasurer and
# Procurement Officer are R only here even though they write elsewhere (Finance,
# HR). PROJECTS_CREATE_ROLES (dtmgp/projects.py) narrows this further to who may
# create a new record; PROJECTS_MANAGE_ROLES is the broader "may call a write
# endpoint at all" gate covering create *and* approve.
PROJECTS_MANAGE_ROLES = {"System Manager", "State Administrator", "Project Officer", "LGA Chairman", "LGA Secretary"}
ANALYTICS_VIEW_ROLES = STATE_ROLES | {
	"LGA Administrator", "LGA Chairman", "LGA Secretary", "Treasurer", "Revenue Officer", "HR Officer",
	"Procurement Officer", "Project Officer", "Traditional Affairs Officer", "Internal Auditor", "Read-only Officer",
}


def get_user_roles(user=None):
	user = user or frappe.session.user
	return set(frappe.get_roles(user))


def is_state_user(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & STATE_ROLES)


def can_manage_users(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & USER_ADMIN_ROLES)


def can_manage_system_config(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & STATE_ONLY_ROLES)


def can_manage_system_operations(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or "System Manager" in get_user_roles(user)


def can_view_hr(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & HR_VIEW_ROLES)


def can_manage_hr(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & HR_MANAGE_ROLES)


def can_view_restricted_hr(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & RESTRICTED_HR_VIEW_ROLES)


def require_restricted_hr_access(write=False):
	require_authenticated_user()
	allowed = can_manage_hr() if write else can_view_restricted_hr()
	if not allowed:
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "Restricted personnel record access denied")
		frappe.throw("You are not permitted to access restricted personnel records", frappe.PermissionError)


def can_view_finance(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & FINANCE_VIEW_ROLES)


def can_manage_finance(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & FINANCE_MANAGE_ROLES)


def can_view_governance(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & GOVERNANCE_VIEW_ROLES)


def can_manage_governance(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & GOVERNANCE_MANAGE_ROLES)


def can_view_traditional(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & TRADITIONAL_VIEW_ROLES)


def can_manage_traditional(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & TRADITIONAL_MANAGE_ROLES)


def can_view_projects(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & PROJECTS_VIEW_ROLES)


def can_manage_projects(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & PROJECTS_MANAGE_ROLES)


def can_view_analytics(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & ANALYTICS_VIEW_ROLES)


def can_compare_lgas(user=None):
	return is_state_user(user)


def require_analytics_access(statewide=False):
	require_authenticated_user()
	allowed = can_compare_lgas() if statewide else can_view_analytics()
	if not allowed:
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "Executive analytics access denied", metadata={"statewide": statewide})
		frappe.throw("You are not permitted to access Executive Dashboard and Analytics", frappe.PermissionError)


def require_finance_access(write=False):
	require_authenticated_user()
	allowed = can_manage_finance() if write else can_view_finance()
	if not allowed:
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "Finance, Revenue and Procurement access denied")
		frappe.throw("You are not permitted to access Finance, Revenue and Procurement", frappe.PermissionError)


def require_governance_access(write=False):
	require_authenticated_user()
	allowed = can_manage_governance() if write else can_view_governance()
	if not allowed:
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "Administration and Governance access denied")
		frappe.throw("You are not permitted to access Administration and Governance", frappe.PermissionError)


def require_traditional_access(write=False):
	require_authenticated_user()
	allowed = can_manage_traditional() if write else can_view_traditional()
	if not allowed:
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "Chieftaincy and Traditional Institutions access denied")
		frappe.throw("You are not permitted to access Chieftaincy and Traditional Institutions", frappe.PermissionError)


def require_projects_access(write=False):
	require_authenticated_user()
	allowed = can_manage_projects() if write else can_view_projects()
	if not allowed:
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "Projects, Assets and Field Monitoring access denied")
		frappe.throw("You are not permitted to access Projects, Assets and Field Monitoring", frappe.PermissionError)


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


def require_state_admin():
	require_authenticated_user()
	if not can_manage_system_config():
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "State-level system administration access denied")
		frappe.throw("You are not permitted to manage this system configuration", frappe.PermissionError)


def require_system_manager():
	require_authenticated_user()
	if not can_manage_system_operations():
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "System operations access denied")
		frappe.throw("You are not permitted to access system operations", frappe.PermissionError)


def require_hr_access(write=False):
	require_authenticated_user()
	allowed = can_manage_hr() if write else can_view_hr()
	if not allowed:
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "People and HR access denied")
		frappe.throw("You are not permitted to access People and HR", frappe.PermissionError)


def can_view_staff_audit(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & STAFF_AUDIT_ROLES)


def can_view_payroll(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(get_user_roles(user) & PAYROLL_ROLES)


def require_staff_audit_access(user=None):
	require_authenticated_user()
	if not can_view_staff_audit(user):
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "Staff audit access denied")
		frappe.throw("You are not permitted to access staff audit records", frappe.PermissionError)


def require_payroll_access(user=None):
	require_authenticated_user()
	if not can_view_payroll(user):
		from dtmgp.audit import record_denial

		record_denial("authorization_denied", "Payroll access denied")
		frappe.throw("You are not permitted to access payroll records", frappe.PermissionError)

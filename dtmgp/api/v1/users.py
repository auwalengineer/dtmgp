import frappe
from frappe.utils import cint

from dtmgp.permissions.scope import get_allowed_companies, get_requested_companies, get_scoped_user_names, is_state_user, require_user_admin
from dtmgp.setup.security import PLATFORM_ROLES


@frappe.whitelist()
def list_users(page=1, page_size=20, search=None, company=None):
	require_user_admin()
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	companies = get_requested_companies(company)
	if not companies:
		return {"items": [], "total": 0, "page": page, "page_size": page_size}

	user_names = get_scoped_user_names(companies=companies)
	user_filters = {"name": ["in", user_names], "user_type": "System User"}
	if search:
		user_filters["full_name"] = ["like", f"%{search.strip()}%"]
	users = frappe.get_all(
		"User",
		filters=user_filters,
		fields=["name", "full_name", "enabled", "last_active"],
		start=(page - 1) * page_size,
		page_length=page_size,
		order_by="full_name asc",
	)
	for user in users:
		user["lgas"] = frappe.get_all(
			"User Permission",
			filters={"user": user.name, "allow": "Company", "for_value": ["in", companies]},
			pluck="for_value",
		)
		user["roles"] = [role for role in frappe.get_roles(user.name) if role in PLATFORM_ROLES]
	return {"items": users, "total": len(user_names), "page": page, "page_size": page_size}


@frappe.whitelist(methods=["POST"])
def create_user(email, first_name, role, company, last_name=None, temporary_password=None):
	require_user_admin()
	_validate_assignment(role, company)
	if frappe.db.exists("User", email.lower().strip()):
		frappe.throw("A user with this email already exists", frappe.DuplicateEntryError)
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email.lower().strip(),
			"first_name": first_name.strip(),
			"last_name": (last_name or "").strip(),
			"enabled": 1,
			"send_welcome_email": 0,
			"new_password": temporary_password or None,
			"dtmgp_lga": company,
			"roles": [{"role": role}],
		}
	)
	user.insert()
	return {"name": user.name, "full_name": user.full_name, "company": company, "role": role}


@frappe.whitelist(methods=["POST"])
def set_user_enabled(user, enabled):
	require_user_admin()
	if user in (frappe.session.user, "Administrator", "Guest"):
		frappe.throw("This account cannot be changed here")
	_require_user_in_scope(user)
	doc = frappe.get_doc("User", user)
	doc.enabled = cint(enabled)
	doc.save()
	return {"name": doc.name, "enabled": doc.enabled}


@frappe.whitelist(methods=["POST"])
def update_user(user, first_name, role, company, last_name=None):
	require_user_admin()
	if user in (frappe.session.user, "Administrator", "Guest"):
		frappe.throw("This account's access cannot be changed here")
	_require_user_in_scope(user)
	_validate_assignment(role, company)

	doc = frappe.get_doc("User", user)
	doc.first_name = first_name.strip()
	doc.last_name = (last_name or "").strip()
	doc.dtmgp_lga = company
	for row in list(doc.roles):
		if row.role in PLATFORM_ROLES:
			doc.remove(row)
	doc.append("roles", {"role": role})
	doc.save()
	return {"name": doc.name, "full_name": doc.full_name, "company": company, "role": role}


def _require_user_in_scope(user):
	if user not in get_scoped_user_names():
		frappe.throw("You are not permitted to manage this user", frappe.PermissionError)


def _validate_assignment(role, company):
	if role not in PLATFORM_ROLES or role in {"State Administrator", "State Auditor", "State Executive Viewer"} and not is_state_user():
		frappe.throw("Role is not available for assignment", frappe.PermissionError)
	if company not in get_allowed_companies():
		frappe.throw("LGA is outside your permitted scope", frappe.PermissionError)

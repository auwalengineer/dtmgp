import frappe
from frappe.utils import cint

from dtmgp.permissions.scope import get_allowed_companies, is_state_user, require_user_admin
from dtmgp.setup.security import PLATFORM_ROLES


@frappe.whitelist()
def list_users(page=1, page_size=20, search=None):
	require_user_admin()
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	companies = get_allowed_companies()
	if not companies:
		return {"items": [], "total": 0, "page": page, "page_size": page_size}

	filters = {"allow": "Company", "for_value": ["in", companies]}
	user_names = list(dict.fromkeys(frappe.get_all("User Permission", filters=filters, pluck="user")))
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
	if not is_state_user():
		target_companies = set(
			frappe.get_all("User Permission", filters={"user": user, "allow": "Company"}, pluck="for_value")
		)
		if not target_companies or not target_companies.issubset(set(get_allowed_companies())):
			frappe.throw("You are not permitted to manage this user", frappe.PermissionError)
	doc = frappe.get_doc("User", user)
	doc.enabled = cint(enabled)
	doc.save()
	return {"name": doc.name, "enabled": doc.enabled}


def _validate_assignment(role, company):
	if role not in PLATFORM_ROLES or role in {"State Administrator", "State Auditor", "State Executive Viewer"} and not is_state_user():
		frappe.throw("Role is not available for assignment", frappe.PermissionError)
	if company not in get_allowed_companies():
		frappe.throw("LGA is outside your permitted scope", frappe.PermissionError)

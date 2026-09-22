from collections import Counter

import frappe
from frappe.utils import cint

from dtmgp.permissions.scope import (
	get_requested_companies,
	get_scoped_user_names,
	is_state_user,
	require_state_admin,
	require_system_manager,
	require_user_admin,
)
from dtmgp.setup.security import PLATFORM_ROLES


@frappe.whitelist()
def get_dashboard(company=None):
	require_user_admin()
	companies = get_requested_companies(company)
	user_names = get_scoped_user_names(companies=companies)
	users = _get_users(user_names)
	role_counts = Counter()
	for user in users:
		role_counts.update(role for role in frappe.get_roles(user.name) if role in PLATFORM_ROLES)

	return {
		"scope": "Statewide" if is_state_user() and not company else (companies[0] if companies else "No LGA assigned"),
		"lga_count": len(companies),
		"user_count": len(users),
		"active_user_count": sum(1 for user in users if user.enabled),
		"disabled_user_count": sum(1 for user in users if not user.enabled),
		"roles": [{"role": role, "count": count} for role, count in role_counts.most_common()],
		"recent_users": [
			{
				"name": user.name,
				"full_name": user.full_name,
				"enabled": user.enabled,
				"last_active": user.last_active,
			}
			for user in users[:5]
		],
	}


def _get_users(user_names):
	if not user_names:
		return []
	return frappe.get_all(
		"User",
		filters={"name": ["in", user_names], "user_type": "System User"},
		fields=["name", "full_name", "enabled", "last_active", "creation"],
		order_by="creation desc",
	)


# ---------------------------------------------------------------------------
# User Management: Roles, Role Profiles, LGA Access, User Sessions
# ---------------------------------------------------------------------------


@frappe.whitelist()
def list_platform_roles():
	"""Read-only register of platform roles with how many in-scope users hold each.
	Role has no company field of its own, so "in scope" is derived by counting only
	among the users get_scoped_user_names already permits the caller to see."""
	require_user_admin()
	user_names = get_scoped_user_names()
	counts = Counter()
	for user in user_names:
		counts.update(role for role in frappe.get_roles(user) if role in PLATFORM_ROLES or role == "System Manager")
	roles = (*PLATFORM_ROLES, "System Manager")
	return [
		{"role": role, "desk_access": frappe.db.get_value("Role", role, "desk_access"), "user_count": counts.get(role, 0)}
		for role in roles
	]


@frappe.whitelist()
def list_role_profiles():
	"""Read-only register of Role Profiles, seeded 1:1 with PLATFORM_ROLES by
	dtmgp.setup.security.seed_role_profiles (FND-003)."""
	require_user_admin()
	profiles = frappe.get_all("Role Profile", fields=["name"], order_by="name")
	for profile in profiles:
		profile["roles"] = frappe.get_all(
			"Has Role", filters={"parent": profile.name, "parenttype": "Role Profile"}, pluck="role"
		)
	return profiles


@frappe.whitelist()
def list_lga_access(company=None):
	"""Access register grouping Company User Permission grants by LGA -- a review
	screen across the caller's scope, distinct from the Users list/edit form."""
	require_user_admin()
	rows = []
	for lga in get_requested_companies(company):
		user_names = frappe.get_all("User Permission", filters={"allow": "Company", "for_value": lga}, pluck="user")
		if not user_names:
			continue
		users = frappe.get_all(
			"User",
			filters={"name": ["in", user_names], "user_type": "System User"},
			fields=["name", "full_name", "enabled"],
			order_by="full_name",
		)
		for user in users:
			user["roles"] = [role for role in frappe.get_roles(user.name) if role in PLATFORM_ROLES]
		rows.append({"company": lga, "users": users})
	return rows


@frappe.whitelist()
def list_user_sessions(company=None):
	"""Active session register read from Frappe's raw `tabSessions` table -- there is
	no Session DocType to query via frappe.get_all. Scoped to the caller's allowed
	users the same way list_users is; never selects `sessiondata`, which can hold
	form state and CSRF tokens."""
	require_user_admin()
	user_names = get_scoped_user_names(companies=get_requested_companies(company))
	if not user_names:
		return []
	placeholders = ", ".join(["%s"] * len(user_names))
	rows = frappe.db.sql(
		f"""select `user`, `sid`, `ipaddress`, `lastupdate`, `status`
			from `tabSessions` where `user` in ({placeholders}) order by `lastupdate` desc""",
		user_names,
		as_dict=True,
	)
	for row in rows:
		row["sid"] = f"{row['sid'][:8]}…" if row.get("sid") else None
	return rows


# ---------------------------------------------------------------------------
# Organization Setup: LGAs, Designations, Fiscal Years; Reference Data: Locations
# ---------------------------------------------------------------------------


@frappe.whitelist()
def list_lga_profiles():
	"""Statewide LGA directory. LGA Profile already grants LGA Administrator
	read access to the whole registry at the doctype level (see lga_profile.json) --
	this mirrors that, not a new scoping decision."""
	require_user_admin()
	return frappe.get_all("LGA Profile", fields=["name", "lga_name", "lga_code", "company", "enabled"], order_by="lga_name")


@frappe.whitelist(methods=["POST"])
def set_lga_profile_enabled(lga_code, enabled):
	require_state_admin()
	doc = frappe.get_doc("LGA Profile", lga_code)
	doc.enabled = cint(enabled)
	doc.save()
	return {"name": doc.name, "enabled": doc.enabled}


# Designation and Location are shared statewide reference masters (no `company`
# field), same treatment as Supplier elsewhere -- any System Administration role can
# manage them. Fiscal Year is also global but defines the accounting calendar every
# LGA's ledger runs on, so unlike the other two its write is held to state admins only
# (see save_reference_record) even though the read view is available to the same
# audience as the rest of Organization Setup.
RECORD_FIELDS = {
	"Designation": ["designation_name", "description"],
	"Fiscal Year": ["year", "year_start_date", "year_end_date", "disabled"],
	"Location": ["location_name", "parent_location", "is_group", "latitude", "longitude"],
}
EDITABLE_FIELDS = {
	"Designation": {"designation_name", "description"},
	"Fiscal Year": {"year", "year_start_date", "year_end_date", "disabled"},
	"Location": {"location_name", "parent_location", "is_group", "latitude", "longitude"},
}
STATE_ONLY_RECORD_TYPES = {"Fiscal Year"}


@frappe.whitelist()
def list_reference_records(doctype):
	require_user_admin()
	if doctype not in RECORD_FIELDS:
		frappe.throw("Unsupported reference record type", frappe.PermissionError)
	return frappe.get_all(doctype, fields=["name", *RECORD_FIELDS[doctype]], order_by="name")


@frappe.whitelist(methods=["POST"])
def save_reference_record(doctype, values, name=None):
	if doctype in STATE_ONLY_RECORD_TYPES:
		require_state_admin()
	else:
		require_user_admin()
	if doctype not in EDITABLE_FIELDS:
		frappe.throw("Unsupported reference record type", frappe.PermissionError)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	if not isinstance(values, dict):
		frappe.throw("Record values must be an object")
	doc = frappe.get_doc(doctype, name) if name else frappe.new_doc(doctype)
	for field in EDITABLE_FIELDS[doctype]:
		if field in values:
			doc.set(field, values[field])
	doc.save()
	return {"name": doc.name, "doctype": doc.doctype}


# ---------------------------------------------------------------------------
# Reference Data: Document Numbering
# ---------------------------------------------------------------------------

# Every DTMGP doctype that carries a document identifier, listed once here rather
# than duplicating docs/naming-and-coding-conventions.md by hand. Doctypes below use
# dtmgp.governance.lga_dated_autoname (a Python autoname() override, not a JSON
# `format:` string) to compose {TYPE}-{LGA_CODE}-{YYYY}-{#####}, so their type code
# is listed explicitly here -- frappe.get_meta().autoname is empty for a Python
# override and would otherwise misreport them as having no numbering scheme at all.
# The remaining finance/HR doctypes use a plain JSON `format:` autoname and are read
# from doctype metadata directly; several of them predate lga_dated_autoname and
# genuinely don't carry an LGA code segment -- this reports what's actually
# configured rather than restating the aspirational convention as if universal.
LGA_DATED_TYPE_CODES = {
	"DTMGP Correspondence": "COR", "DTMGP Meeting": "CM", "DTMGP Resolution": "RES",
	"DTMGP Resolution Action": "RAC", "DTMGP Statutory Return": "RET", "DTMGP Compliance Submission": "CMP",
	"DTMGP Traditional Institution": "INST", "DTMGP Traditional Ruler": "RUL", "DTMGP Ruling House": "RH",
	"DTMGP Traditional Appointment": "APPT", "DTMGP Succession Case": "SUCC",
	"DTMGP Chieftaincy Petition": "PET", "DTMGP Traditional Allowance": "ALLOW",
	"DTMGP Project Inspection": "INSP", "DTMGP Asset Verification": "AVER",
}
DOCUMENT_NUMBERING_DOCTYPES = (
	*LGA_DATED_TYPE_CODES,
	"DTMGP Allocation", "DTMGP Audit Query", "DTMGP Contract", "DTMGP Contract Variation",
	"DTMGP Payment Request", "DTMGP Procurement Case", "DTMGP Procurement Plan",
	"DTMGP Revenue Assessment", "DTMGP Revenue Head", "DTMGP Revenue Receipt",
	"DTMGP Approval Delegation", "DTMGP Approval Limit",
	"DTMGP Staff Verification Exercise", "DTMGP Staff Verification Record",
	"LGA Profile",
)


@frappe.whitelist()
def get_document_numbering_reference():
	require_state_admin()
	items = []
	for doctype in DOCUMENT_NUMBERING_DOCTYPES:
		if not frappe.db.exists("DocType", doctype):
			continue
		type_code = LGA_DATED_TYPE_CODES.get(doctype)
		autoname = f"{type_code}-{{LGA_CODE}}-{{YYYY}}-{{#####}}" if type_code else (frappe.get_meta(doctype).autoname or "")
		items.append({"doctype": doctype, "autoname": autoname})
	return items


# ---------------------------------------------------------------------------
# Security & Audit: Audit Logs, Login History (Permission Changes and Security
# Events are the same Audit Logs data, with preset event_type/outcome filters)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def list_audit_events(company=None, event_type=None, outcome=None, page=1, page_size=25):
	"""event_type accepts a comma-separated list (e.g. Security & Audit's Permission
	Changes preset needs both `permission_change` and `user_access_change`)."""
	require_state_admin()
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {}
	if company:
		filters["company"] = company
	if event_type:
		types = [item.strip() for item in event_type.split(",") if item.strip()]
		filters["event_type"] = types[0] if len(types) == 1 else ["in", types]
	if outcome:
		filters["outcome"] = outcome
	total = frappe.db.count("DTMGP Audit Event", filters)
	items = frappe.get_all(
		"DTMGP Audit Event",
		filters=filters,
		fields=["name", "occurred_at", "event_type", "outcome", "actor", "company", "reference_doctype", "reference_name", "summary", "metadata_json", "ip_address"],
		order_by="occurred_at desc",
		start=(page - 1) * page_size,
		page_length=page_size,
	)
	for item in items:
		item["metadata"] = frappe.parse_json(item.pop("metadata_json") or "{}")
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist()
def list_login_history(company=None, page=1, page_size=25):
	"""Activity Log has no company field of its own; company=None (the default for a
	state-level caller, the only audience require_state_admin admits) means
	statewide -- every system user's login/logout, including state-level actors who
	have no Company User Permission row at all. A company filter narrows to that
	LGA's own scoped staff via get_scoped_user_names."""
	require_state_admin()
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"operation": ["in", ["Login", "Logout"]]}
	if company:
		user_names = get_scoped_user_names(companies=get_requested_companies(company))
		if not user_names:
			return {"items": [], "total": 0, "page": page, "page_size": page_size}
		filters["user"] = ["in", user_names]
	total = frappe.db.count("Activity Log", filters)
	items = frappe.get_all(
		"Activity Log",
		filters=filters,
		fields=["name", "user", "full_name", "operation", "status", "creation", "ip_address"],
		order_by="creation desc",
		start=(page - 1) * page_size,
		page_length=page_size,
	)
	return {"items": items, "total": total, "page": page, "page_size": page_size}


# ---------------------------------------------------------------------------
# System Operations
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_system_health():
	require_system_manager()
	from frappe.utils.scheduler import is_scheduler_inactive

	return {"scheduler_active": not is_scheduler_inactive(verbose=False)}

import frappe

from dtmgp.permissions.scope import get_allowed_companies, is_state_user


def _conditions(doctype, user=None):
	user = user or frappe.session.user
	if is_state_user(user):
		return ""
	companies = get_allowed_companies(user)
	if not companies:
		return "1 = 0"
	values = ", ".join(frappe.db.escape(company) for company in companies)
	return f"`tab{doctype}`.`company` in ({values})"


def has_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	return is_state_user(user) or bool(doc.company and doc.company in get_allowed_companies(user))


def asset_query(user=None): return _conditions("Asset", user)
def asset_movement_query(user=None): return _conditions("Asset Movement", user)
def asset_maintenance_query(user=None): return _conditions("Asset Maintenance", user)
def vehicle_query(user=None): return _conditions("Vehicle", user)
def project_inspection_query(user=None): return _conditions("DTMGP Project Inspection", user)
def asset_verification_query(user=None): return _conditions("DTMGP Asset Verification", user)
def project_proposal_query(user=None): return _conditions("DTMGP Project Proposal", user)
def asset_disposal_query(user=None): return _conditions("DTMGP Asset Disposal", user)
def contractor_document_query(user=None): return _conditions("DTMGP Contractor Document", user)


def asset_maintenance_log_query(user=None):
	"""Asset Maintenance Log has no `company` field of its own; scope through the
	Asset Maintenance record it belongs to, same pattern as Task-via-Project in
	dtmgp.permissions.hr.task_query."""
	user = user or frappe.session.user
	if is_state_user(user):
		return ""
	companies = get_allowed_companies(user)
	if not companies:
		return "1 = 0"
	values = ", ".join(frappe.db.escape(company) for company in companies)
	return f"`tabAsset Maintenance Log`.`asset_maintenance` in (select name from `tabAsset Maintenance` where company in ({values}))"


def asset_maintenance_log_has_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if is_state_user(user):
		return True
	if not doc.asset_maintenance:
		return False
	company = frappe.db.get_value("Asset Maintenance", doc.asset_maintenance, "company")
	return bool(company and company in get_allowed_companies(user))


def vehicle_log_query(user=None):
	"""Vehicle Log has no `company` field of its own; scope through the Vehicle
	(license_plate) it belongs to -- Vehicle's own `company` is a Custom Field added by
	dtmgp.setup.security._ensure_project_custom_fields, same pattern as Task-via-Project."""
	user = user or frappe.session.user
	if is_state_user(user):
		return ""
	companies = get_allowed_companies(user)
	if not companies:
		return "1 = 0"
	values = ", ".join(frappe.db.escape(company) for company in companies)
	return f"`tabVehicle Log`.`license_plate` in (select name from `tabVehicle` where company in ({values}))"


def vehicle_log_has_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if is_state_user(user):
		return True
	if not doc.license_plate:
		return False
	company = frappe.db.get_value("Vehicle", doc.license_plate, "company")
	return bool(company and company in get_allowed_companies(user))

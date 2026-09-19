import frappe
from frappe.utils import cint, nowdate

from dtmgp.permissions.scope import can_manage_governance, get_requested_companies, is_state_user, require_governance_access


RECORD_FIELDS = {
	"DTMGP Correspondence": [
		"company", "correspondence_type", "subject", "correspondent", "department",
		"correspondence_date", "priority", "status", "assigned_to", "due_date", "dispatched_date",
	],
}
EDITABLE_FIELDS = {
	"DTMGP Correspondence": {
		"company", "correspondence_type", "subject", "correspondent", "department",
		"correspondence_date", "priority", "assigned_to", "due_date", "summary", "attachment", "remarks",
	},
}

TRANSITIONS = {
	"DTMGP Correspondence": {
		("Draft", "Registered"): {"LGA Secretary", "LGA Administrator"},
		("Registered", "Dispatched"): {"LGA Secretary", "LGA Administrator"},
		("Registered", "Closed"): {"LGA Secretary", "LGA Administrator"},
		("Dispatched", "Closed"): {"LGA Secretary", "LGA Administrator"},
	},
}


@frappe.whitelist()
def get_dashboard(company=None):
	require_governance_access()
	companies = get_requested_companies(company)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	return {
		"scope": "Statewide" if is_state_user() and not company else (companies[0] if companies else "No LGA assigned"),
		"lga_count": len(companies),
		"can_manage": can_manage_governance(),
		"correspondence": {
			"draft": frappe.db.count("DTMGP Correspondence", filters={**filters, "status": "Draft"}),
			"registered": frappe.db.count("DTMGP Correspondence", filters={**filters, "status": "Registered"}),
			"dispatched": frappe.db.count("DTMGP Correspondence", filters={**filters, "status": "Dispatched"}),
			"overdue_assigned": frappe.db.count("DTMGP Correspondence", filters={**filters, "status": ["not in", ["Closed"]], "due_date": ["<", nowdate()]}),
		},
		"departments": frappe.db.count("Department", filters={**filters, "disabled": 0}) if companies else 0,
	}


@frappe.whitelist()
def get_form_options(company=None):
	require_governance_access()
	companies = get_requested_companies(company)
	selected = companies[0] if len(companies) == 1 else company
	if not selected:
		return {"departments": [], "users": []}
	return {
		"departments": frappe.get_all("Department", filters={"company": selected, "disabled": 0}, pluck="name", order_by="department_name"),
		"users": frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, fields=["name", "full_name"], order_by="full_name"),
	}


@frappe.whitelist()
def list_records(doctype, company=None, search=None, page=1, page_size=25):
	require_governance_access()
	if doctype not in RECORD_FIELDS:
		frappe.throw("Unsupported governance record type", frappe.PermissionError)
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"company": ["in", companies]}
	or_filters = None
	if search and search.strip():
		term = f"%{search.strip()}%"
		search_fields = [field for field in ("subject", "correspondent") if field in RECORD_FIELDS[doctype]]
		or_filters = {field: ["like", term] for field in search_fields} or None
	items = frappe.get_all(
		doctype, filters=filters, or_filters=or_filters, fields=["name", *RECORD_FIELDS[doctype]],
		start=(page - 1) * page_size, page_length=page_size, order_by="modified desc",
	)
	total = frappe.db.count(doctype, filters=filters)
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist(methods=["POST"])
def save_record(doctype, values, name=None):
	require_governance_access(write=True)
	if doctype not in EDITABLE_FIELDS:
		frappe.throw("Unsupported governance record type", frappe.PermissionError)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	if not isinstance(values, dict):
		frappe.throw("Record values must be an object")
	if name:
		doc = frappe.get_doc(doctype, name)
		if doc.company not in get_requested_companies():
			frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	else:
		doc = frappe.new_doc(doctype)
	for field in EDITABLE_FIELDS[doctype]:
		if field in values:
			doc.set(field, values[field])
	doc.save()
	return {"name": doc.name, "doctype": doc.doctype, "status": doc.get("status")}


@frappe.whitelist(methods=["POST"])
def transition_record(doctype, name, target_status):
	require_governance_access(write=True)
	if doctype not in TRANSITIONS:
		frappe.throw("This record does not support workflow transitions", frappe.PermissionError)
	doc = frappe.get_doc(doctype, name)
	if doc.company not in get_requested_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	if (doc.status, target_status) not in TRANSITIONS[doctype]:
		frappe.throw(f"Transition from {doc.status} to {target_status} is not allowed")
	required_roles = TRANSITIONS[doctype][(doc.status, target_status)]
	roles = set(frappe.get_roles())
	if frappe.session.user != "Administrator" and not roles.intersection(required_roles | {"State Administrator"}):
		frappe.throw("Your role cannot perform this workflow transition", frappe.PermissionError)
	if doctype == "DTMGP Correspondence" and target_status == "Dispatched":
		doc.dispatched_date = nowdate()
	doc.status = target_status
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def list_departments(company=None):
	require_governance_access()
	companies = get_requested_companies(company)
	if not companies:
		return []
	return frappe.get_all(
		"Department", filters={"company": ["in", companies]},
		fields=["name", "department_name", "company", "disabled", "is_group", "parent_department"],
		order_by="department_name",
	)


@frappe.whitelist(methods=["POST"])
def save_department(values, name=None):
	require_governance_access(write=True)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	if not isinstance(values, dict):
		frappe.throw("Department values must be an object")
	if name:
		doc = frappe.get_doc("Department", name)
		if doc.company not in get_requested_companies():
			frappe.throw("Department is outside your permitted scope", frappe.PermissionError)
	else:
		company = values.get("company")
		if company not in get_requested_companies(company):
			frappe.throw("LGA is outside your permitted scope", frappe.PermissionError)
		doc = frappe.new_doc("Department")
	for field in ("department_name", "company", "parent_department", "is_group", "disabled"):
		if field in values:
			doc.set(field, values[field])
	doc.save()
	return {"name": doc.name}

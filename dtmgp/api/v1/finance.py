import frappe
from frappe.utils import cint, flt, nowdate

from dtmgp.permissions.scope import can_manage_finance, get_requested_companies, is_state_user, require_finance_access


RECORD_FIELDS = {
	"DTMGP Revenue Head": ["company", "revenue_code", "revenue_name", "rate_type", "default_rate", "disabled"],
	"DTMGP Revenue Assessment": ["company", "revenue_head", "taxpayer_name", "assessment_date", "due_date", "amount", "amount_paid", "status"],
	"DTMGP Revenue Receipt": ["company", "assessment", "posting_date", "amount", "payment_channel", "bank_reference", "docstatus"],
	"DTMGP Procurement Plan": ["company", "fiscal_year", "title", "procurement_category", "procurement_method", "estimated_amount", "status"],
	"DTMGP Procurement Case": ["company", "title", "procurement_plan", "estimated_amount", "status", "recommended_supplier", "evaluated_amount", "purchase_order"],
	"DTMGP Payment Request": ["company", "request_date", "payee", "description", "amount", "status", "payment_entry"],
	"DTMGP Audit Query": ["company", "query_date", "query_type", "severity", "subject", "assigned_to", "response_due_date", "status"],
}
EDITABLE_FIELDS = {
	"DTMGP Revenue Head": {"company", "revenue_code", "revenue_name", "legal_authority", "collection_frequency", "rate_type", "default_rate", "income_account", "valid_from", "valid_to", "disabled"},
	"DTMGP Revenue Assessment": {"company", "revenue_head", "taxpayer_name", "taxpayer_id", "contact", "assessment_date", "due_date", "amount", "notes"},
	"DTMGP Revenue Receipt": {"company", "assessment", "posting_date", "amount", "payment_channel", "bank_reference", "erpnext_payment_entry", "remarks"},
	"DTMGP Procurement Plan": {"company", "fiscal_year", "title", "requesting_department", "procurement_category", "procurement_method", "estimated_amount", "budget_account", "planned_start_date", "planned_end_date", "description"},
	"DTMGP Procurement Case": {"company", "title", "procurement_plan", "material_request", "request_for_quotation", "estimated_amount", "bid_opening_date", "recommended_supplier", "evaluated_amount", "approval_reference", "purchase_order", "contract_end_date", "description"},
	"DTMGP Payment Request": {"company", "request_date", "requesting_department", "payee_type", "payee", "description", "amount", "expense_account", "cost_center", "procurement_case", "purchase_invoice", "approval_reference", "payment_entry", "justification"},
	"DTMGP Audit Query": {"company", "query_date", "query_type", "severity", "reference_doctype", "reference_name", "subject", "finding", "recommendation", "assigned_to", "response_due_date", "management_response", "resolution"},
}

TRANSITIONS = {
	"DTMGP Procurement Plan": {
		("Draft", "Pending Approval"): {"Procurement Officer", "Treasurer"},
		("Pending Approval", "Approved"): None,
		("Pending Approval", "Deferred"): None,
	},
	"DTMGP Procurement Case": {
		("Initiated", "Solicitation"): {"Procurement Officer"},
		("Solicitation", "Bid Opening"): {"Procurement Officer"},
		("Bid Opening", "Evaluation"): {"Procurement Officer"},
		("Evaluation", "Evaluated"): {"Procurement Officer"},
		("Evaluated", "Pending Approval"): {"Procurement Officer"},
		("Pending Approval", "Approved"): None,
		("Pending Approval", "Cancelled"): None,
		("Approved", "Awarded"): {"Procurement Officer"},
		("Awarded", "Completed"): {"Procurement Officer", "Treasurer"},
	},
	"DTMGP Payment Request": {
		("Draft", "Budget Checked"): {"Treasurer"},
		("Budget Checked", "Pending Audit"): {"Treasurer"},
		("Pending Audit", "Pending Approval"): {"Internal Auditor", "State Auditor"},
		("Pending Approval", "Approved"): None,
		("Pending Approval", "Rejected"): None,
		("Approved", "Paid"): {"Treasurer"},
	},
	"DTMGP Audit Query": {
		("Open", "Response Submitted"): {"Treasurer", "Revenue Officer", "Procurement Officer", "LGA Administrator"},
		("Response Submitted", "Under Review"): {"Internal Auditor", "State Auditor"},
		("Under Review", "Resolved"): {"Internal Auditor", "State Auditor"},
		("Resolved", "Closed"): {"Internal Auditor", "State Auditor"},
	},
}


@frappe.whitelist()
def get_dashboard(company=None):
	require_finance_access()
	companies = get_requested_companies(company)
	return {
		"scope": "Statewide" if is_state_user() and not company else (companies[0] if companies else "No LGA assigned"),
		"lga_count": len(companies),
		"revenue": _revenue_summary(companies),
		"procurement": _procurement_summary(companies),
		"payments": _payment_summary(companies),
		"audit": _audit_summary(companies),
		"can_manage": can_manage_finance(),
	}


@frappe.whitelist()
def get_form_options(company=None):
	require_finance_access()
	companies = get_requested_companies(company)
	selected = companies[0] if len(companies) == 1 else company
	if not selected:
		return {"departments": [], "accounts": [], "cost_centers": [], "fiscal_years": [], "revenue_heads": [], "procurement_plans": []}
	return {
		"departments": frappe.get_all("Department", filters={"company": selected, "disabled": 0}, pluck="name", order_by="department_name"),
		"accounts": frappe.get_all("Account", filters={"company": selected, "is_group": 0}, pluck="name", order_by="name"),
		"cost_centers": frappe.get_all("Cost Center", filters={"company": selected, "is_group": 0}, pluck="name", order_by="name"),
		"fiscal_years": frappe.get_all("Fiscal Year", filters={"disabled": 0}, pluck="name", order_by="year_start_date desc"),
		"revenue_heads": frappe.get_all("DTMGP Revenue Head", filters={"company": selected, "disabled": 0}, fields=["name", "revenue_name"], order_by="revenue_name"),
		"procurement_plans": frappe.get_all("DTMGP Procurement Plan", filters={"company": selected, "status": ["not in", ["Deferred", "Cancelled"]]}, fields=["name", "title"], order_by="modified desc"),
	}


@frappe.whitelist()
def list_records(doctype, company=None, search=None, page=1, page_size=25):
	require_finance_access()
	if doctype not in RECORD_FIELDS:
		frappe.throw("Unsupported finance record type", frappe.PermissionError)
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"company": ["in", companies]}
	or_filters = None
	if search and search.strip():
		term = f"%{search.strip()}%"
		search_fields = [field for field in ("title", "subject", "taxpayer_name", "revenue_name", "payee") if field in RECORD_FIELDS[doctype]]
		or_filters = {field: ["like", term] for field in search_fields} or None
	items = frappe.get_all(
		doctype, filters=filters, or_filters=or_filters, fields=["name", *RECORD_FIELDS[doctype]],
		start=(page - 1) * page_size, page_length=page_size, order_by="modified desc",
	)
	total = frappe.db.count(doctype, filters=filters)
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist(methods=["POST"])
def save_record(doctype, values, name=None):
	require_finance_access(write=True)
	if doctype not in EDITABLE_FIELDS:
		frappe.throw("Unsupported finance record type", frappe.PermissionError)
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
	return {"name": doc.name, "doctype": doc.doctype, "status": doc.get("status"), "docstatus": doc.docstatus}


@frappe.whitelist(methods=["POST"])
def submit_record(doctype, name):
	require_finance_access(write=True)
	if doctype not in {"DTMGP Revenue Assessment", "DTMGP Revenue Receipt"}:
		frappe.throw("This record type cannot be submitted through this service", frappe.PermissionError)
	doc = frappe.get_doc(doctype, name)
	if doc.company not in get_requested_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	doc.submit()
	return {"name": doc.name, "docstatus": doc.docstatus, "status": doc.get("status")}


@frappe.whitelist(methods=["POST"])
def transition_record(doctype, name, target_status):
	require_finance_access(write=True)
	if doctype not in TRANSITIONS:
		frappe.throw("This record does not support workflow transitions", frappe.PermissionError)
	doc = frappe.get_doc(doctype, name)
	if doc.company not in get_requested_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	roles = set(frappe.get_roles())
	required_roles = TRANSITIONS[doctype].get((doc.status, target_status))
	if (doc.status, target_status) not in TRANSITIONS[doctype]:
		frappe.throw(f"Transition from {doc.status} to {target_status} is not allowed")
	if required_roles is None:
		_validate_approval_limit(doc, target_status, roles)
	elif frappe.session.user != "Administrator" and not roles.intersection(required_roles | {"State Administrator"}):
		frappe.throw("Your role cannot perform this workflow transition", frappe.PermissionError)
	if doctype == "DTMGP Payment Request" and target_status == "Paid" and not doc.payment_entry:
		frappe.throw("An ERPNext Payment Entry is required before marking a request Paid")
	doc.status = target_status
	doc.save()
	return {"name": doc.name, "status": doc.status}


def _validate_approval_limit(doc, target_status, roles):
	if target_status not in {"Approved", "Rejected", "Deferred", "Cancelled"}:
		return
	if frappe.session.user == "Administrator" or "State Administrator" in roles:
		return
	transaction_type = "Payment Request" if doc.doctype == "DTMGP Payment Request" else ("Procurement Plan" if doc.doctype == "DTMGP Procurement Plan" else "Procurement Award")
	amount = flt(doc.get("amount") or doc.get("estimated_amount"))
	limits = frappe.get_all("DTMGP Approval Limit", filters={"company": doc.company, "transaction_type": transaction_type, "active": 1}, fields=["approving_role", "minimum_amount", "maximum_amount"])
	if not any(limit.approving_role in roles and flt(limit.minimum_amount) <= amount <= flt(limit.maximum_amount) for limit in limits):
		frappe.throw("No active approval limit authorizes your role for this amount", frappe.PermissionError)


def _sum(doctype, field, companies, filters=None):
	if not companies:
		return 0
	conditions = {"company": ["in", companies], **(filters or {})}
	return sum(flt(value) for value in frappe.get_all(doctype, filters=conditions, pluck=field))


def _revenue_summary(companies):
	assessed = _sum("DTMGP Revenue Assessment", "amount", companies, {"docstatus": 1})
	collected = _sum("DTMGP Revenue Receipt", "amount", companies, {"docstatus": 1})
	return {"assessed": assessed, "collected": collected, "outstanding": max(assessed - collected, 0)}


def _procurement_summary(companies):
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	return {
		"planned": frappe.db.count("DTMGP Procurement Plan", filters=filters),
		"active": frappe.db.count("DTMGP Procurement Case", filters={**filters, "status": ["not in", ["Completed", "Cancelled"]]}),
		"pending_approval": frappe.db.count("DTMGP Procurement Case", filters={**filters, "status": "Pending Approval"}),
	}


def _payment_summary(companies):
	return {
		"pending": _sum("DTMGP Payment Request", "amount", companies, {"status": ["in", ["Budget Checked", "Pending Audit", "Pending Approval"]]}),
		"paid": _sum("DTMGP Payment Request", "amount", companies, {"status": "Paid"}),
	}


def _audit_summary(companies):
	filters = {"company": ["in", companies], "status": ["not in", ["Resolved", "Closed"]]} if companies else {"name": ""}
	return {"open_queries": frappe.db.count("DTMGP Audit Query", filters=filters), "overdue_queries": frappe.db.count("DTMGP Audit Query", filters={**filters, "response_due_date": ["<", nowdate()]})}

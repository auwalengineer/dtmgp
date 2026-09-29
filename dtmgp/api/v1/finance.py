import frappe
from frappe.utils import cint, flt, nowdate

from dtmgp.permissions.scope import can_manage_finance, get_requested_companies, is_state_user, require_finance_access


RECORD_FIELDS = {
	"DTMGP Revenue Head": ["company", "revenue_code", "revenue_name", "legal_authority", "rate_type", "default_rate", "approval_status", "disabled"],
	"DTMGP Revenue Assessment": ["company", "revenue_head", "taxpayer_name", "assessment_date", "due_date", "amount", "amount_paid", "status"],
	"DTMGP Revenue Receipt": ["company", "assessment", "posting_date", "amount", "payment_channel", "payment_gateway", "gateway_transaction_id", "gateway_status", "bank_reference", "reconciliation_status", "docstatus"],
	"DTMGP Procurement Plan": ["company", "fiscal_year", "title", "procurement_category", "procurement_method", "estimated_amount", "status"],
	"DTMGP Procurement Case": ["company", "title", "procurement_plan", "estimated_amount", "applicable_threshold", "procurement_committee", "status", "public_notice_url", "recommended_supplier", "evaluated_amount", "purchase_order"],
	"DTMGP Payment Request": ["company", "request_date", "payee", "description", "amount", "status", "payment_entry"],
	"DTMGP Audit Query": ["company", "query_date", "query_type", "severity", "subject", "assigned_to", "response_due_date", "status"],
	"DTMGP Allocation": ["company", "fiscal_year", "tier", "source", "tranche_period", "amount", "expected_date", "received_date", "status"],
	"DTMGP Contract": ["company", "title", "procurement_case", "contractor", "contract_value", "start_date", "end_date", "status", "completion_certificate_reference"],
	"DTMGP Contract Variation": ["company", "contract", "project", "variation_type", "requested_date", "amount_change", "days_change", "status"],
	# Consumed by _validate_approval_limit below but had no CRUD surface anywhere --
	# System Administration's Workflow Setup section is the entry point for it.
	"DTMGP Approval Limit": ["company", "transaction_type", "approving_role", "minimum_amount", "maximum_amount", "active"],
	"DTMGP Finance Control Policy": ["company", "policy_type", "version", "status", "effective_from", "legal_authority", "reconciliation_frequency", "variance_tolerance", "voucher_print_format"],
	"DTMGP Bank Signatory": ["company", "bank_account", "user", "signatory_role", "mandate_group", "valid_from", "valid_to", "status", "approval_reference"],
}
EDITABLE_FIELDS = {
	"DTMGP Revenue Head": {"company", "revenue_code", "revenue_name", "legal_authority", "collection_frequency", "rate_type", "default_rate", "income_account", "valid_from", "valid_to", "approval_status", "disabled"},
	"DTMGP Revenue Assessment": {"company", "revenue_head", "taxpayer_name", "taxpayer_id", "contact", "assessment_date", "due_date", "amount", "enforcement_stage", "last_notice_date", "next_action_date", "enforcement_notes", "notes"},
	"DTMGP Revenue Receipt": {"company", "assessment", "posting_date", "amount", "payment_channel", "payment_gateway", "gateway_transaction_id", "gateway_status", "bank_reference", "erpnext_payment_entry", "reconciliation_status", "remarks"},
	"DTMGP Procurement Plan": {"company", "fiscal_year", "title", "requesting_department", "procurement_category", "procurement_method", "estimated_amount", "budget_account", "planned_start_date", "planned_end_date", "description"},
	"DTMGP Procurement Case": {"company", "title", "procurement_plan", "material_request", "request_for_quotation", "estimated_amount", "applicable_threshold", "procurement_committee", "public_notice_url", "notice_publication_date", "bid_opening_date", "bid_opening_minutes", "bid_evidence", "evaluation_report", "recommended_supplier", "evaluated_amount", "approval_reference", "purchase_order", "contract_end_date", "description"},
	"DTMGP Payment Request": {"company", "request_date", "requesting_department", "payee_type", "payee", "description", "amount", "expense_account", "cost_center", "procurement_case", "purchase_invoice", "approval_reference", "payment_entry", "justification"},
	"DTMGP Audit Query": {"company", "query_date", "query_type", "severity", "reference_doctype", "reference_name", "subject", "finding", "recommendation", "assigned_to", "response_due_date", "management_response", "resolution"},
	"DTMGP Allocation": {"company", "fiscal_year", "tier", "source", "tranche_period", "amount", "expected_date", "received_date", "bank_reference", "distributions", "remarks"},
	"DTMGP Contract": {"company", "title", "procurement_case", "contractor", "contract_value", "start_date", "end_date", "completion_certificate_reference", "milestones", "description"},
	"DTMGP Contract Variation": {"company", "contract", "project", "variation_type", "requested_date", "amount_change", "days_change", "description", "approval_reference"},
	"DTMGP Approval Limit": {"company", "transaction_type", "approving_role", "minimum_amount", "maximum_amount", "active"},
	"DTMGP Finance Control Policy": {"company", "policy_type", "version", "status", "effective_from", "legal_authority", "chart_template", "reconciliation_frequency", "variance_tolerance", "voucher_print_format", "notes"},
	"DTMGP Bank Signatory": {"company", "bank_account", "user", "signatory_role", "mandate_group", "valid_from", "valid_to", "status", "approval_reference"},
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
	"DTMGP Allocation": {
		("Expected", "Received"): {"Treasurer"},
		("Received", "Distributed"): {"Treasurer"},
	},
	"DTMGP Contract": {
		("Draft", "Active"): {"Procurement Officer", "Treasurer"},
		("Active", "Suspended"): {"Procurement Officer", "Treasurer"},
		("Suspended", "Active"): {"Procurement Officer", "Treasurer"},
		("Active", "Completed"): {"Procurement Officer", "Treasurer"},
		("Active", "Terminated"): {"Procurement Officer", "Treasurer"},
		("Suspended", "Terminated"): {"Procurement Officer", "Treasurer"},
	},
	"DTMGP Contract Variation": {
		("Draft", "Pending Approval"): {"Procurement Officer", "Treasurer"},
		("Pending Approval", "Approved"): None,
		("Pending Approval", "Rejected"): None,
	},
}

TRANSACTION_TYPE_BY_DOCTYPE = {
	"DTMGP Payment Request": "Payment Request",
	"DTMGP Procurement Plan": "Procurement Plan",
	"DTMGP Procurement Case": "Procurement Award",
	"DTMGP Contract Variation": "Contract Variation",
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
	transaction_type = TRANSACTION_TYPE_BY_DOCTYPE.get(doc.doctype, "Procurement Award")
	amount = flt(doc.get("amount") or doc.get("estimated_amount"))
	if not amount and doc.doctype == "DTMGP Contract Variation":
		amount = abs(flt(doc.get("amount_change")))
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


def _selected_company(company, companies):
	return companies[0] if len(companies) == 1 else (company if company in companies else None)


@frappe.whitelist()
def list_allocations(company=None):
	require_finance_access()
	companies = get_requested_companies(company)
	if not companies:
		return {"items": []}
	allocations = frappe.get_all(
		"DTMGP Allocation", filters={"company": ["in", companies]},
		fields=["name", "company", "fiscal_year", "tier", "source", "tranche_period", "amount", "expected_date", "received_date", "bank_reference", "status"],
		order_by="modified desc",
	)
	if allocations:
		totals = frappe.db.sql(
			"""select parent, coalesce(sum(amount), 0) as total from `tabDTMGP Allocation Distribution`
			where parent in %(names)s group by parent""",
			{"names": [allocation.name for allocation in allocations]}, as_dict=True,
		)
		totals_by_name = {row.parent: row.total for row in totals}
		for allocation in allocations:
			allocation["distributed_total"] = flt(totals_by_name.get(allocation.name))
	return {"items": allocations}


@frappe.whitelist()
def get_allocation_distributions(company=None):
	require_finance_access()
	companies = get_requested_companies(company)
	if not companies:
		return {"items": []}
	return {"items": frappe.db.sql(
		"""select d.name, d.parent as allocation, d.department, d.purpose, d.amount, a.company, a.status
		from `tabDTMGP Allocation Distribution` d
		join `tabDTMGP Allocation` a on a.name = d.parent
		where a.company in %(companies)s
		order by d.modified desc""",
		{"companies": companies}, as_dict=True,
	)}


@frappe.whitelist()
def get_contract_milestones(company=None):
	require_finance_access()
	companies = get_requested_companies(company)
	if not companies:
		return {"items": []}
	return {"items": frappe.db.sql(
		"""select m.name, m.parent as contract, m.title, m.due_date, m.amount, m.status, m.certified_date, m.payment_request, c.company
		from `tabDTMGP Contract Milestone` m
		join `tabDTMGP Contract` c on c.name = m.parent
		where c.company in %(companies)s
		order by m.idx""",
		{"companies": companies}, as_dict=True,
	)}


@frappe.whitelist()
def get_accounts_tree(company=None):
	require_finance_access()
	companies = get_requested_companies(company)
	selected = _selected_company(company, companies)
	if not selected:
		return {"items": []}
	return {"items": frappe.get_all(
		"Account", filters={"company": selected},
		fields=["name", "account_name", "parent_account", "is_group", "root_type", "account_type"],
		order_by="lft",
	)}


@frappe.whitelist()
def list_journal_entries(company=None, page=1, page_size=25):
	require_finance_access()
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	if not companies:
		return {"items": [], "total": 0, "page": page, "page_size": page_size}
	filters = {"company": ["in", companies], "docstatus": 1}
	items = frappe.get_all(
		"Journal Entry", filters=filters,
		fields=["name", "posting_date", "voucher_type", "company", "total_debit", "user_remark"],
		order_by="posting_date desc", start=(page - 1) * page_size, page_length=page_size,
	)
	return {"items": items, "total": frappe.db.count("Journal Entry", filters=filters), "page": page, "page_size": page_size}


@frappe.whitelist()
def list_gl_entries(company=None, account=None, from_date=None, to_date=None, page=1, page_size=50):
	require_finance_access()
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 200)
	if not companies:
		return {"items": [], "total": 0, "page": page, "page_size": page_size}
	filters = [["company", "in", companies], ["is_cancelled", "=", 0]]
	if account:
		filters.append(["account", "=", account])
	if from_date:
		filters.append(["posting_date", ">=", from_date])
	if to_date:
		filters.append(["posting_date", "<=", to_date])
	items = frappe.get_all(
		"GL Entry", filters=filters,
		fields=["name", "posting_date", "account", "debit", "credit", "against", "voucher_type", "voucher_no", "company"],
		order_by="posting_date desc", start=(page - 1) * page_size, page_length=page_size,
	)
	return {"items": items, "total": frappe.db.count("GL Entry", filters=filters), "page": page, "page_size": page_size}


@frappe.whitelist()
def get_trial_balance(company=None, fiscal_year=None):
	require_finance_access()
	companies = get_requested_companies(company)
	selected = _selected_company(company, companies)
	if not selected:
		return {"rows": [], "total_debit": 0, "total_credit": 0}
	conditions = "ge.company=%(company)s and ge.is_cancelled=0"
	values = {"company": selected}
	if fiscal_year:
		year = frappe.db.get_value("Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
		if year:
			conditions += " and ge.posting_date between %(start)s and %(end)s"
			values.update({"start": year.year_start_date, "end": year.year_end_date})
	rows = frappe.db.sql(
		f"""select ge.account, acc.root_type, sum(ge.debit) as debit, sum(ge.credit) as credit
		from `tabGL Entry` ge join `tabAccount` acc on acc.name = ge.account
		where {conditions} group by ge.account order by ge.account""",
		values, as_dict=True,
	)
	return {"rows": rows, "total_debit": sum(flt(row.debit) for row in rows), "total_credit": sum(flt(row.credit) for row in rows)}


@frappe.whitelist()
def get_receivables_payables(company=None):
	"""Operational subledgers for DTMGP's non-invoice model. Receivables are lawful
	revenue assessments; payables are approved/unpaid expenditure requests."""
	require_finance_access()
	companies = get_requested_companies(company)
	receivables = frappe.get_all(
		"DTMGP Revenue Assessment", filters={"company": ["in", companies], "docstatus": 1, "status": ["in", ["Unpaid", "Part Paid"]]},
		fields=["name", "company", "taxpayer_name as party", "due_date", "amount", "amount_paid", "status"], order_by="due_date asc", limit_page_length=500,
	)
	for row in receivables:
		row.outstanding = flt(row.amount) - flt(row.amount_paid)
	payables = frappe.get_all(
		"DTMGP Payment Request", filters={"company": ["in", companies], "status": ["in", ["Pending Approval", "Approved"]]},
		fields=["name", "company", "payee as party", "request_date as due_date", "amount", "status", "payment_entry"], order_by="request_date asc", limit_page_length=500,
	)
	return {"receivables": receivables, "payables": payables}


@frappe.whitelist()
def get_banking_setup(company=None):
	require_finance_access()
	companies = get_requested_companies(company)
	accounts = frappe.get_all("Bank Account", filters={"company": ["in", companies]}, fields=["name", "account_name", "bank", "company", "is_default", "is_company_account", "disabled"], order_by="account_name")
	transactions = frappe.get_all("Bank Transaction", filters={"company": ["in", companies], "docstatus": 1}, fields=["name", "bank_account", "date", "deposit", "withdrawal", "status", "unallocated_amount"], order_by="date desc", limit_page_length=200)
	signatories = frappe.get_all("DTMGP Bank Signatory", filters={"company": ["in", companies]}, fields=RECORD_FIELDS["DTMGP Bank Signatory"], order_by="modified desc")
	formats = frappe.get_all("Print Format", filters={"doc_type": ["in", ["Journal Entry", "Payment Entry", "DTMGP Payment Request"]], "disabled": 0}, fields=["name", "doc_type", "standard"], order_by="doc_type, name")
	return {"accounts": accounts, "transactions": transactions, "signatories": signatories, "voucher_print_formats": formats}


@frappe.whitelist()
def get_cash_flow(company=None, fiscal_year=None):
	require_finance_access()
	companies = get_requested_companies(company)
	selected = _selected_company(company, companies)
	if not selected:
		return {"inflow": 0, "outflow": 0, "net": 0}
	inflow_extra, outflow_extra = {}, {}
	if fiscal_year:
		year = frappe.db.get_value("Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
		if year:
			inflow_extra["posting_date"] = ["between", [year.year_start_date, year.year_end_date]]
			outflow_extra["request_date"] = ["between", [year.year_start_date, year.year_end_date]]
	inflow = _sum("DTMGP Revenue Receipt", "amount", [selected], {"docstatus": 1, **inflow_extra})
	outflow = _sum("DTMGP Payment Request", "amount", [selected], {"status": "Paid", **outflow_extra})
	return {"inflow": inflow, "outflow": outflow, "net": inflow - outflow}


@frappe.whitelist()
def get_budget_performance(company=None, fiscal_year=None):
	require_finance_access()
	companies = get_requested_companies(company)
	selected = _selected_company(company, companies)
	if not selected or not fiscal_year:
		return {"rows": []}
	budget_names = frappe.get_all("Budget", filters={"company": selected, "fiscal_year": fiscal_year, "docstatus": 1}, pluck="name")
	if not budget_names:
		return {"rows": []}
	budget_rows = frappe.get_all("Budget Account", filters={"parent": ["in", budget_names]}, fields=["account", "budget_amount"])
	budget_by_account = {}
	for row in budget_rows:
		budget_by_account[row.account] = budget_by_account.get(row.account, 0) + flt(row.budget_amount)
	year = frappe.db.get_value("Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
	actuals = frappe.db.sql(
		"""select account, sum(debit) - sum(credit) as actual from `tabGL Entry`
		where company=%(company)s and is_cancelled=0 and posting_date between %(start)s and %(end)s
		and account in %(accounts)s group by account""",
		{"company": selected, "start": year.year_start_date, "end": year.year_end_date, "accounts": list(budget_by_account) or [""]},
		as_dict=True,
	) if year else []
	actual_by_account = {row.account: flt(row.actual) for row in actuals}
	rows = [
		{"account": account, "budget": amount, "actual": actual_by_account.get(account, 0), "variance": amount - actual_by_account.get(account, 0)}
		for account, amount in budget_by_account.items()
	]
	return {"rows": rows}


@frappe.whitelist()
def list_purchase_receipts(company=None):
	require_finance_access()
	companies = get_requested_companies(company)
	if not companies:
		return {"items": []}
	return {"items": frappe.get_all(
		"Purchase Receipt", filters={"company": ["in", companies], "docstatus": 1},
		fields=["name", "posting_date", "supplier", "grand_total", "status"],
		order_by="posting_date desc",
	)}


@frappe.whitelist()
def list_budgets(company=None, fiscal_year=None):
	require_finance_access()
	companies = get_requested_companies(company)
	if not companies:
		return {"items": []}
	filters = {"company": ["in", companies]}
	if fiscal_year:
		filters["fiscal_year"] = fiscal_year
	budgets = frappe.get_all(
		"Budget", filters=filters,
		fields=["name", "company", "fiscal_year", "budget_against", "cost_center", "project", "docstatus", "amended_from"],
		order_by="modified desc",
	)
	if budgets:
		totals = frappe.db.sql(
			"""select parent, coalesce(sum(budget_amount), 0) as total from `tabBudget Account`
			where parent in %(names)s group by parent""",
			{"names": [budget.name for budget in budgets]}, as_dict=True,
		)
		totals_by_name = {row.parent: row.total for row in totals}
		for budget in budgets:
			budget["total_budget"] = flt(totals_by_name.get(budget.name))
	return {"items": budgets}


@frappe.whitelist(methods=["POST"])
def save_budget(company, fiscal_year, budget_against, cost_center=None, project=None, accounts=None, name=None):
	require_finance_access(write=True)
	if company not in get_requested_companies(company):
		frappe.throw("LGA is outside your permitted scope", frappe.PermissionError)
	accounts = frappe.parse_json(accounts) if isinstance(accounts, str) else (accounts or [])
	if name:
		doc = frappe.get_doc("Budget", name)
		if doc.company not in get_requested_companies():
			frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
		if doc.docstatus == 1:
			frappe.throw("A submitted budget cannot be edited directly -- cancel and amend it instead")
	else:
		doc = frappe.new_doc("Budget")
	doc.company = company
	doc.fiscal_year = fiscal_year
	doc.budget_against = budget_against
	doc.cost_center = cost_center
	doc.project = project
	doc.set("accounts", [{"account": row.get("account"), "budget_amount": row.get("budget_amount")} for row in accounts])
	doc.save()
	return {"name": doc.name, "docstatus": doc.docstatus}


@frappe.whitelist(methods=["POST"])
def submit_budget(name):
	require_finance_access(write=True)
	doc = frappe.get_doc("Budget", name)
	if doc.company not in get_requested_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	doc.submit()
	return {"name": doc.name, "docstatus": doc.docstatus}


@frappe.whitelist(methods=["POST"])
def cancel_budget(name):
	require_finance_access(write=True)
	doc = frappe.get_doc("Budget", name)
	if doc.company not in get_requested_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	doc.cancel()
	return {"name": doc.name, "docstatus": doc.docstatus}


@frappe.whitelist(methods=["POST"])
def amend_budget(name):
	require_finance_access(write=True)
	source = frappe.get_doc("Budget", name)
	if source.company not in get_requested_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	if source.docstatus != 2:
		frappe.throw("Only a cancelled budget can be amended")
	amended = frappe.copy_doc(source)
	amended.amended_from = source.name
	amended.docstatus = 0
	amended.insert()
	return {"name": amended.name, "docstatus": amended.docstatus}

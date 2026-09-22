import frappe
from frappe.utils import cint, nowdate

from dtmgp.permissions.scope import can_manage_governance, get_requested_companies, is_state_user, require_governance_access
from dtmgp.setup.security import PLATFORM_ROLES


RECORD_FIELDS = {
	"DTMGP Correspondence": [
		"company", "correspondence_type", "subject", "correspondent", "department",
		"correspondence_date", "priority", "status", "assigned_to", "due_date", "dispatched_date",
	],
	"DTMGP Meeting": ["company", "meeting_type", "title", "meeting_date", "venue", "chairperson", "status", "minutes_finalized"],
	"DTMGP Resolution": ["company", "meeting", "title", "category", "status", "adopted_date"],
	"DTMGP Resolution Action": ["company", "resolution", "action_description", "responsible_department", "assigned_to", "due_date", "status", "completed_date"],
	"DTMGP Statutory Return": ["company", "return_type", "period", "due_date", "status", "prepared_by", "submitted_date"],
	"DTMGP Compliance Submission": ["company", "requirement", "period", "due_date", "status", "submitted_date", "verified_by"],
	"DTMGP Approval Delegation": ["company", "delegator", "delegate", "role", "start_date", "end_date", "active"],
}
EDITABLE_FIELDS = {
	"DTMGP Correspondence": {
		"company", "correspondence_type", "subject", "correspondent", "department",
		"correspondence_date", "priority", "assigned_to", "due_date", "summary", "attachment", "remarks",
	},
	"DTMGP Meeting": {"company", "meeting_type", "title", "meeting_date", "venue", "chairperson", "convened_by", "agenda_items", "attendees", "minutes", "minutes_finalized"},
	"DTMGP Resolution": {"company", "meeting", "title", "category", "resolution_text"},
	"DTMGP Resolution Action": {"company", "resolution", "action_description", "responsible_department", "assigned_to", "due_date", "remarks"},
	"DTMGP Statutory Return": {"company", "return_type", "period", "due_date", "prepared_by", "attachment"},
	"DTMGP Compliance Submission": {"company", "requirement", "period", "due_date", "evidence", "verified_by", "verification_notes"},
	"DTMGP Approval Delegation": {"company", "delegator", "delegate", "role", "start_date", "end_date", "active"},
}

TRANSITIONS = {
	"DTMGP Correspondence": {
		("Draft", "Registered"): {"LGA Secretary", "LGA Administrator"},
		("Registered", "Dispatched"): {"LGA Secretary", "LGA Administrator"},
		("Registered", "Closed"): {"LGA Secretary", "LGA Administrator"},
		("Dispatched", "Closed"): {"LGA Secretary", "LGA Administrator"},
	},
	"DTMGP Meeting": {
		("Scheduled", "Held"): {"LGA Secretary", "LGA Administrator"},
		("Scheduled", "Postponed"): {"LGA Secretary", "LGA Administrator"},
		("Scheduled", "Cancelled"): {"LGA Secretary", "LGA Administrator"},
		("Postponed", "Scheduled"): {"LGA Secretary", "LGA Administrator"},
	},
	"DTMGP Resolution": {
		("Proposed", "Adopted"): {"LGA Chairman", "LGA Administrator"},
		("Proposed", "Rejected"): {"LGA Chairman", "LGA Administrator"},
		("Adopted", "Rescinded"): {"LGA Chairman", "LGA Administrator"},
	},
	"DTMGP Resolution Action": {
		("Pending", "In Progress"): {"LGA Secretary", "LGA Administrator"},
		("In Progress", "Completed"): {"LGA Secretary", "LGA Administrator"},
		("Pending", "Completed"): {"LGA Secretary", "LGA Administrator"},
	},
	"DTMGP Statutory Return": {
		("Draft", "Prepared"): {"LGA Secretary", "Treasurer", "LGA Administrator"},
		("Prepared", "Submitted"): {"LGA Secretary", "LGA Administrator"},
		("Submitted", "State Reviewed"): {"State Auditor"},
		("Submitted", "Returned"): {"State Auditor"},
		("Returned", "Prepared"): {"LGA Secretary", "LGA Administrator"},
	},
	"DTMGP Compliance Submission": {
		("Pending", "Submitted"): {"LGA Secretary", "LGA Administrator"},
		("Submitted", "Verified"): {"Internal Auditor", "State Auditor"},
		("Submitted", "Non-Compliant"): {"Internal Auditor", "State Auditor"},
	},
}

# Doctype -> (display field, status awaiting the caller's decision) for the
# cross-cutting Approvals inbox. Not a separate transactional record type (see
# docs/implementation-status.md Governance backlog) — it reads the same status
# fields TRANSITIONS already governs.
APPROVAL_SOURCES = {
	"DTMGP Resolution": ("title", "Proposed"),
	"DTMGP Statutory Return": ("period", "Submitted"),
	"DTMGP Compliance Submission": ("period", "Submitted"),
}


def _effective_roles(company):
	"""The caller's own roles, plus any role delegated to them for this LGA via an
	active DTMGP Approval Delegation. Used for governance workflow transitions and
	the approvals inbox so a delegate can act while the delegator is unavailable."""
	roles = set(frappe.get_roles())
	if frappe.session.user == "Administrator" or not company:
		return roles
	delegated = frappe.get_all(
		"DTMGP Approval Delegation",
		filters={"company": company, "delegate": frappe.session.user, "active": 1, "start_date": ["<=", nowdate()], "end_date": [">=", nowdate()]},
		pluck="role",
	)
	return roles | set(delegated)


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
		"meetings_scheduled": frappe.db.count("DTMGP Meeting", filters={**filters, "status": "Scheduled"}),
		"resolutions_proposed": frappe.db.count("DTMGP Resolution", filters={**filters, "status": "Proposed"}),
		"actions_overdue": frappe.db.count("DTMGP Resolution Action", filters={**filters, "status": ["!=", "Completed"], "due_date": ["<", nowdate()]}),
		"returns_overdue": frappe.db.count("DTMGP Statutory Return", filters={**filters, "status": ["not in", ["Submitted", "State Reviewed"]], "due_date": ["<", nowdate()]}),
		"compliance_non_compliant": frappe.db.count("DTMGP Compliance Submission", filters={**filters, "status": "Non-Compliant"}),
		"pending_approvals": len(get_approvals_inbox(company)) if companies else 0,
	}


@frappe.whitelist()
def get_reports(company=None):
	require_governance_access()
	companies = get_requested_companies(company)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	return {
		"meetings": {
			"scheduled": frappe.db.count("DTMGP Meeting", {**filters, "status": "Scheduled"}),
			"held": frappe.db.count("DTMGP Meeting", {**filters, "status": "Held"}),
			"cancelled": frappe.db.count("DTMGP Meeting", {**filters, "status": "Cancelled"}),
			"postponed": frappe.db.count("DTMGP Meeting", {**filters, "status": "Postponed"}),
		},
		"resolutions": {
			"proposed": frappe.db.count("DTMGP Resolution", {**filters, "status": "Proposed"}),
			"adopted": frappe.db.count("DTMGP Resolution", {**filters, "status": "Adopted"}),
			"rejected": frappe.db.count("DTMGP Resolution", {**filters, "status": "Rejected"}),
		},
		"resolution_actions": {
			"pending": frappe.db.count("DTMGP Resolution Action", {**filters, "status": ["!=", "Completed"]}),
			"completed": frappe.db.count("DTMGP Resolution Action", {**filters, "status": "Completed"}),
			"overdue": frappe.db.count("DTMGP Resolution Action", {**filters, "status": ["!=", "Completed"], "due_date": ["<", nowdate()]}),
		},
		"statutory_returns": {
			"submitted": frappe.db.count("DTMGP Statutory Return", {**filters, "status": ["in", ["Submitted", "State Reviewed"]]}),
			"overdue": frappe.db.count("DTMGP Statutory Return", {**filters, "status": ["not in", ["Submitted", "State Reviewed"]], "due_date": ["<", nowdate()]}),
		},
		"compliance": {
			"verified": frappe.db.count("DTMGP Compliance Submission", {**filters, "status": "Verified"}),
			"non_compliant": frappe.db.count("DTMGP Compliance Submission", {**filters, "status": "Non-Compliant"}),
			"pending": frappe.db.count("DTMGP Compliance Submission", {**filters, "status": "Pending"}),
		},
	}


@frappe.whitelist()
def get_approvals_inbox(company=None):
	require_governance_access()
	companies = get_requested_companies(company)
	if not companies:
		return []
	is_admin = frappe.session.user == "Administrator"
	inbox = []
	for doctype, (title_field, pending_status) in APPROVAL_SOURCES.items():
		outgoing_roles = set()
		for (from_status, _to_status), required in TRANSITIONS[doctype].items():
			if from_status == pending_status and required:
				outgoing_roles |= required
		records = frappe.get_all(
			doctype, filters={"company": ["in", companies], "status": pending_status},
			fields=["name", "company", title_field, "status", "modified"], order_by="modified desc",
		)
		for record in records:
			if is_admin or (outgoing_roles & _effective_roles(record.company)):
				inbox.append({"doctype": doctype, "name": record.name, "title": record.get(title_field), "company": record.company, "status": record.status})
	return inbox


@frappe.whitelist()
def get_form_options(company=None):
	require_governance_access()
	companies = get_requested_companies(company)
	selected = companies[0] if len(companies) == 1 else company
	if not selected:
		return {"departments": [], "users": [], "meetings": [], "resolutions": [], "return_types": [], "compliance_requirements": [], "roles": []}
	return {
		"departments": frappe.get_all("Department", filters={"company": selected, "disabled": 0}, pluck="name", order_by="department_name"),
		"users": frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, fields=["name", "full_name"], order_by="full_name"),
		"meetings": frappe.get_all("DTMGP Meeting", filters={"company": selected}, fields=["name", "title", "meeting_date"], order_by="meeting_date desc", page_length=50),
		"resolutions": frappe.get_all("DTMGP Resolution", filters={"company": selected, "status": ["in", ["Proposed", "Adopted"]]}, fields=["name", "title"], order_by="modified desc", page_length=50),
		"return_types": frappe.get_all("DTMGP Statutory Return Type", filters={"disabled": 0}, fields=["name", "return_name", "frequency"], order_by="return_name"),
		"compliance_requirements": frappe.get_all("DTMGP Compliance Requirement", filters={"disabled": 0}, fields=["name", "requirement_name", "frequency"], order_by="requirement_name"),
		"roles": frappe.get_all("Role", filters={"name": ["in", list(PLATFORM_ROLES)]}, pluck="name", order_by="name"),
	}


@frappe.whitelist()
def list_records(doctype, company=None, search=None, page=1, page_size=25, correspondence_type=None, status=None, assigned_to=None):
	require_governance_access()
	if doctype not in RECORD_FIELDS:
		frappe.throw("Unsupported governance record type", frappe.PermissionError)
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"company": ["in", companies]}
	if correspondence_type and "correspondence_type" in RECORD_FIELDS[doctype]:
		filters["correspondence_type"] = correspondence_type
	if status and "status" in RECORD_FIELDS[doctype]:
		filters["status"] = status
	if assigned_to and "assigned_to" in RECORD_FIELDS[doctype]:
		filters["assigned_to"] = assigned_to
	or_filters = None
	if search and search.strip():
		term = f"%{search.strip()}%"
		search_fields = [field for field in ("subject", "correspondent", "title", "action_description", "period") if field in RECORD_FIELDS[doctype]]
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
	# View access is enough to enter here: the exact required_roles intersection
	# check below (plus each doctype's own DocPerm write=1) governs who can actually
	# perform a given transition — e.g. State Auditor/Internal Auditor can review a
	# Statutory Return or Compliance Submission without being a general record
	# manager (GOVERNANCE_MANAGE_ROLES), matching how they're granted write only on
	# those two doctypes' JSON permissions and nothing else in the module.
	require_governance_access()
	if doctype not in TRANSITIONS:
		frappe.throw("This record does not support workflow transitions", frappe.PermissionError)
	doc = frappe.get_doc(doctype, name)
	if doc.company not in get_requested_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	if (doc.status, target_status) not in TRANSITIONS[doctype]:
		frappe.throw(f"Transition from {doc.status} to {target_status} is not allowed")
	required_roles = TRANSITIONS[doctype][(doc.status, target_status)]
	roles = _effective_roles(doc.company)
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

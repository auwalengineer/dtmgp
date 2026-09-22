import frappe
from frappe.utils import cint

from dtmgp.permissions.scope import can_manage_traditional, get_requested_companies, require_traditional_access


RECORD_FIELDS = {
	"DTMGP Traditional Institution": ["company", "institution_name", "institution_type", "rank_class", "parent_institution", "seat_location", "status"],
	"DTMGP Traditional Ruler": ["company", "ruler_name", "institution", "ruling_house", "appointment_date", "installation_date", "status", "reign_end_date"],
	"DTMGP Ruling House": ["company", "house_name", "institution", "rotation_order", "is_eligible", "last_occupied_from"],
	"DTMGP Traditional Appointment": ["company", "institution", "candidate_name", "ruling_house", "application_date", "status", "gazette_reference", "gazette_date", "installation_date", "recognition_status"],
	"DTMGP Succession Case": ["company", "institution", "vacancy_date", "vacancy_reason", "status", "eligible_ruling_house", "candidates", "selected_candidate", "resulting_appointment"],
	"DTMGP Chieftaincy Petition": ["company", "institution", "respondent_institution", "petitioner_name", "petition_type", "petition_date", "status", "hearing_date", "decision", "decision_date"],
	"DTMGP Traditional Allowance": ["company", "ruler", "allowance_type", "amount", "period_start", "period_end", "status", "payment_date"],
}
EDITABLE_FIELDS = {
	"DTMGP Traditional Institution": {"company", "institution_name", "institution_type", "rank_class", "parent_institution", "seat_location", "founding_basis", "history", "status"},
	"DTMGP Traditional Ruler": {"company", "ruler_name", "institution", "ruling_house", "gender", "date_of_birth", "appointment_date", "installation_date", "gazette_reference", "status", "reign_end_date", "reign_end_reason"},
	"DTMGP Ruling House": {"company", "house_name", "institution", "rotation_order", "is_eligible", "last_occupied_from", "notes"},
	"DTMGP Traditional Appointment": {"company", "institution", "candidate_name", "ruling_house", "application_date", "gazette_reference", "gazette_date", "certificate_number"},
	"DTMGP Succession Case": {"company", "institution", "vacancy_date", "vacancy_reason", "eligible_ruling_house", "candidates", "selected_candidate", "resulting_appointment"},
	"DTMGP Chieftaincy Petition": {"company", "institution", "respondent_institution", "petitioner_name", "petition_type", "petition_date", "description", "panel_reference", "decision", "litigation_reference", "appeal_outcome"},
	"DTMGP Traditional Allowance": {"company", "ruler", "allowance_type", "amount", "period_start", "period_end", "payment_reference"},
}
TRANSITIONS = {
	"DTMGP Traditional Appointment": [
		"Nominated", "Kingmakers Selection", "Council Endorsed", "Ministry Vetting",
		"Exco Approved", "Governor Approved", "Gazetted", "Installed",
	],
	"DTMGP Succession Case": ["Open", "Candidates Nominated", "Kingmakers Deliberation", "Selected", "Closed"],
	"DTMGP Chieftaincy Petition": ["Filed", "Council Hearing", "Panel of Inquiry", "Exco Review", "Decided", "Appealed", "Closed"],
	"DTMGP Traditional Allowance": ["Draft", "Approved", "Paid"],
}
TRANSITION_DATE_FIELDS = {
	"DTMGP Traditional Appointment": {
		"Kingmakers Selection": "kingmakers_selection_date", "Council Endorsed": "council_endorsement_date",
		"Ministry Vetting": "ministry_vetting_date", "Exco Approved": "exco_approval_date",
		"Governor Approved": "governor_approval_date", "Installed": "installation_date",
	},
	"DTMGP Chieftaincy Petition": {"Council Hearing": "hearing_date", "Decided": "decision_date", "Appealed": "appeal_date"},
	"DTMGP Traditional Allowance": {"Paid": "payment_date"},
	"DTMGP Succession Case": {"Closed": "closed_date"},
}


@frappe.whitelist()
def get_dashboard(company=None):
	require_traditional_access()
	companies = get_requested_companies(company)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	return {
		"active_institutions": frappe.db.count("DTMGP Traditional Institution", filters={**filters, "status": "Active"}),
		"reigning_rulers": frappe.db.count("DTMGP Traditional Ruler", filters={**filters, "status": "Reigning"}),
		"vacant_stools": _vacant_stool_count(companies),
		"pending_recognition": frappe.db.count("DTMGP Traditional Appointment", filters={**filters, "status": ["!=", "Installed"]}),
		"open_petitions": frappe.db.count("DTMGP Chieftaincy Petition", filters={**filters, "status": ["not in", ["Decided", "Closed"]]}),
		"can_manage": can_manage_traditional(),
	}


def _vacant_stool_count(companies):
	if not companies:
		return 0
	active = frappe.get_all("DTMGP Traditional Institution", filters={"company": ["in", companies], "status": "Active"}, pluck="name")
	if not active:
		return 0
	reigning = set(frappe.get_all("DTMGP Traditional Ruler", filters={"institution": ["in", active], "status": "Reigning"}, pluck="institution"))
	return len([institution for institution in active if institution not in reigning])


@frappe.whitelist()
def get_form_options(company=None):
	require_traditional_access()
	companies = get_requested_companies(company)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	return {
		"institutions": frappe.get_all("DTMGP Traditional Institution", filters=filters, fields=["name", "institution_name"], order_by="institution_name asc"),
		"ruling_houses": frappe.get_all("DTMGP Ruling House", filters=filters, fields=["name", "house_name", "institution"], order_by="house_name asc"),
		"rulers": frappe.get_all("DTMGP Traditional Ruler", filters={**filters, "status": "Reigning"}, fields=["name", "ruler_name"], order_by="ruler_name asc"),
	}


@frappe.whitelist()
def list_records(doctype, company=None, search=None, status=None, page=1, page_size=25):
	require_traditional_access()
	if doctype not in RECORD_FIELDS:
		frappe.throw("Unsupported traditional affairs record type", frappe.PermissionError)
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"company": ["in", companies]}
	if status:
		filters["status"] = status
	or_filters = None
	if search and search.strip():
		term = f"%{search.strip()}%"
		search_fields = [field for field in ("institution_name", "ruler_name", "house_name", "candidate_name", "petitioner_name") if field in RECORD_FIELDS[doctype]]
		or_filters = {field: ["like", term] for field in search_fields} or None
	items = frappe.get_all(
		doctype, filters=filters, or_filters=or_filters, fields=["name", *RECORD_FIELDS[doctype]],
		start=(page - 1) * page_size, page_length=page_size, order_by="modified desc",
	)
	total = frappe.db.count(doctype, filters=filters)
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist(methods=["POST"])
def save_record(doctype, values, name=None):
	require_traditional_access(write=True)
	if doctype not in EDITABLE_FIELDS:
		frappe.throw("Unsupported traditional affairs record type", frappe.PermissionError)
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
	require_traditional_access(write=True)
	if doctype not in TRANSITIONS:
		frappe.throw("This record does not support workflow transitions", frappe.PermissionError)
	doc = frappe.get_doc(doctype, name)
	if doc.company not in get_requested_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	chain = TRANSITIONS[doctype]
	if doc.status not in chain or target_status not in chain or chain.index(target_status) != chain.index(doc.status) + 1:
		frappe.throw(f"Transition from {doc.status} to {target_status} is not allowed")
	date_field = TRANSITION_DATE_FIELDS.get(doctype, {}).get(target_status)
	if date_field and not doc.get(date_field):
		doc.set(date_field, frappe.utils.nowdate())
	doc.status = target_status
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def update_recognition(name, recognition_status, reason=None):
	require_traditional_access(write=True)
	doc = frappe.get_doc("DTMGP Traditional Appointment", name)
	if doc.company not in get_requested_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	if recognition_status == "Suspended":
		doc.suspension_reason = reason or ""
	elif recognition_status == "Withdrawn":
		doc.withdrawal_reason = reason or ""
	doc.recognition_status = recognition_status
	doc.save()
	return {"name": doc.name, "recognition_status": doc.recognition_status}


@frappe.whitelist()
def list_petition_documents(petition):
	require_traditional_access()
	doc = frappe.get_doc("DTMGP Chieftaincy Petition", petition)
	if doc.company not in get_requested_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	return frappe.get_all(
		"File", filters={"attached_to_doctype": "DTMGP Chieftaincy Petition", "attached_to_name": petition},
		fields=["name", "file_name", "file_url", "is_private", "creation"], order_by="creation desc",
	)


@frappe.whitelist()
def get_traditional_reports(company=None):
	require_traditional_access()
	companies = get_requested_companies(company)
	return {
		"institutions_by_type": _group_count("DTMGP Traditional Institution", "institution_type", companies),
		"rulers_by_status": _group_count("DTMGP Traditional Ruler", "status", companies),
		"appointments_by_stage": _group_count("DTMGP Traditional Appointment", "status", companies),
		"succession_by_status": _group_count("DTMGP Succession Case", "status", companies),
		"petitions_by_status": _group_count("DTMGP Chieftaincy Petition", "status", companies),
	}


def _group_count(doctype, fieldname, companies):
	if not companies:
		return []
	rows = frappe.get_all(doctype, filters={"company": ["in", companies]}, fields=[fieldname, "count(name) as count"], group_by=fieldname)
	return [{"label": row.get(fieldname) or "Unspecified", "count": row.count} for row in rows]

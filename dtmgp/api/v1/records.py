from collections.abc import Callable

import frappe
from frappe.utils import cint, format_datetime, formatdate

from dtmgp.permissions.scope import (
	get_allowed_companies,
	require_finance_access,
	require_governance_access,
	require_hr_access,
	require_projects_access,
	require_restricted_hr_access,
	require_traditional_access,
)


HR_DOCTYPES = {
	"Employee", "Attendance", "Shift Assignment", "Leave Application", "Leave Allocation",
	"Employee Transfer", "Employee Promotion", "Employee Separation", "Staffing Plan",
	"DTMGP Staff Verification Exercise", "DTMGP Staff Verification Record",
}
RESTRICTED_HR_DOCTYPES = {"DTMGP Personnel File", "DTMGP Next of Kin", "DTMGP Staff Document"}
FINANCE_DOCTYPES = {
	"Account", "Bank Account", "Bank Transaction", "Budget", "Cost Center", "GL Entry",
	"Journal Entry", "Payment Entry", "Purchase Receipt", "Supplier",
	"DTMGP Allocation", "DTMGP Approval Limit", "DTMGP Audit Query", "DTMGP Bank Signatory",
	"DTMGP Contract", "DTMGP Contract Variation", "DTMGP Finance Control Policy",
	"DTMGP Payment Request", "DTMGP Procurement Case", "DTMGP Procurement Plan",
	"DTMGP Revenue Assessment", "DTMGP Revenue Head", "DTMGP Revenue Receipt",
}
GOVERNANCE_DOCTYPES = {
	"Department", "DTMGP Approval Delegation", "DTMGP Compliance Requirement",
	"DTMGP Compliance Submission", "DTMGP Correspondence", "DTMGP Meeting",
	"DTMGP Resolution", "DTMGP Resolution Action", "DTMGP Statutory Return",
	"DTMGP Statutory Return Type",
}
TRADITIONAL_DOCTYPES = {
	"DTMGP Chieftaincy Petition", "DTMGP Ruling House", "DTMGP Succession Case",
	"DTMGP Traditional Allowance", "DTMGP Traditional Appointment",
	"DTMGP Traditional Institution", "DTMGP Traditional Ruler",
}
PROJECT_DOCTYPES = {
	"Project", "Task", "Asset", "Asset Movement", "Asset Maintenance",
	"Asset Maintenance Log", "Vehicle", "Vehicle Log", "DTMGP Asset Disposal",
	"DTMGP Asset Verification", "DTMGP Contractor Document", "DTMGP Project Inspection",
	"DTMGP Project Proposal",
}

DOMAIN_GATES: tuple[tuple[set[str], Callable], ...] = (
	(RESTRICTED_HR_DOCTYPES, require_restricted_hr_access),
	(HR_DOCTYPES, require_hr_access),
	(FINANCE_DOCTYPES, require_finance_access),
	(GOVERNANCE_DOCTYPES, require_governance_access),
	(TRADITIONAL_DOCTYPES, require_traditional_access),
	(PROJECT_DOCTYPES, require_projects_access),
)
ALLOWED_DOCTYPES = set().union(*(doctypes for doctypes, _gate in DOMAIN_GATES))
SKIPPED_FIELDTYPES = {"Button", "Column Break", "Fold", "Heading", "HTML", "Image", "Password", "Section Break", "Tab Break"}
# These DocTypes contain Restricted fields at permlevel 0 in upstream ERPNext or
# combine routine list data with protected case evidence. Keep their frontend DTO
# deliberately narrower than the underlying document.
FIELD_ALLOWLISTS = {
	"Employee": {"employee_name", "company", "department", "designation", "status", "date_of_joining", "company_email", "grade_level", "verification_status"},
	"Supplier": {"supplier_name", "supplier_group", "supplier_type", "country", "disabled"},
	"Bank Account": {"account_name", "bank", "company", "is_default", "is_company_account", "disabled"},
	"Bank Transaction": {"company", "bank_account", "date", "deposit", "withdrawal", "status", "unallocated_amount"},
	"DTMGP Procurement Case": {"company", "title", "procurement_plan", "estimated_amount", "applicable_threshold", "procurement_committee", "status", "public_notice_url", "recommended_supplier", "evaluated_amount", "purchase_order"},
	"DTMGP Audit Query": {"company", "query_date", "query_type", "severity", "subject", "assigned_to", "response_due_date", "status"},
	"DTMGP Chieftaincy Petition": {"company", "institution", "respondent_institution", "petition_type", "petition_date", "status", "hearing_date", "decision_date"},
	"DTMGP Succession Case": {"company", "institution", "vacancy_date", "vacancy_reason", "status", "eligible_ruling_house", "selected_candidate", "resulting_appointment"},
}


def _frontend_label(field):
	if field.fieldname == "company":
		return "LGA"
	if field.fieldname == "new_company":
		return "New LGA"
	if field.fieldname == "company_email":
		return "Work Email"
	return field.label


def _section_label(label):
	return "LGA Details" if label == "Company Details" else label


def _require_domain_access(doctype):
	if doctype not in ALLOWED_DOCTYPES:
		frappe.throw("This record type is not available in the frontend", frappe.PermissionError)
	for doctypes, gate in DOMAIN_GATES:
		if doctype in doctypes:
			gate()
			return


def _format_value(field, value):
	if value in (None, ""):
		return None
	if field.fieldtype == "Check":
		return bool(cint(value))
	if field.fieldtype == "Date":
		return formatdate(value)
	if field.fieldtype == "Datetime":
		return format_datetime(value)
	if field.fieldtype in {"Currency", "Float", "Percent"}:
		return float(value)
	if field.fieldtype in {"Int", "Long Int"}:
		return cint(value)
	return str(value)


def _serialize_fields(doc, meta):
	allowed_fields = FIELD_ALLOWLISTS.get(doc.doctype)
	sections = []
	section = {"label": "Details", "fields": []}
	sections.append(section)
	for field in meta.fields:
		if field.fieldtype in {"Section Break", "Tab Break"}:
			if field.label:
				label = _section_label(field.label)
				if section["fields"]:
					section = {"label": label, "fields": []}
					sections.append(section)
				else:
					section["label"] = label
			continue
		if field.fieldtype in SKIPPED_FIELDTYPES or field.hidden or cint(field.permlevel) > 0:
			continue
		if allowed_fields is not None and field.fieldname not in allowed_fields:
			continue
		value = doc.get(field.fieldname)
		if field.fieldtype == "Table":
			rows = []
			child_meta = frappe.get_meta(field.options)
			for child in value or []:
				row = []
				for child_field in child_meta.fields:
					if child_field.fieldtype in SKIPPED_FIELDTYPES or child_field.hidden or cint(child_field.permlevel) > 0:
						continue
					child_value = _format_value(child_field, child.get(child_field.fieldname))
					if child_value is not None:
						row.append({"label": _frontend_label(child_field), "value": child_value, "type": child_field.fieldtype})
				if row:
					rows.append(row)
			if rows:
				section["fields"].append({"label": _frontend_label(field), "value": rows, "type": "Table"})
			continue
		formatted = _format_value(field, value)
		if formatted is not None:
			section["fields"].append({"label": _frontend_label(field), "value": formatted, "type": field.fieldtype})
	return [item for item in sections if item["fields"]]


def _require_record_access(doctype, name):
	_require_domain_access(doctype)
	doc = frappe.get_doc(doctype, name)
	if not frappe.has_permission(doctype, "read", doc=doc):
		frappe.throw("You are not permitted to view this record", frappe.PermissionError)
	if doc.meta.has_field("company") and doc.get("company") and doc.get("company") not in get_allowed_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	return doc


def _record_image(doc):
	"""The record's picture (its DocType's image_field), for the drawer header.
	Employee also falls back to a Desk-attached photo, matching the people API.
	The caller is already authorized for this record, and a private image is
	served by Frappe only to users who can read the record it's attached to."""
	if doc.doctype == "Employee":
		from dtmgp.api.v1.people import employee_photo_fields

		return employee_photo_fields(doc)["image"]
	image_field = doc.meta.image_field
	return doc.get(image_field) if image_field and doc.meta.has_field(image_field) else None


@frappe.whitelist(methods=["GET"])
def get_record(doctype, name):
	doc = _require_record_access(doctype, name)
	title_field = doc.meta.title_field
	title = doc.get(title_field) if title_field else None
	return {
		"doctype": doctype,
		"doctype_label": frappe._(doctype),
		"name": doc.name,
		"title": title or doc.name,
		"status": doc.get("status") or ("Submitted" if doc.docstatus == 1 else "Cancelled" if doc.docstatus == 2 else "Draft"),
		"modified": format_datetime(doc.modified),
		"image": _record_image(doc) or None,
		"sections": _serialize_fields(doc, doc.meta),
	}


@frappe.whitelist(methods=["GET"])
def get_record_timeline(doctype, name):
	"""A record's own DTMGP Audit Event history, for the RecordDetailDrawer's Timeline
	section. Read permission on DTMGP Audit Event itself is restricted to a handful of
	audit roles (State Administrator/Auditor, Internal Auditor) -- far narrower than
	who can legitimately view a record's own detail. _require_record_access above
	already proves the caller can read *this specific record* (domain gate +
	has_permission + company scope, identical to get_record); ignore_permissions=True
	is deliberate here, scoped tightly to that one already-authorized record's own
	events (reference_doctype/reference_name), not an open query over the doctype."""
	_require_record_access(doctype, name)
	events = frappe.get_all(
		"DTMGP Audit Event",
		filters={"reference_doctype": doctype, "reference_name": name},
		fields=["name", "occurred_at", "event_type", "outcome", "actor", "summary"],
		order_by="occurred_at desc",
		limit_page_length=100,
		ignore_permissions=True,
	)
	return {"items": events}

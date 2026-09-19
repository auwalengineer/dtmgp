from copy import deepcopy

import frappe
from frappe.utils import now_datetime

SENSITIVE_KEYS = {"password", "pwd", "secret", "token", "csrf_token", "authorization", "bank_ac_no", "iban"}


def record_event(event_type, summary, outcome="Success", company=None, reference_doctype=None, reference_name=None, metadata=None):
	payload = {
		"event_type": event_type,
		"summary": summary[:500],
		"outcome": outcome,
		"company": company,
		"reference_doctype": reference_doctype,
		"reference_name": reference_name,
		"metadata": _redact(deepcopy(metadata or {})),
		"actor": getattr(frappe.session, "user", None) or "Guest",
		"request_id": getattr(frappe.local, "request_id", None),
		"ip_address": getattr(frappe.local, "request_ip", None),
	}
	_insert_event(payload)


def record_denial(event_type, summary, company=None, reference_doctype=None, reference_name=None, metadata=None):
	payload = {
		"event_type": event_type,
		"summary": summary[:500],
		"outcome": "Denied",
		"company": company,
		"reference_doctype": reference_doctype,
		"reference_name": reference_name,
		"metadata": _redact(deepcopy(metadata or {})),
		"actor": getattr(frappe.session, "user", None) or "Guest",
		"request_id": getattr(frappe.local, "request_id", None),
		"ip_address": getattr(frappe.local, "request_ip", None),
	}
	frappe.db.after_rollback.add(lambda: _insert_event(payload, commit=True))


def audit_user_permission(doc, method=None):
	company = doc.for_value if doc.allow == "Company" else None
	record_event(
		"permission_change",
		f"User permission {method or 'changed'}",
		company=company,
		reference_doctype="User Permission",
		reference_name=doc.name,
		metadata={"user": doc.user, "allow": doc.allow, "for_value": doc.for_value, "operation": method},
	)


def audit_user_change(doc, method=None):
	previous = doc.get_doc_before_save()
	if not previous:
		record_event("user_created", "User account created", reference_doctype="User", reference_name=doc.name)
		return
	changes = {}
	for field in ("enabled", "dtmgp_lga"):
		if previous.get(field) != doc.get(field):
			changes[field] = {"from": previous.get(field), "to": doc.get(field)}
	previous_roles = {row.role for row in previous.roles}
	roles = {row.role for row in doc.roles}
	if previous_roles != roles:
		changes["roles"] = {"added": sorted(roles - previous_roles), "removed": sorted(previous_roles - roles)}
	if changes:
		record_event(
			"user_access_change",
			"User access configuration changed",
			company=doc.get("dtmgp_lga"),
			reference_doctype="User",
			reference_name=doc.name,
			metadata=changes,
		)


def audit_finance_change(doc, method=None):
	_audit_scoped_record_change(doc, method, "financial_record_change")


def audit_hr_change(doc, method=None):
	_audit_scoped_record_change(doc, method, "hr_record_change")


def audit_governance_change(doc, method=None):
	_audit_scoped_record_change(doc, method, "governance_record_change")


def _audit_scoped_record_change(doc, method, default_event_type):
	event_type = "workflow_transition" if doc.has_value_changed("status") else default_event_type
	previous = doc.get_doc_before_save()
	metadata = {"operation": method, "docstatus": doc.docstatus}
	if previous and previous.get("status") != doc.get("status"):
		metadata["status"] = {"from": previous.get("status"), "to": doc.get("status")}
	record_event(
		event_type,
		f"{doc.doctype} {method or 'changed'}",
		company=doc.get("company"),
		reference_doctype=doc.doctype,
		reference_name=doc.name,
		metadata=metadata,
	)


def _insert_event(payload, commit=False):
	frappe.get_doc(
		{
			"doctype": "DTMGP Audit Event",
			"occurred_at": now_datetime(),
			"event_type": payload["event_type"],
			"outcome": payload["outcome"],
			"actor": payload["actor"],
			"company": payload.get("company"),
			"reference_doctype": payload.get("reference_doctype"),
			"reference_name": payload.get("reference_name"),
			"summary": payload["summary"],
			"metadata_json": frappe.as_json(payload.get("metadata") or {}, indent=None),
			"request_id": payload.get("request_id"),
			"ip_address": payload.get("ip_address"),
		}
	).insert(ignore_permissions=True)
	if commit:
		frappe.db.commit()


def _redact(value):
	if isinstance(value, dict):
		return {key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else _redact(item) for key, item in value.items()}
	if isinstance(value, (list, tuple)):
		return [_redact(item) for item in value]
	return value

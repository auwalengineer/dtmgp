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


def approval_limit_query(user=None): return _conditions("DTMGP Approval Limit", user)
def revenue_head_query(user=None): return _conditions("DTMGP Revenue Head", user)
def revenue_assessment_query(user=None): return _conditions("DTMGP Revenue Assessment", user)
def revenue_receipt_query(user=None): return _conditions("DTMGP Revenue Receipt", user)
def procurement_plan_query(user=None): return _conditions("DTMGP Procurement Plan", user)
def procurement_case_query(user=None): return _conditions("DTMGP Procurement Case", user)
def payment_request_query(user=None): return _conditions("DTMGP Payment Request", user)
def audit_query_query(user=None): return _conditions("DTMGP Audit Query", user)
def allocation_query(user=None): return _conditions("DTMGP Allocation", user)
def contract_query(user=None): return _conditions("DTMGP Contract", user)
def contract_variation_query(user=None): return _conditions("DTMGP Contract Variation", user)
def finance_control_policy_query(user=None): return _conditions("DTMGP Finance Control Policy", user)
def bank_signatory_query(user=None): return _conditions("DTMGP Bank Signatory", user)

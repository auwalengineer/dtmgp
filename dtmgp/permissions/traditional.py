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


def institution_query(user=None): return _conditions("DTMGP Traditional Institution", user)
def ruler_query(user=None): return _conditions("DTMGP Traditional Ruler", user)
def ruling_house_query(user=None): return _conditions("DTMGP Ruling House", user)
def appointment_query(user=None): return _conditions("DTMGP Traditional Appointment", user)
def succession_case_query(user=None): return _conditions("DTMGP Succession Case", user)
def petition_query(user=None): return _conditions("DTMGP Chieftaincy Petition", user)
def allowance_query(user=None): return _conditions("DTMGP Traditional Allowance", user)

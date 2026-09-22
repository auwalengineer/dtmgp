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


def correspondence_query(user=None):
	return _conditions("DTMGP Correspondence", user)


def meeting_query(user=None):
	return _conditions("DTMGP Meeting", user)


def resolution_query(user=None):
	return _conditions("DTMGP Resolution", user)


def resolution_action_query(user=None):
	return _conditions("DTMGP Resolution Action", user)


def statutory_return_query(user=None):
	return _conditions("DTMGP Statutory Return", user)


def compliance_submission_query(user=None):
	return _conditions("DTMGP Compliance Submission", user)


def approval_delegation_query(user=None):
	return _conditions("DTMGP Approval Delegation", user)

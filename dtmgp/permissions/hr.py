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


def verification_exercise_query(user=None): return _conditions("DTMGP Staff Verification Exercise", user)
def verification_record_query(user=None): return _conditions("DTMGP Staff Verification Record", user)
def personnel_file_query(user=None): return _conditions("DTMGP Personnel File", user)
def next_of_kin_query(user=None): return _conditions("DTMGP Next of Kin", user)
def staff_document_query(user=None): return _conditions("DTMGP Staff Document", user)
def project_query(user=None): return _conditions("Project", user)
def shift_assignment_query(user=None): return _conditions("Shift Assignment", user)


def task_query(user=None):
	"""Task has no `company` field of its own; scope through the Project it belongs
	to (the Employee Separation checklist creates one Project + Task per exit case)."""
	user = user or frappe.session.user
	if is_state_user(user):
		return ""
	companies = get_allowed_companies(user)
	if not companies:
		return "1 = 0"
	values = ", ".join(frappe.db.escape(company) for company in companies)
	return f"`tabTask`.`project` in (select name from `tabProject` where company in ({values}))"


def task_has_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if is_state_user(user):
		return True
	if not doc.project:
		return False
	company = frappe.db.get_value("Project", doc.project, "company")
	return bool(company and company in get_allowed_companies(user))


def employee_transfer_query(user=None):
	"""Employee Transfer belongs to the requesting LGA on either side (`company`, the
	employee's LGA at request time, or `new_company`, the destination for a cross-LGA
	transfer). Frappe's automatic Company User-Permission filtering already covers
	`company`; `new_company` is exempted from it via a Property Setter
	(dtmgp.setup.security.seed_employee_transfer_property_setters) precisely so this
	explicit OR condition — not an implicit AND — decides destination-LGA visibility."""
	user = user or frappe.session.user
	if is_state_user(user):
		return ""
	companies = get_allowed_companies(user)
	if not companies:
		return "1 = 0"
	values = ", ".join(frappe.db.escape(company) for company in companies)
	return f"(`tabEmployee Transfer`.`company` in ({values}) or `tabEmployee Transfer`.`new_company` in ({values}))"


def employee_transfer_has_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if is_state_user(user):
		return True
	companies = get_allowed_companies(user)
	return bool((doc.company and doc.company in companies) or (doc.new_company and doc.new_company in companies))

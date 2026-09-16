import frappe
from frappe.utils import cint, nowdate

from dtmgp.permissions.scope import can_manage_hr, get_requested_companies, require_hr_access
from dtmgp.setup.security import EMPLOYEE_GRADE_FIELD, EMPLOYEE_VERIFICATION_FIELD


@frappe.whitelist()
def get_dashboard(company=None):
	require_hr_access()
	companies = get_requested_companies(company)
	employees = _employees(companies)
	today = nowdate()
	on_leave = frappe.db.count(
		"Leave Application",
		filters={
			"company": ["in", companies],
			"status": "Approved",
			"from_date": ["<=", today],
			"to_date": [">=", today],
		},
	) if companies else 0
	verified = sum(1 for employee in employees if employee.get(EMPLOYEE_VERIFICATION_FIELD) == "Verified")
	return {
		"total": len(employees),
		"active": sum(1 for employee in employees if employee.status == "Active"),
		"verified": verified,
		"on_leave": on_leave,
		"needs_attention": len(employees) - verified,
		"can_manage": can_manage_hr(),
	}


@frappe.whitelist()
def list_employees(company=None, search=None, department=None, status=None, page=1, page_size=25):
	require_hr_access()
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"company": ["in", companies]}
	if department:
		filters["department"] = department
	if status:
		filters["status"] = status
	or_filters = None
	if search and search.strip():
		term = f"%{search.strip()}%"
		or_filters = {"employee_name": ["like", term], "name": ["like", term], "designation": ["like", term]}
	fields = [
		"name", "employee_name", "first_name", "last_name", "company", "department", "designation",
		"status", "date_of_joining", "gender", "date_of_birth", EMPLOYEE_GRADE_FIELD, EMPLOYEE_VERIFICATION_FIELD,
	]
	items = frappe.get_all(
		"Employee",
		filters=filters,
		or_filters=or_filters,
		fields=fields,
		start=(page - 1) * page_size,
		page_length=page_size,
		order_by="employee_name asc",
	)
	total = len(frappe.get_all("Employee", filters=filters, or_filters=or_filters, pluck="name"))
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist()
def get_form_options(company=None):
	require_hr_access()
	companies = get_requested_companies(company)
	return {
		"departments": frappe.get_all(
			"Department", filters={"company": ["in", companies], "disabled": 0}, pluck="name", order_by="department_name asc"
		),
		"designations": frappe.get_all("Designation", pluck="name", order_by="designation_name asc"),
		"genders": frappe.get_all("Gender", pluck="name", order_by="name asc"),
		"statuses": ["Active", "Inactive", "Suspended", "Left"],
		"verification_statuses": ["Pending", "Verified", "Review Due"],
	}


@frappe.whitelist(methods=["POST"])
def save_employee(
	first_name,
	company,
	gender,
	date_of_birth,
	date_of_joining,
	employee=None,
	last_name=None,
	department=None,
	designation=None,
	grade_level=None,
	status="Active",
	verification_status="Pending",
):
	require_hr_access(write=True)
	_validate_company(company)
	if employee:
		doc = frappe.get_doc("Employee", employee)
		_validate_company(doc.company)
	else:
		doc = frappe.new_doc("Employee")
		doc.company = company

	doc.first_name = first_name.strip()
	doc.last_name = (last_name or "").strip()
	doc.gender = gender
	doc.date_of_birth = date_of_birth
	doc.date_of_joining = date_of_joining
	doc.department = department or None
	doc.designation = designation or None
	doc.status = status
	doc.set(EMPLOYEE_GRADE_FIELD, (grade_level or "").strip())
	doc.set(EMPLOYEE_VERIFICATION_FIELD, verification_status)
	if employee:
		doc.save()
	else:
		doc.insert()
	return {"name": doc.name, "employee_name": doc.employee_name}


@frappe.whitelist(methods=["POST"])
def set_verification(employee, verification_status):
	require_hr_access(write=True)
	if verification_status not in {"Pending", "Verified", "Review Due"}:
		frappe.throw("Invalid verification status")
	doc = frappe.get_doc("Employee", employee)
	_validate_company(doc.company)
	doc.set(EMPLOYEE_VERIFICATION_FIELD, verification_status)
	doc.save()
	return {"name": doc.name, "verification_status": verification_status}


@frappe.whitelist()
def list_leave(company=None, limit=25):
	require_hr_access()
	companies = get_requested_companies(company)
	return frappe.get_all(
		"Leave Application",
		filters={"company": ["in", companies]},
		fields=["name", "employee", "employee_name", "leave_type", "from_date", "to_date", "total_leave_days", "status"],
		page_length=min(max(cint(limit), 1), 100),
		order_by="from_date desc",
	)


@frappe.whitelist()
def get_establishment(company=None):
	require_hr_access()
	companies = get_requested_companies(company)
	departments = frappe.get_all(
		"Department",
		filters={"company": ["in", companies], "disabled": 0},
		fields=["name", "department_name", "company"],
		order_by="department_name asc",
	)
	for department in departments:
		department["employee_count"] = frappe.db.count(
			"Employee", filters={"company": department.company, "department": department.name, "status": "Active"}
		)
	return departments


def _employees(companies):
	if not companies:
		return []
	return frappe.get_all(
		"Employee",
		filters={"company": ["in", companies]},
		fields=["name", "status", EMPLOYEE_VERIFICATION_FIELD],
	)


def _validate_company(company):
	if company not in get_requested_companies():
		frappe.throw("LGA is outside your permitted scope", frappe.PermissionError)

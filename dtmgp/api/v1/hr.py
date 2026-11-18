import frappe
from frappe.utils import add_months, cint, flt, get_last_day, now_datetime, today

from dtmgp.permissions.scope import (
	get_requested_companies,
	require_hr_access,
	require_payroll_access,
	require_restricted_hr_access,
	require_staff_audit_access,
)
from dtmgp.setup.organization import PARENT_COMPANY
from dtmgp.setup.security import EMPLOYEE_GRADE_FIELD, EMPLOYEE_SEPARATION_EXIT_TYPE_FIELD, EMPLOYEE_VERIFICATION_FIELD

EXERCISE_TRANSITIONS = {("Draft", "In Progress"): None, ("In Progress", "Completed"): None}
DEFAULT_SEPARATION_ACTIVITIES = (
	{"activity_name": "HR clearance", "role": "HR Officer"},
	{"activity_name": "Finance clearance", "role": "Treasurer"},
	{"activity_name": "Records and IT clearance", "role": "LGA Administrator"},
	{"activity_name": "Head of Department clearance", "role": "LGA Secretary"},
)


def _scope_guard(doc, extra_company=None):
	companies = get_requested_companies()
	if doc.company not in companies and (not extra_company or extra_company not in companies):
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)


def _block_self_decision(owner, message):
	if frappe.session.user != "Administrator" and owner == frappe.session.user and "State Administrator" not in frappe.get_roles():
		frappe.throw(message, frappe.PermissionError)


@frappe.whitelist()
def list_lga_companies():
	"""All 23 LGA names, for pickers such as a transfer's destination LGA. LGA names
	are not scope-sensitive on their own (they're the published organization list),
	unlike the records within them, which stay filtered by get_requested_companies."""
	require_hr_access()
	return frappe.get_all("Company", filters={"parent_company": PARENT_COMPANY, "is_group": 0}, pluck="name", order_by="company_name asc")


# ------------------------------------------------------- Restricted personnel records

RESTRICTED_DOCTYPES = {
	"personnel_file": ("DTMGP Personnel File", ["name", "company", "employee", "file_status", "classification", "retention_category", "retention_review_date", "physical_file_reference"]),
	"next_of_kin": ("DTMGP Next of Kin", ["name", "company", "employee", "full_name", "relationship", "phone", "alternate_phone", "email", "address", "is_primary", "verified_on"]),
	"staff_document": ("DTMGP Staff Document", ["name", "company", "employee", "document_type", "document_date", "expiry_date", "reference_number", "file", "classification", "retention_category", "retention_review_date", "verification_status", "verified_by", "verified_on"]),
}


def _restricted_definition(record_type):
	if record_type not in RESTRICTED_DOCTYPES:
		frappe.throw("Unknown restricted HR record type")
	return RESTRICTED_DOCTYPES[record_type]


@frappe.whitelist()
def list_restricted_hr_records(record_type, company=None, employee=None):
	require_restricted_hr_access()
	doctype, fields = _restricted_definition(record_type)
	companies = get_requested_companies(company)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	if employee:
		if frappe.db.get_value("Employee", employee, "company") not in companies:
			frappe.throw("Employee is outside your permitted scope", frappe.PermissionError)
		filters["employee"] = employee
	return frappe.get_all(doctype, filters=filters, fields=fields, order_by="modified desc", limit_page_length=200)


@frappe.whitelist(methods=["POST"])
def save_restricted_hr_record(record_type, values, name=None):
	require_restricted_hr_access(write=True)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	doctype, fields = _restricted_definition(record_type)
	doc = frappe.get_doc(doctype, name) if name else frappe.new_doc(doctype)
	if name:
		_scope_guard(doc)
	allowed = {field for field in fields if field not in {"name", "verified_by", "verified_on"}}
	for field in allowed:
		if field in values:
			doc.set(field, values[field])
	doc.save()
	return {"name": doc.name}


@frappe.whitelist()
def get_hr_migration_templates():
	"""Machine-readable production import layouts. Restricted values are intentionally
	not inferred; administrators must populate and validate them before import."""
	require_restricted_hr_access(write=True)
	return {
		"version": "1.0",
		"templates": {
			"employees": ["employee_id", "first_name", "last_name", "company", "gender", "date_of_birth", "date_of_joining", "department", "designation", "grade_level", "status"],
			"personnel_files": ["employee_id", "company", "file_status", "classification", "retention_category", "retention_review_date", "physical_file_reference"],
			"next_of_kin": ["employee_id", "company", "full_name", "relationship", "phone", "alternate_phone", "email", "address", "is_primary", "verified_on"],
			"staff_documents": ["employee_id", "company", "document_type", "document_date", "expiry_date", "reference_number", "private_file_url", "classification", "retention_category", "retention_review_date"],
		},
	}


# ---------------------------------------------------------------- Establishment (Staffing Plan)


@frappe.whitelist()
def list_staffing_plans(company=None, page=1, page_size=25):
	require_hr_access()
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	items = frappe.get_all(
		"Staffing Plan", filters=filters,
		fields=["name", "company", "department", "from_date", "to_date", "docstatus", "total_estimated_budget"],
		start=(page - 1) * page_size, page_length=page_size, order_by="modified desc",
	)
	total = frappe.db.count("Staffing Plan", filters=filters)
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist()
def get_staffing_plan(name):
	require_hr_access()
	doc = frappe.get_doc("Staffing Plan", name)
	_scope_guard(doc)
	return {
		"name": doc.name,
		"company": doc.company,
		"department": doc.department,
		"from_date": doc.from_date,
		"to_date": doc.to_date,
		"docstatus": doc.docstatus,
		"total_estimated_budget": doc.total_estimated_budget,
		"positions": [
			{
				"designation": row.designation,
				"number_of_positions": row.number_of_positions,
				"current_count": row.current_count,
				"vacancies": row.vacancies,
				"estimated_cost_per_position": row.estimated_cost_per_position,
				"total_estimated_cost": row.total_estimated_cost,
			}
			for row in doc.staffing_details
		],
	}


@frappe.whitelist(methods=["POST"])
def save_staffing_plan(values, name=None):
	require_hr_access(write=True)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	if name:
		doc = frappe.get_doc("Staffing Plan", name)
		if doc.docstatus != 0:
			frappe.throw("Only a draft staffing plan can be edited")
		_scope_guard(doc)
	else:
		doc = frappe.new_doc("Staffing Plan")
	for field in ("company", "department", "from_date", "to_date"):
		if field in values:
			doc.set(field, values[field])
	if not name:
		# Staffing Plan uses autoname "prompt" (the caller must supply a name).
		doc.name = f"{doc.company} Staffing Plan {doc.from_date} {frappe.generate_hash(length=4)}"
	if "staffing_details" in values:
		doc.staffing_details = []
		for row in values["staffing_details"]:
			doc.append("staffing_details", {
				"designation": row.get("designation"),
				"vacancies": row.get("vacancies"),
				"estimated_cost_per_position": row.get("estimated_cost_per_position") or 0,
			})
	doc.save()
	return {"name": doc.name, "docstatus": doc.docstatus}


@frappe.whitelist(methods=["POST"])
def submit_staffing_plan(name):
	require_hr_access(write=True)
	doc = frappe.get_doc("Staffing Plan", name)
	_scope_guard(doc)
	doc.submit()
	return {"name": doc.name, "docstatus": doc.docstatus}


@frappe.whitelist()
def get_establishment_report(company=None):
	require_hr_access()
	companies = get_requested_companies(company)
	if not companies:
		return {"positions": [], "vacant_count": 0, "overstaffed_count": 0, "approved_total": 0, "filled_total": 0}
	plan_names = frappe.get_all("Staffing Plan", filters={"company": ["in", companies], "docstatus": 1}, pluck="name")
	rows = frappe.get_all(
		"Staffing Plan Detail",
		filters={"parent": ["in", plan_names]} if plan_names else {"parent": ""},
		fields=["parent", "designation", "number_of_positions", "current_count", "current_openings", "vacancies"],
	)
	positions = []
	for row in rows:
		filled, approved = cint(row.current_count), cint(row.number_of_positions)
		status = "Vacant" if filled == 0 else ("Overstaffed" if filled > approved else ("Filled" if filled == approved else "Partially Filled"))
		positions.append({**row, "position_status": status})
	return {
		"positions": positions,
		"vacant_count": sum(1 for position in positions if position["position_status"] == "Vacant"),
		"overstaffed_count": sum(1 for position in positions if position["position_status"] == "Overstaffed"),
		"approved_total": sum(flt(position["number_of_positions"]) for position in positions),
		"filled_total": sum(flt(position["current_count"]) for position in positions),
	}


# ---------------------------------------------------------------- Postings & transfers (Employee Transfer)


@frappe.whitelist()
def list_employee_transfers(company=None, page=1, page_size=25):
	require_hr_access()
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	if not companies:
		return {"items": [], "total": 0, "page": page, "page_size": page_size}
	or_filters = {"company": ["in", companies], "new_company": ["in", companies]}
	fields = ["name", "employee", "employee_name", "company", "new_company", "department", "transfer_date", "docstatus", "owner"]
	items = frappe.get_all(
		"Employee Transfer", or_filters=or_filters, fields=fields,
		start=(page - 1) * page_size, page_length=page_size, order_by="modified desc",
	)
	for item in items:
		item["movement_type"] = "Transfer" if item.new_company and item.new_company != item.company else "Posting"
	total = len(frappe.get_all("Employee Transfer", or_filters=or_filters, pluck="name"))
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist(methods=["POST"])
def save_employee_transfer(values, name=None):
	require_hr_access(write=True)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	if name:
		doc = frappe.get_doc("Employee Transfer", name)
		if doc.docstatus != 0:
			frappe.throw("Only a draft posting or transfer can be edited")
		_scope_guard(doc, doc.new_company)
	else:
		doc = frappe.new_doc("Employee Transfer")
		doc.employee = values.get("employee")
		doc.company = frappe.db.get_value("Employee", doc.employee, "company")
	current_department = frappe.db.get_value("Employee", doc.employee, "department")
	if "transfer_date" in values:
		doc.transfer_date = values["transfer_date"]
	doc.new_company = values.get("new_company") or doc.company
	new_department = values.get("to_department") or current_department
	doc.transfer_details = []
	doc.append("transfer_details", {"property": "Department", "fieldname": "department", "current": current_department, "new": new_department})
	doc.save()
	return {"name": doc.name, "docstatus": doc.docstatus}


@frappe.whitelist(methods=["POST"])
def submit_employee_transfer(name):
	require_hr_access(write=True)
	doc = frappe.get_doc("Employee Transfer", name)
	_scope_guard(doc, doc.new_company)
	_block_self_decision(doc.owner, "You cannot submit your own posting or transfer request")
	doc.submit()
	return {"name": doc.name, "docstatus": doc.docstatus}


@frappe.whitelist(methods=["POST"])
def cancel_employee_transfer(name):
	require_hr_access(write=True)
	doc = frappe.get_doc("Employee Transfer", name)
	_scope_guard(doc, doc.new_company)
	doc.cancel()
	return {"name": doc.name, "docstatus": doc.docstatus}


# ---------------------------------------------------------------- Promotions (Employee Promotion)


@frappe.whitelist()
def list_employee_promotions(company=None, page=1, page_size=25):
	require_hr_access()
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	items = frappe.get_all(
		"Employee Promotion", filters=filters,
		fields=["name", "employee", "employee_name", "company", "promotion_date", "docstatus", "owner"],
		start=(page - 1) * page_size, page_length=page_size, order_by="modified desc",
	)
	total = frappe.db.count("Employee Promotion", filters=filters)
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist(methods=["POST"])
def save_employee_promotion(values, name=None):
	require_hr_access(write=True)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	if name:
		doc = frappe.get_doc("Employee Promotion", name)
		if doc.docstatus != 0:
			frappe.throw("Only a draft promotion review can be edited")
		_scope_guard(doc)
	else:
		doc = frappe.new_doc("Employee Promotion")
		doc.employee = values.get("employee")
		doc.company = frappe.db.get_value("Employee", doc.employee, "company")
	if "promotion_date" in values:
		doc.promotion_date = values["promotion_date"]
	current_grade = frappe.db.get_value("Employee", doc.employee, EMPLOYEE_GRADE_FIELD)
	if not values.get("proposed_grade_level") or values["proposed_grade_level"] == current_grade:
		frappe.throw("Proposed grade must be provided and differ from the current grade")
	doc.promotion_details = []
	doc.append("promotion_details", {"property": "Grade Level", "fieldname": EMPLOYEE_GRADE_FIELD, "current": current_grade, "new": values["proposed_grade_level"]})
	doc.save()
	return {"name": doc.name, "docstatus": doc.docstatus}


@frappe.whitelist(methods=["POST"])
def submit_employee_promotion(name):
	require_hr_access(write=True)
	doc = frappe.get_doc("Employee Promotion", name)
	_scope_guard(doc)
	_block_self_decision(doc.owner, "You cannot approve your own promotion review")
	doc.submit()
	return {"name": doc.name, "docstatus": doc.docstatus}


# ---------------------------------------------------------------- Verification & biometrics


@frappe.whitelist()
def list_verification_exercises(company=None, status=None, page=1, page_size=25):
	require_hr_access()
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	if status:
		filters["status"] = status
	items = frappe.get_all(
		"DTMGP Staff Verification Exercise", filters=filters,
		fields=["name", "company", "title", "cycle_start_date", "cycle_end_date", "status"],
		start=(page - 1) * page_size, page_length=page_size, order_by="modified desc",
	)
	total = frappe.db.count("DTMGP Staff Verification Exercise", filters=filters)
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist(methods=["POST"])
def save_verification_exercise(values, name=None):
	require_hr_access(write=True)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	if name:
		doc = frappe.get_doc("DTMGP Staff Verification Exercise", name)
		_scope_guard(doc)
	else:
		doc = frappe.new_doc("DTMGP Staff Verification Exercise")
	for field in ("company", "title", "cycle_start_date", "cycle_end_date"):
		if field in values:
			doc.set(field, values[field])
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def transition_verification_exercise(name, target_status):
	require_hr_access(write=True)
	doc = frappe.get_doc("DTMGP Staff Verification Exercise", name)
	_scope_guard(doc)
	transition = (doc.status, target_status)
	if transition not in EXERCISE_TRANSITIONS:
		frappe.throw(f"Transition from {doc.status} to {target_status} is not allowed")
	doc.status = target_status
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def list_verification_records(company=None, exercise=None, review_status=None, page=1, page_size=25):
	require_hr_access()
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	if exercise:
		filters["exercise"] = exercise
	if review_status:
		filters["review_status"] = review_status
	items = frappe.get_all(
		"DTMGP Staff Verification Record", filters=filters,
		fields=["name", "company", "exercise", "employee", "prepared_by", "biometric_captured", "review_status", "reviewed_by", "exception_reason"],
		start=(page - 1) * page_size, page_length=page_size, order_by="modified desc",
	)
	total = frappe.db.count("DTMGP Staff Verification Record", filters=filters)
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist(methods=["POST"])
def save_verification_record(values, name=None):
	require_hr_access(write=True)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	if "review_status" in values or "reviewed_by" in values:
		frappe.throw("Use the review action to change the review status")
	if name:
		doc = frappe.get_doc("DTMGP Staff Verification Record", name)
		_scope_guard(doc)
		if doc.review_status != "Pending":
			frappe.throw("A reviewed record cannot be edited")
	else:
		doc = frappe.new_doc("DTMGP Staff Verification Record")
	for field in ("company", "exercise", "employee", "biometric_captured", "evidence"):
		if field in values:
			doc.set(field, values[field])
	doc.save()
	return {"name": doc.name}


@frappe.whitelist(methods=["POST"])
def review_verification_record(name, review_status, exception_reason=None):
	require_hr_access(write=True)
	if review_status not in {"Verified", "Exception"}:
		frappe.throw("Invalid review status")
	doc = frappe.get_doc("DTMGP Staff Verification Record", name)
	_scope_guard(doc)
	doc.review_status = review_status
	doc.reviewed_by = frappe.session.user
	doc.reviewed_on = now_datetime()
	doc.exception_reason = exception_reason
	doc.save()
	employee = frappe.get_doc("Employee", doc.employee)
	employee.set(EMPLOYEE_VERIFICATION_FIELD, "Verified" if review_status == "Verified" else "Review Due")
	employee.save()
	return {"name": doc.name, "review_status": doc.review_status}


# ---------------------------------------------------------------- Retirement & exit (Employee Separation)


@frappe.whitelist()
def list_employee_separations(company=None, page=1, page_size=25):
	require_hr_access()
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	items = frappe.get_all(
		"Employee Separation", filters=filters,
		fields=["name", "employee", "employee_name", "company", "boarding_status", "resignation_letter_date", "docstatus", EMPLOYEE_SEPARATION_EXIT_TYPE_FIELD],
		start=(page - 1) * page_size, page_length=page_size, order_by="modified desc",
	)
	total = frappe.db.count("Employee Separation", filters=filters)
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist()
def get_employee_separation(name):
	require_hr_access()
	doc = frappe.get_doc("Employee Separation", name)
	_scope_guard(doc)
	activities = [
		{"activity_name": row.activity_name, "role": row.role, "task": row.task, "status": (frappe.db.get_value("Task", row.task, "status") if row.task else "Pending")}
		for row in doc.activities
	]
	return {
		"name": doc.name, "employee": doc.employee, "employee_name": doc.employee_name, "boarding_status": doc.boarding_status,
		"docstatus": doc.docstatus, "resignation_letter_date": doc.resignation_letter_date,
		"exit_type": doc.get(EMPLOYEE_SEPARATION_EXIT_TYPE_FIELD), "activities": activities,
	}


@frappe.whitelist(methods=["POST"])
def save_employee_separation(values, name=None):
	require_hr_access(write=True)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	if name:
		doc = frappe.get_doc("Employee Separation", name)
		if doc.docstatus != 0:
			frappe.throw("Only a draft exit case can be edited")
		_scope_guard(doc)
	else:
		doc = frappe.new_doc("Employee Separation")
		doc.employee = values.get("employee")
		employee = frappe.db.get_value("Employee", doc.employee, ["company", "department", "designation"], as_dict=True)
		doc.company, doc.department, doc.designation = employee.company, employee.department, employee.designation
	if "resignation_letter_date" in values:
		# Employee Separation.resignation_letter_date is fetch_from employee.resignation_letter_date,
		# so Frappe re-pulls it from the Employee on every save regardless of what we set here —
		# the authoritative field to write is on the Employee record itself.
		employee_doc = frappe.get_doc("Employee", doc.employee)
		if employee_doc.resignation_letter_date != values["resignation_letter_date"]:
			employee_doc.resignation_letter_date = values["resignation_letter_date"]
			employee_doc.save()
		doc.resignation_letter_date = values["resignation_letter_date"]
	if "exit_interview" in values:
		doc.exit_interview = values["exit_interview"]
	if "exit_type" in values:
		doc.set(EMPLOYEE_SEPARATION_EXIT_TYPE_FIELD, values["exit_type"])
	if not doc.activities:
		doc.boarding_begins_on = doc.resignation_letter_date or today()
		for activity in DEFAULT_SEPARATION_ACTIVITIES:
			doc.append("activities", activity)
	doc.save()
	return {"name": doc.name, "docstatus": doc.docstatus}


@frappe.whitelist(methods=["POST"])
def submit_employee_separation(name):
	require_hr_access(write=True)
	doc = frappe.get_doc("Employee Separation", name)
	_scope_guard(doc)
	doc.submit()
	return {"name": doc.name, "docstatus": doc.docstatus, "boarding_status": doc.boarding_status}


@frappe.whitelist(methods=["POST"])
def complete_separation_activity(name, activity_name):
	require_hr_access(write=True)
	doc = frappe.get_doc("Employee Separation", name)
	_scope_guard(doc)
	row = next((activity for activity in doc.activities if activity.activity_name == activity_name), None)
	if not row or not row.task:
		frappe.throw("Activity task not found — submit the exit case first")
	task = frappe.get_doc("Task", row.task)
	task.status = "Completed"
	task.save()
	doc.reload()
	if doc.boarding_status == "Completed":
		employee = frappe.get_doc("Employee", doc.employee)
		if employee.status != "Left":
			employee.status = "Left"
			employee.relieving_date = doc.resignation_letter_date
			if doc.exit_interview:
				employee.reason_for_leaving = doc.exit_interview
			employee.save()
	return {"name": doc.name, "boarding_status": doc.boarding_status}


@frappe.whitelist()
def get_retirement_forecast(company=None, months=12):
	require_hr_access()
	companies = get_requested_companies(company)
	if not companies:
		return []
	horizon = add_months(today(), cint(months))
	return frappe.get_all(
		"Employee",
		filters={"company": ["in", companies], "status": "Active", "date_of_retirement": ["between", [today(), horizon]]},
		fields=["name", "employee_name", "company", "department", "designation", "date_of_retirement"],
		order_by="date_of_retirement asc",
	)


# ---------------------------------------------------------------- Attendance


@frappe.whitelist()
def list_attendance(company=None, attendance_date=None, status=None, page=1, page_size=25):
	require_hr_access()
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	if attendance_date:
		filters["attendance_date"] = attendance_date
	if status:
		filters["status"] = status
	items = frappe.get_all(
		"Attendance", filters=filters,
		fields=["name", "employee", "employee_name", "attendance_date", "status", "late_entry", "early_exit"],
		start=(page - 1) * page_size, page_length=page_size, order_by="attendance_date desc",
	)
	total = frappe.db.count("Attendance", filters=filters)
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist()
def get_attendance_summary(company=None, attendance_date=None):
	require_hr_access()
	companies = get_requested_companies(company)
	date = attendance_date or today()
	filters = {"company": ["in", companies], "attendance_date": date} if companies else {"name": ""}
	return {
		"date": date,
		"present": frappe.db.count("Attendance", {**filters, "status": "Present"}),
		"absent": frappe.db.count("Attendance", {**filters, "status": "Absent"}),
		"on_leave": frappe.db.count("Attendance", {**filters, "status": "On Leave"}),
		"half_day": frappe.db.count("Attendance", {**filters, "status": "Half Day"}),
		"late_entries": frappe.db.count("Attendance", {**filters, "late_entry": 1}),
	}


# ---------------------------------------------------------------- Leave


@frappe.whitelist(methods=["POST"])
def decide_leave_application(name, decision):
	require_hr_access(write=True)
	if decision not in {"Approved", "Rejected"}:
		frappe.throw("Invalid decision")
	doc = frappe.get_doc("Leave Application", name)
	if doc.company not in get_requested_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	employee_user = frappe.db.get_value("Employee", doc.employee, "user_id")
	if employee_user and employee_user == frappe.session.user and frappe.session.user != "Administrator":
		frappe.throw("You cannot decide your own leave application", frappe.PermissionError)
	doc.status = decision
	if decision == "Approved":
		doc.submit()
	else:
		doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def get_leave_balances(company=None, employee=None):
	require_hr_access()
	companies = get_requested_companies(company)
	if not companies:
		return []
	filters = {"company": ["in", companies]}
	if employee:
		filters["employee"] = employee
	allocations = frappe.get_all(
		"Leave Allocation", filters=filters,
		fields=["employee", "employee_name", "leave_type", "total_leaves_allocated"],
	)
	for row in allocations:
		taken = frappe.db.sql(
			"""select coalesce(sum(total_leave_days), 0) from `tabLeave Application`
			where employee=%s and leave_type=%s and docstatus=1""",
			(row.employee, row.leave_type),
		)[0][0]
		row["taken"] = flt(taken)
		row["balance"] = flt(row.total_leaves_allocated) - flt(taken)
	return allocations


@frappe.whitelist()
def list_leave_calendar(company=None, month=None):
	require_hr_access()
	companies = get_requested_companies(company)
	if not companies:
		return []
	month = month or today()[:7]
	start = f"{month}-01"
	end = get_last_day(start)
	return frappe.get_all(
		"Leave Application",
		filters={"company": ["in", companies], "status": "Approved", "from_date": ["<=", end], "to_date": [">=", start]},
		fields=["name", "employee", "employee_name", "leave_type", "from_date", "to_date", "status"],
		order_by="from_date asc",
	)


# ---------------------------------------------------------------- Payroll (foundation only)


@frappe.whitelist()
def get_payroll_overview(company=None):
	require_payroll_access()
	companies = get_requested_companies(company)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	return {
		"draft": frappe.db.count("Salary Slip", {**filters, "docstatus": 0}),
		"submitted": frappe.db.count("Salary Slip", {**filters, "docstatus": 1, "status": ["!=", "Paid"]}),
		"paid": frappe.db.count("Salary Slip", {**filters, "status": "Paid"}),
	}


# ---------------------------------------------------------------- Staff audit


@frappe.whitelist()
def get_staff_audit_exceptions(company=None):
	require_staff_audit_access()
	companies = get_requested_companies(company)
	if not companies:
		return {"unverified": [], "duplicate_candidates": [], "missing_grade": []}
	employees = frappe.get_all(
		"Employee", filters={"company": ["in", companies], "status": "Active"},
		fields=["name", "employee_name", "company", "date_of_birth", EMPLOYEE_GRADE_FIELD, EMPLOYEE_VERIFICATION_FIELD],
	)
	unverified = [e for e in employees if e.get(EMPLOYEE_VERIFICATION_FIELD) != "Verified"]
	missing_grade = [e for e in employees if not e.get(EMPLOYEE_GRADE_FIELD)]
	grouped = {}
	for employee in employees:
		key = ((employee.employee_name or "").strip().lower(), str(employee.date_of_birth))
		grouped.setdefault(key, []).append(employee.name)
	duplicate_candidates = [
		{"employee_name": key[0], "date_of_birth": key[1], "employees": names}
		for key, names in grouped.items() if len(names) > 1
	]
	return {"unverified": unverified, "duplicate_candidates": duplicate_candidates, "missing_grade": missing_grade}


# ---------------------------------------------------------------- HR reports


@frappe.whitelist()
def get_hr_report(
	report, company=None, department=None, status=None, grade_level=None, group_by=None, dimension=None,
	months=None, from_date=None, to_date=None,
):
	"""One HR report (see dtmgp.hr_reports) for the caller's scope. The LGA is
	always resolved server-side; every other value is a validated filter."""
	from dtmgp.hr_reports import run_report

	require_hr_access()
	companies = get_requested_companies(company)
	params = {
		"department": department, "status": status, "grade_level": grade_level, "group_by": group_by,
		"dimension": dimension, "months": months, "from_date": from_date, "to_date": to_date,
	}
	return run_report(report, companies, params)


@frappe.whitelist()
def get_hr_report_options(company=None):
	"""Filter choices for the HR reports screen, limited to the caller's scope."""
	from dtmgp.hr_reports import DIMENSIONS, GROUP_LABELS, LEAVE_GROUPS, RETIREMENT_HORIZONS, STATUSES

	require_hr_access()
	companies = get_requested_companies(company)
	departments = frappe.get_all(
		"Department", filters={"company": ["in", companies or [""]], "is_group": 0},
		fields=["name", "department_name", "company"], order_by="department_name asc",
	)
	statewide = len(companies) > 1
	return {
		"departments": [
			{"value": row.name, "label": f"{row.department_name} ({row.company.replace(' Local Government Area', '')})" if statewide else row.department_name}
			for row in departments
		],
		"statuses": [*STATUSES, "All"],
		"group_by": [{"value": key, "label": label} for key, label in GROUP_LABELS.items() if statewide or key != "lga"],
		"dimensions": [{"value": key, "label": label} for key, label in DIMENSIONS.items() if statewide or key != "lga"],
		"leave_groups": [{"value": key, "label": label} for key, label in LEAVE_GROUPS.items() if statewide or key != "lga"],
		"retirement_horizons": list(RETIREMENT_HORIZONS),
		"is_statewide": statewide,
	}


@frappe.whitelist()
def get_hr_reports(company=None):
	require_hr_access()
	companies = get_requested_companies(company)
	if not companies:
		return {
			"strength_by_department": [], "distribution_by_gender": [], "retirement_forecast_12m": 0,
			"leave_by_type": [], "establishment": {"approved_total": 0, "filled_total": 0, "vacant_count": 0},
		}
	filters = {"company": ["in", companies], "status": "Active"}
	strength_by_department = frappe.get_all("Employee", filters=filters, group_by="department", fields=["department", "count(name) as count"])
	distribution_by_gender = frappe.get_all("Employee", filters=filters, group_by="gender", fields=["gender", "count(name) as count"])
	leave_by_type = frappe.get_all(
		"Leave Application", filters={"company": ["in", companies], "docstatus": 1},
		group_by="leave_type", fields=["leave_type", "sum(total_leave_days) as days"],
	)
	establishment = get_establishment_report(company)
	return {
		"strength_by_department": strength_by_department,
		"distribution_by_gender": distribution_by_gender,
		"retirement_forecast_12m": len(get_retirement_forecast(company, 12)),
		"leave_by_type": leave_by_type,
		"establishment": {
			"approved_total": establishment["approved_total"],
			"filled_total": establishment["filled_total"],
			"vacant_count": establishment["vacant_count"],
		},
	}

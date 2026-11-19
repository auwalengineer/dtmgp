import frappe
from frappe.utils import cint, date_diff, getdate, nowdate

from dtmgp.audit import record_event
from dtmgp.permissions.scope import can_manage_hr, get_requested_companies, require_hr_access
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import (
	EMPLOYEE_GRADE_FIELD,
	EMPLOYEE_RETIRE_BY_AGE_FIELD,
	EMPLOYEE_RETIRE_BY_SERVICE_FIELD,
	EMPLOYEE_VERIFICATION_FIELD,
)
from dtmgp.workforce import DISPLAYABLE_IMAGE_EXTENSIONS, REMOVED_PHOTO_FIELD, attached_photos, get_workforce_summary

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")

# Fields an HR manager may edit from the Vue app. Deliberately excluded:
# - company (LGA): moves between LGAs go through Employee Transfer, not an edit;
# - iban: not used for Nigerian (NUBAN) accounts;
# - NIN verification outcome fields: set by the verification process, not by hand;
# - derived retire-by dates: recomputed in dtmgp.hr.validate_employee_record.
EDITABLE_EMPLOYEE_FIELDS = (
	"first_name", "middle_name", "last_name", "gender", "date_of_birth", "date_of_joining",
	"department", "designation", "status", "relieving_date", "reason_for_leaving",
	"employee_number", EMPLOYEE_GRADE_FIELD, "dtmgp_step", "dtmgp_rank", "dtmgp_schedule_of_duty",
	EMPLOYEE_VERIFICATION_FIELD, "dtmgp_date_of_first_appointment", "dtmgp_date_of_present_appointment",
	"date_of_retirement", "dtmgp_local_govt_of_payment", "salary_mode", "bank_name", "bank_ac_no",
	"cell_number", "personal_email", "person_to_be_contacted", "relation", "emergency_phone_number",
	"dtmgp_lg_of_origin", "dtmgp_council_ward", "dtmgp_bvn", "dtmgp_nin", "dtmgp_qualifications",
)
READONLY_EMPLOYEE_FIELDS = ("name", "employee_name", "company", "image", EMPLOYEE_RETIRE_BY_AGE_FIELD, EMPLOYEE_RETIRE_BY_SERVICE_FIELD)
REQUIRED_EMPLOYEE_FIELDS = ("first_name", "gender", "date_of_birth", "date_of_joining", "status")
EMPLOYEE_GENDERS = ("Male", "Female")
EMPLOYEE_STATUSES = ("Active", "Inactive", "Suspended", "Left")
VERIFICATION_STATUSES = ("Pending", "Verified", "Review Due")
SALARY_MODES = ("Bank", "Cash", "Cheque")
BANK_FIELDS = ("salary_mode", "bank_name", "bank_ac_no")


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
def get_workforce_dashboard(company=None):
	"""Overall employee dashboard: totals and breakdowns across every LGA the caller
	may see (or just the one requested LGA). Aggregates only — no per-person fields."""
	require_hr_access()
	return get_workforce_summary(get_requested_companies(company))


def employee_photo_fields(doc):
	"""`image` plus whether it came from an attachment rather than the Image field."""
	if doc.image:
		return {"image": doc.image, "image_from_attachment": False}
	attached = attached_photos([doc.name]).get(doc.name)
	return {"image": attached, "image_from_attachment": bool(attached)}


def _directory_filters(companies, department, status, gender, designation, grade_level, verification_status):
	"""Staff-directory filters. Enumerated values are checked against their allowed
	options so a bad value is an error, not a silently empty list."""
	filters = [["company", "in", companies]]
	for value, allowed, label in (
		(status, EMPLOYEE_STATUSES, "employment status"),
		(gender, EMPLOYEE_GENDERS, "gender"),
		(verification_status, VERIFICATION_STATUSES, "verification status"),
	):
		if value and value not in allowed:
			frappe.throw(f"Unknown {label}: {value}")
	if department:
		filters.append(["department", "=", department])
	if status:
		filters.append(["status", "=", status])
	if gender:
		filters.append(["gender", "=", gender])
	if designation:
		filters.append(["designation", "=", designation])
	if grade_level:
		filters.append([EMPLOYEE_GRADE_FIELD, "=", grade_level])
	if verification_status == "Pending":
		# Records never verified have no status at all; the UI shows those as Pending too.
		# Frappe applies ifnull() for "not in", so empty values match.
		filters.append([EMPLOYEE_VERIFICATION_FIELD, "not in", [s for s in VERIFICATION_STATUSES if s != "Pending"]])
	elif verification_status:
		filters.append([EMPLOYEE_VERIFICATION_FIELD, "=", verification_status])
	return filters


@frappe.whitelist()
def list_employees(
	company=None, search=None, department=None, status=None, page=1, page_size=25,
	gender=None, designation=None, grade_level=None, verification_status=None,
):
	require_hr_access()
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = _directory_filters(companies, department, status, gender, designation, grade_level, verification_status)
	or_filters = None
	if search and search.strip():
		term = f"%{search.strip()}%"
		or_filters = {"employee_name": ["like", term], "name": ["like", term], "designation": ["like", term]}
	fields = [
		"name", "employee_name", "first_name", "last_name", "company", "department", "designation",
		"status", "date_of_joining", "gender", "date_of_birth", "image", EMPLOYEE_GRADE_FIELD, EMPLOYEE_VERIFICATION_FIELD,
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
	attached = attached_photos([row.name for row in items if not row.image])
	for row in items:
		if not row.image and row.name in attached:
			row.image = attached[row.name]
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
		"genders": list(EMPLOYEE_GENDERS),
		"statuses": list(EMPLOYEE_STATUSES),
		"verification_statuses": list(VERIFICATION_STATUSES),
		"grade_levels": _grade_levels(companies),
	}


def _grade_levels(companies):
	"""Grade levels actually recorded in scope (the field is free text), in GL order."""
	values = frappe.get_all(
		"Employee", filters={"company": ["in", companies], EMPLOYEE_GRADE_FIELD: ["is", "set"]},
		pluck=EMPLOYEE_GRADE_FIELD, distinct=True,
	)

	def order(value):
		return (int("".join(ch for ch in value if ch.isdigit()) or 0), value)

	return sorted({value.strip() for value in values if value and value.strip()}, key=order)


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
	_validate_gender(gender)
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


@frappe.whitelist()
def get_employee_for_edit(employee):
	"""Current values of the editable allowlist (plus read-only context) for the
	edit form. Manage-only, since it includes identity numbers (BVN/NIN)."""
	require_hr_access(write=True)
	doc = frappe.get_doc("Employee", employee)
	_validate_company(doc.company)
	return {
		"values": {field: doc.get(field) for field in EDITABLE_EMPLOYEE_FIELDS},
		"readonly": {**{field: doc.get(field) for field in READONLY_EMPLOYEE_FIELDS}, **employee_photo_fields(doc)},
		"pay_points": [lga.name for lga in BENUE_LGAS],
		"salary_modes": list(SALARY_MODES),
		# bank_name may be a Select (Nigerian banks, via property setter) or free text; return its options if any.
		"banks": [option for option in (frappe.get_meta("Employee").get_field("bank_name").options or "").split("\n") if option],
	}


@frappe.whitelist(methods=["POST"])
def update_employee(employee, values):
	"""Apply an allowlisted partial update to an existing Employee. Unknown keys are
	rejected rather than ignored so a client can't silently think it changed e.g. the LGA."""
	require_hr_access(write=True)
	values = frappe.parse_json(values) if isinstance(values, str) else (values or {})
	unknown = sorted(set(values) - set(EDITABLE_EMPLOYEE_FIELDS))
	if unknown:
		frappe.throw(f"These fields cannot be edited here: {', '.join(unknown)}")
	doc = frappe.get_doc("Employee", employee)
	_validate_company(doc.company)
	for field in REQUIRED_EMPLOYEE_FIELDS:
		if field in values and not str(values[field] or "").strip():
			frappe.throw(f"{doc.meta.get_label(field)} is required")
	if "gender" in values:
		_validate_gender(values["gender"])
	if values.get("salary_mode") and values["salary_mode"] not in SALARY_MODES:
		frappe.throw(f"Salary mode must be one of: {', '.join(SALARY_MODES)}")
	if values.get("bank_ac_no") and not (str(values["bank_ac_no"]).strip().isdigit() and len(str(values["bank_ac_no"]).strip()) == 10):
		frappe.throw("Bank account number must be exactly 10 digits (NUBAN)")
	if values.get("dtmgp_local_govt_of_payment") and values["dtmgp_local_govt_of_payment"] not in {lga.name for lga in BENUE_LGAS}:
		frappe.throw("Local Govt. of Payment must be one of the Benue LGAs")

	changed = []
	for field, value in values.items():
		value = value.strip() if isinstance(value, str) else value
		value = None if value == "" else value
		if _normalized(doc.get(field)) != _normalized(value):
			doc.set(field, value)
			changed.append(field)
	if not changed:
		return {"name": doc.name, "employee_name": doc.employee_name, "changed": []}
	# Only enforced when pay details are being edited, so an unrelated edit to an
	# imported record with incomplete bank data isn't blocked.
	if set(changed) & set(BANK_FIELDS) and doc.salary_mode == "Bank" and not (doc.bank_name and doc.bank_ac_no):
		frappe.throw("Bank name and account number are required when salary mode is Bank")
	doc.save()
	# Field names only, never values: the set includes BVN/NIN and contact details.
	record_event(
		"hr_record_change", f"Employee {doc.name} updated", company=doc.company,
		reference_doctype="Employee", reference_name=doc.name, metadata={"changed_fields": changed},
	)
	return {"name": doc.name, "employee_name": doc.employee_name, "changed": changed}


@frappe.whitelist(methods=["POST"])
def set_employee_image(employee, file_url=None):
	"""Set (or clear, when file_url is empty) the native Employee.image photo.
	The file must already be uploaded and attached to this same Employee —
	upload_file checks Employee write permission, and a private attached File
	inherits the Employee's LGA-scoped read permission — so a caller can't point
	the photo at another record's (or another LGA's) file."""
	require_hr_access(write=True)
	doc = frappe.get_doc("Employee", employee)
	_validate_company(doc.company)
	if file_url:
		attached = frappe.db.exists(
			"File", {"file_url": file_url, "attached_to_doctype": "Employee", "attached_to_name": doc.name}
		)
		if not attached:
			frappe.throw("Upload the photo to this employee record first")
		if not file_url.lower().endswith(IMAGE_EXTENSIONS):
			frappe.throw("Employee photo must be a JPG, PNG or WebP image")
	if not file_url:
		# Removing the photo must not let an attachment reappear as the photo
		# (see dtmgp.workforce.attached_photos). The files stay attached — personnel records are
		# retained — they're just no longer photo candidates.
		for row in frappe.get_all(
			"File", filters={"attached_to_doctype": "Employee", "attached_to_name": doc.name, "is_folder": 0},
			fields=["name", "file_url"],
		):
			if (row.file_url or "").lower().endswith(DISPLAYABLE_IMAGE_EXTENSIONS):
				frappe.db.set_value("File", row.name, "attached_to_field", REMOVED_PHOTO_FIELD, update_modified=False)
	doc.image = file_url or None
	doc.save()
	return {"name": doc.name, "image": doc.image}


@frappe.whitelist()
def get_employee_profile(employee):
	"""Consolidated read view backing the Staff Profiles / Digital Personnel File /
	Employment History / Next of Kin nav items: the employee's own record plus the
	native Employee child tables (internal/external work history) and emergency
	contact fields already on core Employee — no new Restricted-data store."""
	require_hr_access()
	doc = frappe.get_doc("Employee", employee)
	_validate_company(doc.company)
	return {
		"name": doc.name, "employee_name": doc.employee_name, "company": doc.company, **employee_photo_fields(doc),
		"department": doc.department, "designation": doc.designation, "status": doc.status,
		"gender": doc.gender, "date_of_birth": doc.date_of_birth, "date_of_joining": doc.date_of_joining,
		"grade_level": doc.get(EMPLOYEE_GRADE_FIELD), "verification_status": doc.get(EMPLOYEE_VERIFICATION_FIELD),
		"cell_number": doc.cell_number, "personal_email": doc.personal_email,
		"emergency_contact": {
			"person_to_be_contacted": doc.person_to_be_contacted,
			"relation": doc.relation,
			"emergency_phone_number": doc.emergency_phone_number,
		},
		"internal_work_history": [
			{"department": row.department, "designation": row.designation, "branch": row.branch, "from_date": row.from_date, "to_date": row.to_date}
			for row in doc.internal_work_history
		],
		"external_work_history": [
			{"company_name": row.company_name, "designation": row.designation, "contact": row.contact, "total_experience": row.total_experience}
			for row in doc.external_work_history
		],
		"sections": _profile_sections(doc),
	}


def _mask(value):
	"""Last four characters only: the profile is readable by more roles than can edit."""
	value = (value or "").strip()
	return f"{'•' * max(len(value) - 4, 0)}{value[-4:]}" if value else None


def _profile_sections(doc):
	"""The full employee record for the Staff Profile view, grouped like the edit
	form. Each field is {label, value, type}; type is text, date, years or masked.
	BVN, NIN and account number are masked here — the edit form (HR write access)
	is where full values are handled."""
	today = getdate(nowdate())

	def years(start):
		return round(date_diff(today, start) / 365.25, 1) if start else None

	department = frappe.db.get_value("Department", doc.department, "department_name") if doc.department else None
	first_appointment = doc.get("dtmgp_date_of_first_appointment") or doc.date_of_joining
	by_age, by_service = doc.get(EMPLOYEE_RETIRE_BY_AGE_FIELD), doc.get(EMPLOYEE_RETIRE_BY_SERVICE_FIELD)
	retirement = getdate(doc.date_of_retirement) if doc.date_of_retirement else None
	basis = None
	if retirement:
		basis = "Age (60 years)" if by_age and getdate(by_age) == retirement else (
			"Service (35 years)" if by_service and getdate(by_service) == retirement else "Set manually"
		)

	def field(label, value, kind="text"):
		return {"label": label, "value": value if value not in ("", None) else None, "type": kind}

	service = [
		field("LGA", doc.company.replace(" Local Government Area", " LGA") if doc.company else None),
		field("Department", department or doc.department),
		field("Designation", doc.designation),
		field("Rank", doc.get("dtmgp_rank")),
		field("Grade level", doc.get(EMPLOYEE_GRADE_FIELD)),
		field("Step", doc.get("dtmgp_step") or None),
		field("Schedule of duty", doc.get("dtmgp_schedule_of_duty")),
		field("Employment status", doc.status),
		field("Date joined", doc.date_of_joining, "date"),
		field("Date of 1st appointment", doc.get("dtmgp_date_of_first_appointment"), "date"),
		field("Date of present appointment", doc.get("dtmgp_date_of_present_appointment"), "date"),
		field("Years of service", years(first_appointment), "years"),
		field("Date of retirement", doc.date_of_retirement, "date"),
		field("Retirement basis", basis),
		field("Retires by age", by_age, "date"),
		field("Retires by length of service", by_service, "date"),
	]
	if doc.status == "Left":
		service += [field("Relieving date", doc.relieving_date, "date"), field("Reason for leaving", doc.reason_for_leaving)]
	return [
		{"label": "Personal", "fields": [
			field("Staff ID", doc.name), field("File no.", doc.employee_number),
			field("First name", doc.first_name), field("Middle name", doc.middle_name), field("Last name", doc.last_name),
			field("Gender", doc.gender), field("Date of birth", doc.date_of_birth, "date"),
			field("Age", years(doc.date_of_birth), "years"), field("Qualifications", doc.get("dtmgp_qualifications")),
		]},
		{"label": "Service & appointment", "fields": service},
		{"label": "Verification & identity", "fields": [
			field("Verification status", doc.get(EMPLOYEE_VERIFICATION_FIELD) or "Pending"),
			field("BVN", _mask(doc.get("dtmgp_bvn")), "masked"), field("NIN", _mask(doc.get("dtmgp_nin")), "masked"),
			field("NIN verification", doc.get("dtmgp_nin_verification_status")),
			field("Name match", doc.get("dtmgp_name_match_status")),
			field("Last verification attempt", doc.get("dtmgp_last_verification_attempt"), "date"),
			field("Verification date", doc.get("dtmgp_nin_verification_date"), "date"),
			field("Verification remarks", doc.get("dtmgp_verification_remarks")),
		]},
		{"label": "Pay & bank", "fields": [
			field("Pay point", doc.get("dtmgp_local_govt_of_payment")), field("Salary mode", doc.salary_mode),
			field("Bank", doc.bank_name), field("Account number", _mask(doc.bank_ac_no), "masked"),
		]},
		{"label": "Contact & next of kin", "fields": [
			field("Phone number", doc.cell_number), field("Personal email", doc.personal_email),
			field("Work email", doc.company_email), field("Emergency contact", doc.person_to_be_contacted),
			field("Relationship", doc.relation), field("Emergency phone", doc.emergency_phone_number),
		]},
		{"label": "Origin", "fields": [
			field("LG of origin", doc.get("dtmgp_lg_of_origin")), field("Council ward", doc.get("dtmgp_council_ward")),
		]},
	]


@frappe.whitelist()
def list_employee_documents(employee):
	"""Staff Documents: exposes the generic, already-scoped Frappe file-attachment
	feature for the Employee record (contracts, certificates, ID scans) rather than
	a new Restricted personnel-file store — File permission inherits from the
	attached Employee, which is already LGA-scoped."""
	require_hr_access()
	doc = frappe.get_doc("Employee", employee)
	_validate_company(doc.company)
	return frappe.get_all(
		"File", filters={"attached_to_doctype": "Employee", "attached_to_name": employee},
		fields=["name", "file_name", "file_url", "is_private", "creation"], order_by="creation desc",
	)


@frappe.whitelist()
def list_former_staff(company=None, page=1, page_size=25):
	require_hr_access()
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"company": ["in", companies], "status": "Left"} if companies else {"name": ""}
	items = frappe.get_all(
		"Employee", filters=filters,
		fields=["name", "employee_name", "company", "department", "designation", "relieving_date", "reason_for_leaving"],
		start=(page - 1) * page_size, page_length=page_size, order_by="relieving_date desc",
	)
	total = frappe.db.count("Employee", filters=filters)
	return {"items": items, "total": total, "page": page, "page_size": page_size}


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


def _validate_gender(gender):
	if gender not in EMPLOYEE_GENDERS:
		frappe.throw("Gender must be Male or Female")


def _normalized(value):
	# DB-loaded dates are date objects and ints are ints; the client sends strings.
	return None if value is None or value == "" else str(value)


def _validate_company(company):
	if company not in get_requested_companies():
		frappe.throw("LGA is outside your permitted scope", frappe.PermissionError)

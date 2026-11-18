"""HR reports for the Vue People & HR > Reports tab.

Each report is a function ``(companies, params) -> dict`` returning a uniform
shape the frontend renders generically and exports as CSV::

    {"columns": [{"key", "label", "type"}], "rows": [{key: value}],
     "totals": {key: value} | None, "summary": [{"label", "value", "unit"?}],
     "note": str | None, "truncated": bool}

Column ``type`` is one of text, int, pct (0-100), years, date (ISO string).

Callers MUST pass a company list already resolved through
``get_requested_companies``; an empty list yields an empty report. No report
returns BVN, NIN or bank values — only whether they are captured.
"""

from collections import Counter, defaultdict

import frappe
from frappe.utils import add_months, cint, getdate, nowdate

from dtmgp.setup.security import (
	EMPLOYEE_FIRST_APPOINTMENT_FIELD,
	EMPLOYEE_GRADE_FIELD,
	EMPLOYEE_RETIRE_BY_AGE_FIELD,
	EMPLOYEE_RETIRE_BY_SERVICE_FIELD,
	EMPLOYEE_VERIFICATION_FIELD,
)
from dtmgp.workforce import (
	AGE_BANDS,
	COMPLETENESS,
	GRADE_BANDS,
	SERVICE_BANDS,
	UNSPECIFIED,
	_active,
	_appointment_date,
	_band,
	_department_names,
	_employees,
	_grade_band,
	_grade_sort_key,
	_pct,
	_years,
	short_lga,
)

# Matches the CSV export row limit in dtmgp.api.v1.report_exports.
MAX_ROWS = 5000
STATUSES = ("Active", "Suspended", "Inactive", "Left")
RETIREMENT_HORIZONS = (12, 24, 36, 60)
GROUP_LABELS = {"lga": "LGA", "department": "Department", "designation": "Designation", "grade_band": "Grade band"}
DIMENSIONS = {
	"gender": "Gender", "grade_level": "Grade level", "grade_band": "Grade band", "age_band": "Age band",
	"service_band": "Years of service", "department": "Department", "designation": "Designation",
	"rank": "Rank", "status": "Employment status", "salary_mode": "Salary mode", "lga": "LGA",
}
LEAVE_GROUPS = {"leave_type": "Leave type", "department": "Department", "month": "Month", "lga": "LGA"}


def _col(key, label, kind="text"):
	return {"key": key, "label": label, "type": kind}


def _result(columns, rows, totals=None, summary=None, note=None, truncated=False):
	return {"columns": columns, "rows": rows, "totals": totals, "summary": summary or [], "note": note, "truncated": truncated}


def _choice(value, allowed, default, label):
	value = value or default
	if value not in allowed:
		frappe.throw(f"Unknown {label}: {value}")
	return value


def _period(params):
	"""(from, to) dates; defaults to the current calendar year to date."""
	today = getdate(nowdate())
	start = getdate(params.get("from_date") or f"{today.year}-01-01")
	end = getdate(params.get("to_date") or today)
	if start > end:
		frappe.throw("The start date must be on or before the end date")
	return start, end


def _default_group(companies):
	return "lga" if len(companies) > 1 else "department"


def _group_key(group_by, departments):
	if group_by == "lga":
		return lambda row: short_lga(row.company)
	if group_by == "department":
		return lambda row: departments.get(row.department) or row.department or UNSPECIFIED
	if group_by == "designation":
		return lambda row: row.designation or UNSPECIFIED
	return lambda row: _grade_band(row.get(EMPLOYEE_GRADE_FIELD))


def _group_order(group_by, labels):
	if group_by == "grade_band":
		order = [label for _low, _high, label in GRADE_BANDS] + [UNSPECIFIED]
		return [label for label in order if label in labels]
	return sorted(labels, key=lambda label: (label == UNSPECIFIED, label))


def _scoped_employees(companies, params):
	"""Workforce rows narrowed by the optional department filter."""
	rows = _employees(companies)
	if params.get("department"):
		rows = [row for row in rows if row.department == params["department"]]
	return rows


# --------------------------------------------------------------------------- Nominal roll


def nominal_roll(companies, params):
	status = params.get("status") or "Active"
	if status not in (*STATUSES, "All"):
		frappe.throw(f"Unknown employment status: {status}")
	filters = {"company": ["in", companies]}
	if status != "All":
		filters["status"] = status
	if params.get("department"):
		filters["department"] = params["department"]
	if params.get("grade_level"):
		filters[EMPLOYEE_GRADE_FIELD] = params["grade_level"]
	fields = [
		"name", "employee_name", "company", "department", "designation", "dtmgp_rank", EMPLOYEE_GRADE_FIELD, "dtmgp_step",
		"gender", "date_of_birth", EMPLOYEE_FIRST_APPOINTMENT_FIELD, "dtmgp_date_of_present_appointment", "date_of_joining",
		"date_of_retirement", "status", EMPLOYEE_VERIFICATION_FIELD,
	]
	records = frappe.get_all("Employee", filters=filters, fields=fields, order_by="employee_name asc", limit_page_length=MAX_ROWS + 1)
	truncated = len(records) > MAX_ROWS
	records = records[:MAX_ROWS]
	departments = _department_names({row.department for row in records if row.department})
	statewide = len(companies) > 1
	records.sort(key=lambda row: (
		row.company if statewide else "", departments.get(row.department) or row.department or "~",
		-(_grade_sort_key((row.get(EMPLOYEE_GRADE_FIELD) or "").strip().upper())[1] if row.get(EMPLOYEE_GRADE_FIELD) else 0),
		row.employee_name or "",
	))
	columns = [_col("name", "Staff ID"), _col("employee_name", "Name")]
	if statewide:
		columns.append(_col("lga", "LGA"))
	columns += [
		_col("department", "Department"), _col("designation", "Designation"), _col("rank", "Rank"), _col("grade_level", "Grade"),
		_col("step", "Step", "int"), _col("gender", "Gender"), _col("date_of_birth", "Date of birth", "date"),
		_col("first_appointment", "Date of 1st appt", "date"), _col("present_appointment", "Date of present appt", "date"),
		_col("date_of_retirement", "Retirement date", "date"), _col("status", "Status"), _col("verification", "Verification"),
	]
	rows = [{
		"name": row.name, "employee_name": row.employee_name, "lga": short_lga(row.company),
		"department": departments.get(row.department) or row.department, "designation": row.designation,
		"rank": row.dtmgp_rank, "grade_level": row.get(EMPLOYEE_GRADE_FIELD), "step": row.dtmgp_step or None,
		"gender": row.gender, "date_of_birth": _iso(row.date_of_birth),
		"first_appointment": _iso(row.get(EMPLOYEE_FIRST_APPOINTMENT_FIELD) or row.date_of_joining),
		"present_appointment": _iso(row.dtmgp_date_of_present_appointment),
		"date_of_retirement": _iso(row.date_of_retirement), "status": row.status,
		"verification": row.get(EMPLOYEE_VERIFICATION_FIELD) or "Pending",
	} for row in records]
	genders = Counter(row["gender"] for row in rows)
	summary = [
		{"label": "Staff listed", "value": len(rows)},
		{"label": "Male", "value": genders.get("Male", 0)},
		{"label": "Female", "value": genders.get("Female", 0)},
		{"label": "Verified", "value": sum(1 for row in rows if row["verification"] == "Verified")},
	]
	note = f"Only the first {MAX_ROWS:,} staff are listed; narrow the filters to see the rest." if truncated else None
	return _result(columns, rows, summary=summary, note=note, truncated=truncated)


# --------------------------------------------------------------------------- Staff strength


def staff_strength(companies, params):
	group_by = _choice(params.get("group_by"), GROUP_LABELS, _default_group(companies), "grouping")
	employees = _scoped_employees(companies, params)
	departments = _department_names({row.department for row in employees if row.department})
	key = _group_key(group_by, departments)
	groups = defaultdict(list)
	for row in employees:
		groups[key(row)].append(row)
	if group_by == "lga":
		for company in companies:
			groups.setdefault(short_lga(company), [])
	bands = [label for _low, _high, label in GRADE_BANDS]

	def measure(members):
		active = _active(members)
		band_counts = Counter(_grade_band(row.get(EMPLOYEE_GRADE_FIELD)) for row in active)
		return {
			"active": len(active),
			"male": sum(1 for row in active if row.gender == "Male"),
			"female": sum(1 for row in active if row.gender == "Female"),
			"junior": band_counts.get(bands[0], 0), "senior": band_counts.get(bands[1], 0),
			"management": band_counts.get(bands[2], 0), "no_grade": band_counts.get(UNSPECIFIED, 0),
			"suspended_inactive": sum(1 for row in members if row.status in ("Suspended", "Inactive")),
			"left": sum(1 for row in members if row.status == "Left"),
			"on_roll": len(members),
		}

	rows = [{"group": label, **measure(groups[label])} for label in _group_order(group_by, groups)]
	totals = {"group": "Total", **measure(employees)}
	for row in [*rows, totals]:
		row["share_pct"] = _pct(row["active"], totals["active"])
	columns = [
		_col("group", GROUP_LABELS[group_by]), _col("active", "Active", "int"), _col("share_pct", "% of active", "pct"),
		_col("male", "Male", "int"), _col("female", "Female", "int"), _col("junior", "Junior (GL 01-06)", "int"),
		_col("senior", "Senior (GL 07-12)", "int"), _col("management", "Management (GL 13-17)", "int"),
		_col("no_grade", "No grade", "int"), _col("suspended_inactive", "Suspended / inactive", "int"),
		_col("left", "Exited", "int"), _col("on_roll", "Total on roll", "int"),
	]
	summary = [
		{"label": "Active staff", "value": totals["active"]},
		{"label": "Female share", "value": _pct(totals["female"], totals["male"] + totals["female"]), "unit": "pct"},
		{"label": "Management cadre", "value": totals["management"]},
		{"label": "Suspended / inactive", "value": totals["suspended_inactive"]},
	]
	return _result(columns, rows, totals=totals, summary=summary)


# --------------------------------------------------------------------------- Distribution


def staff_distribution(companies, params):
	dimension = _choice(params.get("dimension"), DIMENSIONS, "grade_level", "dimension")
	employees = _scoped_employees(companies, params)
	active = _active(employees)
	today = getdate(nowdate())
	departments = _department_names({row.department for row in employees if row.department})
	population = employees if dimension == "status" else active
	key = _dimension_key(dimension, departments, today)
	groups = defaultdict(list)
	for row in population:
		groups[key(row) or UNSPECIFIED].append(row)
	labels = _dimension_order(dimension, groups)
	rows = []
	for label in labels:
		members = groups.get(label, [])
		rows.append({
			"group": label, "staff": len(members),
			"male": sum(1 for row in members if row.gender == "Male"),
			"female": sum(1 for row in members if row.gender == "Female"),
			"share_pct": _pct(len(members), len(population)),
		})
	totals = {
		"group": "Total", "staff": len(population), "male": sum(row["male"] for row in rows),
		"female": sum(row["female"] for row in rows), "share_pct": 100 if population else 0,
	}
	columns = [
		_col("group", DIMENSIONS[dimension]), _col("staff", "Staff", "int"), _col("share_pct", "% of staff", "pct"),
		_col("male", "Male", "int"), _col("female", "Female", "int"),
	]
	largest = max(rows, key=lambda row: row["staff"], default=None)
	summary = [
		{"label": "Staff counted", "value": len(population)},
		{"label": "Groups", "value": sum(1 for row in rows if row["staff"])},
		{"label": "Largest group", "value": f"{largest['group']} ({largest['staff']})" if largest and largest["staff"] else "-"},
	]
	note = "Counts every staff record (all employment statuses)." if dimension == "status" else "Counts active staff."
	return _result(columns, rows, totals=totals, summary=summary, note=note)


def _dimension_key(dimension, departments, today):
	if dimension == "lga":
		return lambda row: short_lga(row.company)
	if dimension == "department":
		return lambda row: departments.get(row.department) or row.department
	if dimension == "grade_level":
		return lambda row: (row.get(EMPLOYEE_GRADE_FIELD) or "").strip().upper()
	if dimension == "grade_band":
		return lambda row: _grade_band(row.get(EMPLOYEE_GRADE_FIELD))
	if dimension == "age_band":
		return lambda row: _band(_years(row.date_of_birth, today), AGE_BANDS) if row.date_of_birth else None
	if dimension == "service_band":
		return lambda row: _band(_years(_appointment_date(row), today), SERVICE_BANDS) if _appointment_date(row) else None
	if dimension == "rank":
		return lambda row: (row.dtmgp_rank or "").strip()
	return lambda row: row.get(dimension)


def _dimension_order(dimension, groups):
	labels = set(groups)
	fixed = {
		"age_band": [label for _low, _high, label in AGE_BANDS],
		"service_band": [label for _low, _high, label in SERVICE_BANDS],
		"grade_band": [label for _low, _high, label in GRADE_BANDS],
		"status": list(STATUSES),
	}.get(dimension)
	if fixed:
		return [*fixed, *sorted(labels - set(fixed), key=lambda label: (label == UNSPECIFIED, label))]
	if dimension == "grade_level":
		return sorted(labels, key=_grade_sort_key)
	return sorted(labels, key=lambda label: (label == UNSPECIFIED, -len(groups[label]), label))


# --------------------------------------------------------------------------- Retirement forecast


def retirement_forecast(companies, params):
	months = cint(params.get("months") or 24)
	if months not in RETIREMENT_HORIZONS:
		frappe.throw(f"Unknown forecast horizon: {months} months")
	today = getdate(nowdate())
	horizon = getdate(add_months(today, months))
	filters = {"company": ["in", companies], "status": "Active", "date_of_retirement": ["<=", horizon]}
	if params.get("department"):
		filters["department"] = params["department"]
	records = frappe.get_all(
		"Employee", filters=filters, order_by="date_of_retirement asc", limit_page_length=MAX_ROWS,
		fields=[
			"name", "employee_name", "company", "department", "designation", EMPLOYEE_GRADE_FIELD, "date_of_birth",
			EMPLOYEE_FIRST_APPOINTMENT_FIELD, "date_of_joining", "date_of_retirement",
			EMPLOYEE_RETIRE_BY_AGE_FIELD, EMPLOYEE_RETIRE_BY_SERVICE_FIELD,
		],
	)
	departments = _department_names({row.department for row in records if row.department})
	rows = []
	for row in records:
		retirement = getdate(row.date_of_retirement)
		months_left = (retirement.year - today.year) * 12 + retirement.month - today.month
		rows.append({
			"name": row.name, "employee_name": row.employee_name, "lga": short_lga(row.company),
			"department": departments.get(row.department) or row.department, "designation": row.designation,
			"grade_level": row.get(EMPLOYEE_GRADE_FIELD), "date_of_birth": _iso(row.date_of_birth),
			"first_appointment": _iso(row.get(EMPLOYEE_FIRST_APPOINTMENT_FIELD) or row.date_of_joining),
			"date_of_retirement": _iso(retirement), "basis": _retirement_basis(row, retirement),
			"months_left": months_left, "timing": "Overdue" if retirement < today else ("Within 12 months" if months_left <= 12 else "Later"),
		})
	columns = [_col("name", "Staff ID"), _col("employee_name", "Name")]
	if len(companies) > 1:
		columns.append(_col("lga", "LGA"))
	columns += [
		_col("department", "Department"), _col("designation", "Designation"), _col("grade_level", "Grade"),
		_col("date_of_birth", "Date of birth", "date"), _col("first_appointment", "Date of 1st appt", "date"),
		_col("date_of_retirement", "Retirement date", "date"), _col("basis", "Basis"),
		_col("months_left", "Months left", "int"), _col("timing", "Timing"),
	]
	by_year = Counter(row["date_of_retirement"][:4] for row in rows if row["timing"] != "Overdue")
	summary = [
		{"label": "Overdue (still active)", "value": sum(1 for row in rows if row["timing"] == "Overdue"), "tone": "danger"},
		{"label": "Within 12 months", "value": sum(1 for row in rows if row["timing"] == "Within 12 months")},
		*([{"label": f"Within {months} months", "value": sum(1 for row in rows if row["timing"] != "Overdue")}] if months > 12 else []),
		*({"label": f"Retiring in {year}", "value": count} for year, count in sorted(by_year.items())),
	]
	note = "Overdue staff are active but past their retirement date: confirm an approved extension or process the exit."
	return _result(columns, rows, summary=summary, note=note, truncated=len(records) >= MAX_ROWS)


def _retirement_basis(row, retirement):
	by_age, by_service = row.get(EMPLOYEE_RETIRE_BY_AGE_FIELD), row.get(EMPLOYEE_RETIRE_BY_SERVICE_FIELD)
	if by_age and getdate(by_age) == retirement:
		return "Age (60 years)"
	if by_service and getdate(by_service) == retirement:
		return "Service (35 years)"
	return "Set manually"


# --------------------------------------------------------------------------- Appointments & exits


def appointments_exits(companies, params):
	start, end = _period(params)
	department = params.get("department")
	base = {"company": ["in", companies]}
	if department:
		base["department"] = department
	fields = ["name", "employee_name", "company", "department", "designation", EMPLOYEE_GRADE_FIELD]
	appointed = [
		row for row in frappe.get_all(
			"Employee", filters=base, fields=[*fields, EMPLOYEE_FIRST_APPOINTMENT_FIELD, "date_of_joining"],
		)
		if start <= getdate(row.get(EMPLOYEE_FIRST_APPOINTMENT_FIELD) or row.date_of_joining) <= end
	]
	exited = frappe.get_all(
		"Employee", filters={**base, "status": "Left", "relieving_date": ["between", [start, end]]},
		fields=[*fields, "relieving_date", "reason_for_leaving"],
	)
	transfer_filters = {"docstatus": 1, "transfer_date": ["between", [start, end]]}
	transfers_out = frappe.get_all(
		"Employee Transfer", filters={**transfer_filters, "company": ["in", companies], "new_company": ["not in", [*companies, ""]]},
		fields=["employee", "employee_name", "company", "new_company", "department", "transfer_date"],
	)
	transfers_in = frappe.get_all(
		"Employee Transfer", filters={**transfer_filters, "new_company": ["in", companies], "company": ["not in", companies]},
		fields=["employee", "employee_name", "company", "new_company", "department", "transfer_date"],
	)
	if department:
		transfers_out = [row for row in transfers_out if row.department == department]
		transfers_in = []  # The receiving department isn't recorded on the transfer.
	departments = _department_names(
		{row.department for row in [*appointed, *exited, *transfers_out, *transfers_in] if row.department}
	)

	def dept(name):
		return departments.get(name) or name

	rows = [
		*({"movement": "Appointed", "date": _iso(row.get(EMPLOYEE_FIRST_APPOINTMENT_FIELD) or row.date_of_joining), "name": row.name,
		   "employee_name": row.employee_name, "lga": short_lga(row.company), "department": dept(row.department),
		   "designation": row.designation, "grade_level": row.get(EMPLOYEE_GRADE_FIELD), "detail": None} for row in appointed),
		*({"movement": "Exited", "date": _iso(row.relieving_date), "name": row.name, "employee_name": row.employee_name,
		   "lga": short_lga(row.company), "department": dept(row.department), "designation": row.designation,
		   "grade_level": row.get(EMPLOYEE_GRADE_FIELD), "detail": row.reason_for_leaving} for row in exited),
		*({"movement": "Transferred out", "date": _iso(row.transfer_date), "name": row.employee, "employee_name": row.employee_name,
		   "lga": short_lga(row.company), "department": dept(row.department), "designation": None, "grade_level": None,
		   "detail": f"To {short_lga(row.new_company)}"} for row in transfers_out),
		*({"movement": "Transferred in", "date": _iso(row.transfer_date), "name": row.employee, "employee_name": row.employee_name,
		   "lga": short_lga(row.new_company), "department": None, "designation": None, "grade_level": None,
		   "detail": f"From {short_lga(row.company)}"} for row in transfers_in),
	]
	rows.sort(key=lambda row: (row["date"] or "", row["movement"], row["employee_name"] or ""), reverse=True)
	columns = [_col("date", "Date", "date"), _col("movement", "Movement"), _col("name", "Staff ID"), _col("employee_name", "Name")]
	if len(companies) > 1:
		columns.append(_col("lga", "LGA"))
	columns += [_col("department", "Department"), _col("designation", "Designation"), _col("grade_level", "Grade"), _col("detail", "Details")]
	gained, lost = len(appointed) + len(transfers_in), len(exited) + len(transfers_out)
	summary = [
		{"label": "Appointed", "value": len(appointed)},
		{"label": "Exited", "value": len(exited)},
		{"label": "Transferred in / out", "value": f"{len(transfers_in)} / {len(transfers_out)}"},
		{"label": "Net change", "value": f"{gained - lost:+d}"},
	]
	note = f"{_display(start)} to {_display(end)}. Appointment uses Date of 1st APPT (Date of Joining when blank); exits use the relieving date."
	return _result(columns, rows[:MAX_ROWS], summary=summary, note=note, truncated=len(rows) > MAX_ROWS)


# --------------------------------------------------------------------------- Leave


def leave_report(companies, params):
	start, end = _period(params)
	group_by = _choice(params.get("group_by"), LEAVE_GROUPS, "leave_type", "grouping")
	filters = {
		"company": ["in", companies], "docstatus": ["!=", 2], "status": ["!=", "Cancelled"],
		"from_date": ["<=", end], "to_date": [">=", start],
	}
	if params.get("department"):
		filters["department"] = params["department"]
	applications = frappe.get_all(
		"Leave Application", filters=filters,
		fields=["employee", "leave_type", "department", "company", "from_date", "to_date", "total_leave_days", "status", "docstatus"],
	)
	departments = _department_names({row.department for row in applications if row.department})
	key = {
		"leave_type": lambda row: row.leave_type,
		"department": lambda row: departments.get(row.department) or row.department or UNSPECIFIED,
		"month": lambda row: getdate(row.from_date).strftime("%Y-%m"),
		"lga": lambda row: short_lga(row.company),
	}[group_by]
	groups = defaultdict(list)
	for row in applications:
		groups[key(row)].append(row)

	def measure(members):
		approved = [row for row in members if row.status == "Approved" and row.docstatus == 1]
		return {
			"applications": len(members), "approved": len(approved),
			"rejected": sum(1 for row in members if row.status == "Rejected"),
			"open": sum(1 for row in members if row.status == "Open"),
			"days": round(sum(float(row.total_leave_days or 0) for row in approved), 1),
			"staff": len({row.employee for row in approved}),
		}

	order = sorted(groups, reverse=True) if group_by == "month" else sorted(groups, key=lambda label: (-len(groups[label]), label))
	rows = [{"group": label, **measure(groups[label])} for label in order]
	totals = {"group": "Total", **measure(applications)}
	today = getdate(nowdate())
	on_leave_today = len({
		row.employee for row in applications
		if row.status == "Approved" and row.docstatus == 1 and getdate(row.from_date) <= today <= getdate(row.to_date)
	})
	columns = [
		_col("group", LEAVE_GROUPS[group_by]), _col("applications", "Applications", "int"), _col("approved", "Approved", "int"),
		_col("rejected", "Rejected", "int"), _col("open", "Awaiting decision", "int"), _col("days", "Days approved", "years"),
		_col("staff", "Staff on approved leave", "int"),
	]
	summary = [
		{"label": "Applications", "value": totals["applications"]},
		{"label": "Days approved", "value": totals["days"]},
		{"label": "Awaiting decision", "value": totals["open"]},
		{"label": "On leave today", "value": on_leave_today},
	]
	note = f"Leave overlapping {_display(start)} to {_display(end)}; cancelled applications are excluded."
	return _result(columns, rows, totals=totals, summary=summary, note=note)


# --------------------------------------------------------------------------- Establishment


def establishment_report(companies, params):
	plans = frappe.get_all(
		"Staffing Plan", filters={"company": ["in", companies], "docstatus": 1},
		fields=["name", "company", "department", "from_date", "to_date"],
	)
	if params.get("department"):
		plans = [plan for plan in plans if plan.department == params["department"]]
	by_plan = {plan.name: plan for plan in plans}
	details = frappe.get_all(
		"Staffing Plan Detail", filters={"parent": ["in", list(by_plan) or [""]]},
		fields=["parent", "designation", "number_of_positions", "current_count", "vacancies"],
	)
	departments = _department_names({plan.department for plan in plans if plan.department})
	rows = []
	for detail in details:
		plan = by_plan[detail.parent]
		approved, filled = cint(detail.number_of_positions), cint(detail.current_count)
		status = "Vacant" if filled == 0 and approved else (
			"Overstaffed" if filled > approved else ("Filled" if filled == approved else "Partially filled")
		)
		rows.append({
			"lga": short_lga(plan.company), "department": departments.get(plan.department) or plan.department or UNSPECIFIED,
			"designation": detail.designation, "plan": plan.name, "period": f"{_display(plan.from_date)} - {_display(plan.to_date)}",
			"approved": approved, "filled": filled, "gap": approved - filled,
			"fill_pct": _pct(filled, approved), "status": status,
		})
	rows.sort(key=lambda row: (row["lga"], row["department"], row["designation"] or ""))
	approved, filled = sum(row["approved"] for row in rows), sum(row["filled"] for row in rows)
	totals = {"lga": "Total", "department": "Total", "approved": approved, "filled": filled, "gap": approved - filled, "fill_pct": _pct(filled, approved)}
	columns = []
	if len(companies) > 1:
		columns.append(_col("lga", "LGA"))
	columns += [
		_col("department", "Department"), _col("designation", "Designation"), _col("plan", "Staffing plan"), _col("period", "Period"),
		_col("approved", "Approved", "int"), _col("filled", "Filled", "int"), _col("gap", "Vacancies (+) / excess (-)", "int"),
		_col("fill_pct", "Filled %", "pct"), _col("status", "Status"),
	]
	summary = [
		{"label": "Approved positions", "value": approved},
		{"label": "Filled", "value": filled},
		{"label": "Fill rate", "value": _pct(filled, approved), "unit": "pct"},
		{"label": "Vacant posts", "value": sum(1 for row in rows if row["status"] == "Vacant")},
		{"label": "Overstaffed posts", "value": sum(1 for row in rows if row["status"] == "Overstaffed"), "tone": "danger"},
	]
	note = None if rows else "No submitted staffing plans in scope. Create one under Establishment Control."
	return _result(columns, rows, totals=totals if rows else None, summary=summary, note=note)


# --------------------------------------------------------------------------- Verification


def verification_report(companies, params):
	group_by = _choice(params.get("group_by"), GROUP_LABELS, _default_group(companies), "grouping")
	employees = _active(_scoped_employees(companies, params))
	departments = _department_names({row.department for row in employees if row.department})
	key = _group_key(group_by, departments)
	groups = defaultdict(list)
	for row in employees:
		groups[key(row)].append(row)
	if group_by == "lga":
		for company in companies:
			groups.setdefault(short_lga(company), [])

	def measure(members):
		states = Counter(row.get(EMPLOYEE_VERIFICATION_FIELD) or "Pending" for row in members)
		return {
			"active": len(members), "verified": states.get("Verified", 0), "pending": states.get("Pending", 0),
			"review_due": states.get("Review Due", 0), "verified_pct": _pct(states.get("Verified", 0), len(members)),
		}

	rows = [{"group": label, **measure(groups[label])} for label in _group_order(group_by, groups)]
	rows.sort(key=lambda row: (row["verified_pct"], row["group"]))
	totals = {"group": "Total", **measure(employees)}
	columns = [
		_col("group", GROUP_LABELS[group_by]), _col("active", "Active staff", "int"), _col("verified", "Verified", "int"),
		_col("pending", "Pending", "int"), _col("review_due", "Review due", "int"), _col("verified_pct", "Verified %", "pct"),
	]
	summary = [
		{"label": "Verified", "value": totals["verified_pct"], "unit": "pct"},
		{"label": "Pending", "value": totals["pending"]},
		{"label": "Review due", "value": totals["review_due"]},
	]
	return _result(columns, rows, totals=totals, summary=summary, note="Active staff, lowest verification rate first.")


# --------------------------------------------------------------------------- Records completeness


def records_completeness(companies, params):
	group_by = _choice(params.get("group_by"), GROUP_LABELS, _default_group(companies), "grouping")
	employees = _active(_scoped_employees(companies, params))
	departments = _department_names({row.department for row in employees if row.department})
	key = _group_key(group_by, departments)
	groups = defaultdict(list)
	for row in employees:
		groups[key(row)].append(row)
	checks = [*COMPLETENESS, ("has_grade", "Grade level")]
	for row in employees:
		row["has_grade"] = bool((row.get(EMPLOYEE_GRADE_FIELD) or "").strip())

	def measure(members):
		values = {f"{flag[4:]}_pct": _pct(sum(1 for row in members if row[flag]), len(members)) for flag, _label in checks}
		complete = sum(1 for row in members if all(row[flag] for flag, _label in checks))
		return {"active": len(members), **values, "complete_pct": _pct(complete, len(members))}

	rows = [{"group": label, **measure(groups[label])} for label in _group_order(group_by, groups)]
	rows.sort(key=lambda row: (row["complete_pct"], row["group"]))
	totals = {"group": "Total", **measure(employees)}
	columns = [
		_col("group", GROUP_LABELS[group_by]), _col("active", "Active staff", "int"),
		*(_col(f"{flag[4:]}_pct", label, "pct") for flag, label in checks),
		_col("complete_pct", "Fully complete", "pct"),
	]
	weakest = min(((label, totals[f"{flag[4:]}_pct"]) for flag, label in checks), key=lambda item: item[1], default=None)
	summary = [
		{"label": "Fully complete records", "value": totals["complete_pct"], "unit": "pct"},
		{"label": "Least captured", "value": f"{weakest[0]} ({weakest[1]}%)" if weakest and employees else "-"},
		{"label": "Active staff", "value": totals["active"]},
	]
	note = "Share of active staff with each item captured, least complete first. Values themselves (BVN, NIN, account numbers) are never shown."
	return _result(columns, rows, totals=totals, summary=summary, note=note)


# --------------------------------------------------------------------------- Registry

REPORTS = {
	"nominal-roll": nominal_roll,
	"staff-strength": staff_strength,
	"staff-distribution": staff_distribution,
	"retirement-forecast": retirement_forecast,
	"appointments-exits": appointments_exits,
	"leave": leave_report,
	"establishment": establishment_report,
	"verification": verification_report,
	"records-completeness": records_completeness,
}


def run_report(report, companies, params):
	if report not in REPORTS:
		frappe.throw(f"Unknown HR report: {report}")
	if not companies:
		return _result([], [], note="No LGA in scope.")
	return REPORTS[report](companies, {key: value for key, value in params.items() if value not in (None, "")})


def _iso(value):
	return str(getdate(value)) if value else None


def _display(value):
	return getdate(value).strftime("%d %b %Y") if value else "-"


def as_table(result):
	"""Column labels and row values (totals last) for CSV export."""
	keys = [column["key"] for column in result["columns"]]
	rows = [[row.get(key) for key in keys] for row in result["rows"]]
	if result.get("totals"):
		rows.append([result["totals"].get(key) for key in keys])
	return [column["label"] for column in result["columns"]], rows

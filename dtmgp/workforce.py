"""Workforce (employee) dashboard aggregates shared by the desk Employee Dashboard
workspace charts and the Vue Workforce Dashboard.

Callers MUST pass a company list already resolved through
``get_requested_companies`` — this module never widens scope on its own, and an
empty list always yields an empty summary rather than a statewide one."""

import re

import frappe
from frappe.utils import add_months, cint, date_diff, getdate, nowdate

from dtmgp.setup.organization import PARENT_COMPANY
from dtmgp.setup.security import EMPLOYEE_FIRST_APPOINTMENT_FIELD, EMPLOYEE_GRADE_FIELD, EMPLOYEE_VERIFICATION_FIELD

AGE_BANDS = ((0, 25, "Under 25"), (25, 35, "25 - 34"), (35, 45, "35 - 44"), (45, 55, "45 - 54"), (55, 60, "55 - 59"), (60, 200, "60 and above"))
STATUS_ORDER = ("Active", "Suspended", "Inactive", "Left")
VERIFICATION_ORDER = ("Verified", "Pending", "Review Due")
TOP_DEPARTMENTS = 10
TREND_YEARS = 10
UNSPECIFIED = "Not specified"

BREAKDOWNS = (
	"lga", "status", "gender", "grade_level", "verification", "age_band",
	"department", "retirements_by_year", "appointments_by_year",
)

_FIELDS = (
	"name", "company", "status", "gender", "department", "date_of_birth", "date_of_joining",
	"date_of_retirement", EMPLOYEE_GRADE_FIELD, EMPLOYEE_VERIFICATION_FIELD, EMPLOYEE_FIRST_APPOINTMENT_FIELD,
)


def short_lga(company):
	return (company or "").replace(" Local Government Area", " LGA").replace(PARENT_COMPANY, "State HQ")


def get_workforce_summary(companies):
	"""Totals plus every breakdown, for the companies the caller is allowed to see."""
	employees = _employees(companies)
	active = [row for row in employees if row.status == "Active"]
	today = getdate(nowdate())
	horizon = getdate(add_months(today, 12))
	verified = sum(1 for row in active if row.get(EMPLOYEE_VERIFICATION_FIELD) == "Verified")
	return {
		"scope": {"companies": len(companies), "is_statewide": len(companies) > 1},
		"totals": {
			"total": len(employees),
			"active": len(active),
			"left": sum(1 for row in employees if row.status == "Left"),
			"verified": verified,
			"pending_verification": len(active) - verified,
			"retiring_12m": sum(1 for row in active if row.date_of_retirement and today <= getdate(row.date_of_retirement) <= horizon),
			"past_retirement": sum(1 for row in active if row.date_of_retirement and getdate(row.date_of_retirement) < today),
			"joined_this_year": sum(1 for row in employees if _appointment_date(row) and _appointment_date(row).year == today.year),
			"average_age": _average_age(active, today),
		},
		"breakdowns": {name: _breakdown(name, employees, active, today) for name in BREAKDOWNS},
	}


def get_breakdown(name, companies):
	"""A single breakdown as ``[{"label", "value"}]`` (for one desk chart)."""
	if name not in BREAKDOWNS:
		frappe.throw("Unknown workforce breakdown")
	employees = _employees(companies)
	return _breakdown(name, employees, [row for row in employees if row.status == "Active"], getdate(nowdate()))


def _employees(companies):
	if not companies:
		return []
	return frappe.get_all("Employee", filters={"company": ["in", companies]}, fields=list(_FIELDS))


def _breakdown(name, employees, active, today):
	if name == "lga":
		counts = _count(active, lambda row: row.company)
		verified = _count([row for row in active if row.get(EMPLOYEE_VERIFICATION_FIELD) == "Verified"], lambda row: row.company)
		rows = [{"label": short_lga(company), "company": company, "value": value, "verified": verified.get(company, 0)} for company, value in counts.items()]
		return sorted(rows, key=lambda row: (-row["value"], row["label"]))
	if name == "status":
		return _ordered(_count(employees, lambda row: row.status), STATUS_ORDER)
	if name == "gender":
		return _sorted_desc(_count(active, lambda row: row.gender))
	if name == "grade_level":
		counts = _count(active, lambda row: (row.get(EMPLOYEE_GRADE_FIELD) or "").strip().upper())
		return [{"label": label, "value": counts[label]} for label in sorted(counts, key=_grade_sort_key)]
	if name == "verification":
		return _ordered(_count(active, lambda row: row.get(EMPLOYEE_VERIFICATION_FIELD) or "Pending"), VERIFICATION_ORDER)
	if name == "age_band":
		counts = _count([row for row in active if row.date_of_birth], lambda row: _age_band(row.date_of_birth, today))
		return [{"label": label, "value": counts.get(label, 0)} for _low, _high, label in AGE_BANDS]
	if name == "department":
		names = _department_names({row.department for row in active if row.department})
		rows = _sorted_desc(_count(active, lambda row: names.get(row.department) or row.department))
		if len(rows) > TOP_DEPARTMENTS:
			rest = sum(row["value"] for row in rows[TOP_DEPARTMENTS - 1:])
			rows = [*rows[: TOP_DEPARTMENTS - 1], {"label": "All other departments", "value": rest}]
		return rows
	if name == "retirements_by_year":
		years = [today.year + offset for offset in range(TREND_YEARS)]
		counts = _count([row for row in active if row.date_of_retirement], lambda row: getdate(row.date_of_retirement).year)
		overdue = sum(value for year, value in counts.items() if year < today.year)
		rows = [{"label": str(year), "value": counts.get(year, 0)} for year in years]
		return [{"label": "Overdue", "value": overdue}, *rows] if overdue else rows
	if name == "appointments_by_year":
		years = [today.year - offset for offset in reversed(range(TREND_YEARS))]
		counts = _count([row for row in employees if _appointment_date(row)], lambda row: _appointment_date(row).year)
		return [{"label": str(year), "value": counts.get(year, 0)} for year in years]
	return []


def _count(rows, key):
	counts = {}
	for row in rows:
		label = key(row) or UNSPECIFIED
		counts[label] = counts.get(label, 0) + 1
	return counts


def _sorted_desc(counts):
	return [{"label": label, "value": value} for label, value in sorted(counts.items(), key=lambda item: (-item[1], str(item[0])))]


def _ordered(counts, order):
	known = [{"label": label, "value": counts[label]} for label in order if counts.get(label)]
	return known + _sorted_desc({label: value for label, value in counts.items() if label not in order})


def _grade_sort_key(label):
	match = re.search(r"\d+", label or "")
	return (label == UNSPECIFIED, cint(match.group()) if match else 999, label)


def _age_band(date_of_birth, today):
	age = date_diff(today, date_of_birth) // 365.25
	for low, high, label in AGE_BANDS:
		if low <= age < high:
			return label
	return AGE_BANDS[-1][2]


def _average_age(rows, today):
	ages = [date_diff(today, row.date_of_birth) / 365.25 for row in rows if row.date_of_birth]
	return round(sum(ages) / len(ages), 1) if ages else None


def _appointment_date(row):
	value = row.get(EMPLOYEE_FIRST_APPOINTMENT_FIELD) or row.date_of_joining
	return getdate(value) if value else None


def _department_names(departments):
	"""ERPNext Department names carry the per-company abbreviation ("Works - ADO");
	group by the bare department_name so a statewide view reads as one 'Works'."""
	if not departments:
		return {}
	return dict(frappe.get_all("Department", filters={"name": ["in", list(departments)]}, fields=["name", "department_name"], as_list=True))

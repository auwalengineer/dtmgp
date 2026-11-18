"""Workforce (employee) dashboard aggregates shared by the desk Employee Dashboard
workspace (charts + LGA comparison report) and the Vue Employee Dashboard.

Callers MUST pass a company list already resolved through
``get_requested_companies`` — this module never widens scope on its own, and an
empty list always yields an empty summary rather than a statewide one.

Sensitive values (BVN, NIN, bank account number) are read only to test whether
they are captured; they are reduced to booleans in ``_employees`` and never
leave this module."""

import re

import frappe
from frappe.utils import add_months, cint, date_diff, flt, getdate, nowdate

from dtmgp.setup.organization import PARENT_COMPANY
from dtmgp.setup.security import (
	EMPLOYEE_BVN_FIELD,
	EMPLOYEE_FIRST_APPOINTMENT_FIELD,
	EMPLOYEE_GRADE_FIELD,
	EMPLOYEE_NIN_FIELD,
	EMPLOYEE_VERIFICATION_FIELD,
)

AGE_BANDS = ((0, 25, "Under 25"), (25, 35, "25 - 34"), (35, 45, "35 - 44"), (45, 55, "45 - 54"), (55, 60, "55 - 59"), (60, 200, "60 and above"))
SERVICE_BANDS = ((0, 5, "Under 5 years"), (5, 10, "5 - 9 years"), (10, 20, "10 - 19 years"), (20, 30, "20 - 29 years"), (30, 35, "30 - 34 years"), (35, 200, "35+ years"))
# Nigerian public service cadres by grade level.
GRADE_BANDS = ((1, 6, "Junior (GL 01-06)"), (7, 12, "Senior (GL 07-12)"), (13, 17, "Management (GL 13-17)"))
STATUS_ORDER = ("Active", "Suspended", "Inactive", "Left")
VERIFICATION_ORDER = ("Verified", "Pending", "Review Due")
SALARY_MODE_ORDER = ("Bank", "Cash", "Cheque")
TOP_N = 10
TREND_YEARS = 10
UNSPECIFIED = "Not specified"

BREAKDOWNS = (
	"lga", "status", "gender", "grade_level", "grade_band", "verification", "age_band", "service_band",
	"department", "designation", "rank", "salary_mode", "data_completeness",
	"retirements_by_year", "appointments_by_year",
)
# Per-LGA comparison metrics: (key, label, unit). "pct" values are 0-100.
COMPARISON_METRICS = (
	("active", "Active staff", "count"),
	("share_pct", "Share of active staff", "pct"),
	("verified_pct", "Verified", "pct"),
	("female_pct", "Female", "pct"),
	("average_age", "Average age", "years"),
	("average_service", "Average years of service", "years"),
	("retiring_12m", "Retiring in 12 months", "count"),
	("past_retirement", "Active past retirement date", "count"),
	("joined_this_year", "Appointed this year", "count"),
	("left", "Exited", "count"),
	("bvn_pct", "BVN captured", "pct"),
	("nin_pct", "NIN captured", "pct"),
	("photo_pct", "Photo captured", "pct"),
	("bank_pct", "Bank details captured", "pct"),
	("management_pct", "Management cadre (GL 13+)", "pct"),
)
COMPLETENESS = (
	("has_bvn", "BVN"), ("has_nin", "NIN"), ("has_photo", "Photo"), ("has_bank", "Bank details"),
	("has_phone", "Phone number"), ("has_first_appointment", "Date of 1st appointment"),
)

_FIELDS = (
	"name", "company", "status", "gender", "department", "designation", "date_of_birth", "date_of_joining",
	"date_of_retirement", "image", "salary_mode", "bank_ac_no", "cell_number", "dtmgp_rank",
	EMPLOYEE_GRADE_FIELD, EMPLOYEE_VERIFICATION_FIELD, EMPLOYEE_FIRST_APPOINTMENT_FIELD, EMPLOYEE_BVN_FIELD, EMPLOYEE_NIN_FIELD,
)


def short_lga(company):
	return (company or "").replace(" Local Government Area", " LGA").replace(PARENT_COMPANY, "State HQ")


def get_workforce_summary(companies):
	"""Totals, every breakdown and the per-LGA comparison for the caller's scope."""
	today = getdate(nowdate())
	employees = _employees(companies)
	active = _active(employees)
	return {
		"scope": {"companies": len(companies), "is_statewide": len(companies) > 1},
		"totals": _totals(employees, active, today),
		"breakdowns": {name: _breakdown(name, employees, active, today) for name in BREAKDOWNS},
		"lga_comparison": get_lga_comparison(companies, employees=employees, today=today),
		"comparison_metrics": [{"key": key, "label": label, "unit": unit} for key, label, unit in COMPARISON_METRICS],
	}


def get_breakdown(name, companies):
	"""A single breakdown as ``[{"label", "value", ...}]`` (for one desk chart)."""
	if name not in BREAKDOWNS:
		frappe.throw("Unknown workforce breakdown")
	employees = _employees(companies)
	return _breakdown(name, employees, _active(employees), getdate(nowdate()))


def get_lga_comparison(companies, employees=None, today=None):
	"""One row per LGA in scope — including LGAs with no staff yet, so gaps show —
	sorted by active staff (largest first)."""
	today = today or getdate(nowdate())
	employees = _employees(companies) if employees is None else employees
	total_active = len(_active(employees))
	by_company = {company: [] for company in companies}
	for row in employees:
		by_company.setdefault(row.company, []).append(row)
	rows = []
	for company, members in by_company.items():
		active = _active(members)
		totals = _totals(members, active, today)
		grade = {label: 0 for _low, _high, label in GRADE_BANDS}
		for row in active:
			band = _grade_band(row.get(EMPLOYEE_GRADE_FIELD))
			if band in grade:
				grade[band] += 1
		rows.append({
			"company": company,
			"label": short_lga(company),
			**{key: totals[key] for key in (
				"total", "active", "left", "verified", "pending_verification", "retiring_12m", "past_retirement",
				"joined_this_year", "average_age", "average_service", "male", "female",
			)},
			"share_pct": _pct(totals["active"], total_active),
			"verified_pct": _pct(totals["verified"], totals["active"]),
			"female_pct": _pct(totals["female"], totals["male"] + totals["female"]),
			"management_pct": _pct(grade[GRADE_BANDS[-1][2]], totals["active"]),
			"grade_bands": grade,
			**{f"{key[4:]}_pct": _pct(sum(1 for row in active if row[key]), len(active)) for key, _label in COMPLETENESS},
		})
	return sorted(rows, key=lambda row: (-row["active"], row["label"]))


def _totals(employees, active, today):
	horizon = getdate(add_months(today, 12))
	verified = sum(1 for row in active if row.get(EMPLOYEE_VERIFICATION_FIELD) == "Verified")
	return {
		"total": len(employees),
		"active": len(active),
		"left": sum(1 for row in employees if row.status == "Left"),
		"suspended_or_inactive": sum(1 for row in employees if row.status in ("Suspended", "Inactive")),
		"verified": verified,
		"pending_verification": len(active) - verified,
		"male": sum(1 for row in active if row.gender == "Male"),
		"female": sum(1 for row in active if row.gender == "Female"),
		"retiring_12m": sum(1 for row in active if row.date_of_retirement and today <= getdate(row.date_of_retirement) <= horizon),
		"retiring_5y": sum(1 for row in active if row.date_of_retirement and today <= getdate(row.date_of_retirement) <= getdate(add_months(today, 60))),
		"past_retirement": sum(1 for row in active if row.date_of_retirement and getdate(row.date_of_retirement) < today),
		"joined_this_year": sum(1 for row in employees if _appointment_date(row) and _appointment_date(row).year == today.year),
		"average_age": _average([_years(row.date_of_birth, today) for row in active if row.date_of_birth]),
		"average_service": _average([_years(_appointment_date(row), today) for row in active if _appointment_date(row)]),
		"completeness": {key[4:]: _pct(sum(1 for row in active if row[key]), len(active)) for key, _label in COMPLETENESS},
	}


def _employees(companies):
	if not companies:
		return []
	rows = frappe.get_all("Employee", filters={"company": ["in", companies]}, fields=list(_FIELDS))
	for row in rows:
		# Reduce sensitive values to "is it captured?" immediately.
		row["has_bvn"] = bool(row.pop(EMPLOYEE_BVN_FIELD, None))
		row["has_nin"] = bool(row.pop(EMPLOYEE_NIN_FIELD, None))
		row["has_bank"] = bool(row.pop("bank_ac_no", None))
		row["has_photo"] = bool(row.pop("image", None))
		row["has_phone"] = bool(row.pop("cell_number", None))
		row["has_first_appointment"] = bool(row.get(EMPLOYEE_FIRST_APPOINTMENT_FIELD))
	return rows


def _active(rows):
	return [row for row in rows if row.status == "Active"]


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
	if name == "grade_band":
		counts = _count(active, lambda row: _grade_band(row.get(EMPLOYEE_GRADE_FIELD)))
		return _ordered(counts, [label for _low, _high, label in GRADE_BANDS])
	if name == "verification":
		return _ordered(_count(active, lambda row: row.get(EMPLOYEE_VERIFICATION_FIELD) or "Pending"), VERIFICATION_ORDER)
	if name == "age_band":
		counts = _count([row for row in active if row.date_of_birth], lambda row: _band(_years(row.date_of_birth, today), AGE_BANDS))
		return [{"label": label, "value": counts.get(label, 0)} for _low, _high, label in AGE_BANDS]
	if name == "service_band":
		counts = _count([row for row in active if _appointment_date(row)], lambda row: _band(_years(_appointment_date(row), today), SERVICE_BANDS))
		return [{"label": label, "value": counts.get(label, 0)} for _low, _high, label in SERVICE_BANDS]
	if name == "department":
		names = _department_names({row.department for row in active if row.department})
		return _top(_sorted_desc(_count(active, lambda row: names.get(row.department) or row.department)), "departments")
	if name == "designation":
		return _top(_sorted_desc(_count(active, lambda row: row.designation)), "designations")
	if name == "rank":
		return _top(_sorted_desc(_count(active, lambda row: (row.dtmgp_rank or "").strip())), "ranks")
	if name == "salary_mode":
		return _ordered(_count(active, lambda row: row.salary_mode), SALARY_MODE_ORDER)
	if name == "data_completeness":
		# value = % of active staff with the item captured; count kept for tooltips/tables.
		return [
			{"label": label, "value": _pct(sum(1 for row in active if row[key]), len(active)), "count": sum(1 for row in active if row[key])}
			for key, label in COMPLETENESS
		]
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


def _top(rows, noun):
	if len(rows) <= TOP_N:
		return rows
	rest = sum(row["value"] for row in rows[TOP_N - 1:])
	return [*rows[: TOP_N - 1], {"label": f"All other {noun}", "value": rest}]


def _grade_number(label):
	match = re.search(r"\d+", label or "")
	return cint(match.group()) if match else None


def _grade_sort_key(label):
	number = _grade_number(label)
	return (label == UNSPECIFIED, number if number is not None else 999, label)


def _grade_band(label):
	number = _grade_number(label)
	for low, high, band in GRADE_BANDS:
		if number is not None and low <= number <= high:
			return band
	return UNSPECIFIED


def _years(start, today):
	return date_diff(today, start) / 365.25 if start else None


def _band(years, bands):
	for low, high, label in bands:
		if low <= years < high:
			return label
	return bands[-1][2] if years >= bands[-1][0] else bands[0][2]


def _average(values):
	values = [value for value in values if value is not None]
	return round(sum(values) / len(values), 1) if values else None


def _pct(part, whole):
	return round(flt(part) * 100 / whole, 1) if whole else 0


def _appointment_date(row):
	value = row.get(EMPLOYEE_FIRST_APPOINTMENT_FIELD) or row.date_of_joining
	return getdate(value) if value else None


def _department_names(departments):
	"""ERPNext Department names carry the per-company abbreviation ("Works - ADO");
	group by the bare department_name so a statewide view reads as one 'Works'."""
	if not departments:
		return {}
	return dict(frappe.get_all("Department", filters={"name": ["in", list(departments)]}, fields=["name", "department_name"], as_list=True))

import frappe

from dtmgp.permissions.scope import get_requested_companies, require_hr_access
from dtmgp.workforce import GRADE_BANDS, get_breakdown, get_lga_comparison

# Dashboard Chart name -> workforce breakdown. The chart (not a user-editable
# filter) decides the breakdown, so a saved per-user filter can't drop it.
CHART_BREAKDOWNS = {
	"Workforce by LGA": "lga",
	"Workforce by Status": "status",
	"Workforce by Gender": "gender",
	"Workforce by Grade Level": "grade_level",
	"Workforce by Grade Band": "grade_band",
	"Workforce Verification Status": "verification",
	"Workforce by Age Band": "age_band",
	"Workforce by Years of Service": "service_band",
	"Workforce by Department": "department",
	"Workforce by Designation": "designation",
	"Workforce Data Completeness": "data_completeness",
	"Upcoming Retirements by Year": "retirements_by_year",
	"Appointments by Year": "appointments_by_year",
}
DATASET_NAMES = {
	"status": "Staff", "retirements_by_year": "Retirements", "appointments_by_year": "Appointments",
	"data_completeness": "% of active staff",
}
# LGA comparison charts: one bar group per LGA, one dataset per (label, row getter).
COMPARISON_CHARTS = {
	"Workforce LGA Comparison": [("Active staff", "active"), ("Verified", "verified"), ("Retiring in 12 months", "retiring_12m")],
	"Workforce Gender by LGA": [("Male", "male"), ("Female", "female")],
	"Workforce Grade Band by LGA": [(label, lambda row, label=label: row["grade_bands"][label]) for _low, _high, label in GRADE_BANDS],
	"Workforce Verification Rate by LGA": [("Verified %", "verified_pct")],
	"Workforce Records Completeness by LGA": [("BVN %", "bvn_pct"), ("NIN %", "nin_pct"), ("Photo %", "photo_pct"), ("Bank details %", "bank_pct")],
	"Workforce Average Age by LGA": [("Average age", "average_age")],
}


@frappe.whitelist()
def get_data(
	chart_name=None,
	chart=None,
	no_cache=None,
	filters=None,
	from_date=None,
	to_date=None,
	timespan=None,
	time_interval=None,
	heatmap_year=None,
	refresh=None,
):
	# Deliberately NOT wrapped in frappe.utils.dashboard.cache_source: that caches by
	# chart name for every user, which would serve one scope's (e.g. statewide)
	# aggregate to an LGA-scoped user. Scope is re-derived per request instead.
	require_hr_access()
	name = chart_name or (frappe.parse_json(chart) or {}).get("name")
	if name not in CHART_BREAKDOWNS and name not in COMPARISON_CHARTS:
		frappe.throw("Unknown workforce chart")
	filters = frappe.parse_json(filters) if filters else {}
	company = filters.get("company") if isinstance(filters, dict) else None
	companies = get_requested_companies(company or None)

	if name in COMPARISON_CHARTS:
		rows = get_lga_comparison(companies)
		return {
			"labels": [_axis_label(row["company"]) for row in rows],
			"datasets": [
				{"name": label, "values": [(getter(row) if callable(getter) else row[getter]) or 0 for row in rows]}
				for label, getter in COMPARISON_CHARTS[name]
			],
		}

	breakdown = CHART_BREAKDOWNS[name]
	rows = get_breakdown(breakdown, companies)
	datasets = [{"name": DATASET_NAMES.get(breakdown, "Active staff"), "values": [row["value"] for row in rows]}]
	if breakdown == "lga":
		datasets.append({"name": "Verified", "values": [row["verified"] for row in rows]})
	labels = [_axis_label(row["company"]) if breakdown == "lga" else row["label"] for row in rows]
	return {"labels": labels, "datasets": datasets}


def _axis_label(company):
	# Bare LGA name ("Katsina-Ala"): with 23 bars, Frappe truncates anything longer.
	return company.replace(" Local Government Area", "")

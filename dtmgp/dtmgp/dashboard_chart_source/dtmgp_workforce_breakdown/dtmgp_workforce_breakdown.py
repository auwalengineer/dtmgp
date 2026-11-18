import frappe

from dtmgp.permissions.scope import get_requested_companies, require_hr_access
from dtmgp.workforce import get_breakdown

# Dashboard Chart name -> workforce breakdown. The chart (not a user-editable
# filter) decides the breakdown, so a saved per-user filter can't drop it.
CHART_BREAKDOWNS = {
	"Workforce by LGA": "lga",
	"Workforce by Status": "status",
	"Workforce by Gender": "gender",
	"Workforce by Grade Level": "grade_level",
	"Workforce Verification Status": "verification",
	"Workforce by Age Band": "age_band",
	"Workforce by Department": "department",
	"Upcoming Retirements by Year": "retirements_by_year",
	"Appointments by Year": "appointments_by_year",
}
DATASET_NAMES = {"status": "Staff", "retirements_by_year": "Retirements", "appointments_by_year": "Appointments"}


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
	breakdown = CHART_BREAKDOWNS.get(name)
	if not breakdown:
		frappe.throw("Unknown workforce chart")
	filters = frappe.parse_json(filters) if filters else {}
	company = filters.get("company") if isinstance(filters, dict) else None
	rows = get_breakdown(breakdown, get_requested_companies(company or None))
	datasets = [{"name": DATASET_NAMES.get(breakdown, "Active staff"), "values": [row["value"] for row in rows]}]
	if breakdown == "lga":
		datasets.append({"name": "Verified", "values": [row["verified"] for row in rows]})
	return {"labels": [row["label"] for row in rows], "datasets": datasets}

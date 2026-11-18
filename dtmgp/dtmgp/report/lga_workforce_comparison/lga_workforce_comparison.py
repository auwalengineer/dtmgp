"""LGA Workforce Comparison: one row per LGA in the caller's scope with headcount,
verification, gender, age/service, retirement and records-completeness metrics.
Scope is re-derived server-side (get_requested_companies); the Report's roles only
decide who may open it."""

import frappe

from dtmgp.permissions.scope import get_requested_companies, require_hr_access
from dtmgp.workforce import GRADE_BANDS, get_lga_comparison

COLUMNS = (
	("label", "LGA", "Data", 170),
	("active", "Active staff", "Int", 100),
	("share_pct", "Share of state %", "Percent", 110),
	("verified", "Verified", "Int", 90),
	("verified_pct", "Verified %", "Percent", 95),
	("male", "Male", "Int", 70),
	("female", "Female", "Int", 75),
	("female_pct", "Female %", "Percent", 90),
	("average_age", "Avg age", "Float", 80),
	("average_service", "Avg years of service", "Float", 120),
	*[(f"grade_{index}", label, "Int", 120) for index, (_low, _high, label) in enumerate(GRADE_BANDS)],
	("retiring_12m", "Retiring in 12 months", "Int", 130),
	("past_retirement", "Active past retirement", "Int", 140),
	("joined_this_year", "Appointed this year", "Int", 120),
	("left", "Exited", "Int", 70),
	("bvn_pct", "BVN captured %", "Percent", 110),
	("nin_pct", "NIN captured %", "Percent", 110),
	("photo_pct", "Photo captured %", "Percent", 115),
	("bank_pct", "Bank details %", "Percent", 105),
)
SUMMED = ("active", "verified", "male", "female", "retiring_12m", "past_retirement", "joined_this_year", "left",
	*[f"grade_{index}" for index in range(len(GRADE_BANDS))])


def execute(filters=None):
	require_hr_access()
	filters = frappe._dict(filters or {})
	rows = get_lga_comparison(get_requested_companies(filters.get("company") or None))
	for row in rows:
		for index, (_low, _high, label) in enumerate(GRADE_BANDS):
			row[f"grade_{index}"] = row["grade_bands"][label]
	if filters.get("hide_empty"):
		rows = [row for row in rows if row["total"]]

	columns = [{"fieldname": key, "label": label, "fieldtype": fieldtype, "width": width} for key, label, fieldtype, width in COLUMNS]
	data = [{key: row.get(key) for key, *_rest in COLUMNS} for row in rows]
	if len(rows) > 1:
		data.append(_state_total(rows))

	active = sum(row["active"] for row in rows)
	verified = sum(row["verified"] for row in rows)
	with_staff = sum(1 for row in rows if row["active"])
	summary = [
		{"label": "LGAs in scope", "value": len(rows), "datatype": "Int"},
		{"label": "LGAs with active staff", "value": with_staff, "datatype": "Int", "indicator": "Red" if with_staff < len(rows) else "Green"},
		{"label": "Active staff", "value": active, "datatype": "Int", "indicator": "Blue"},
		{"label": "Verified", "value": round(verified * 100 / active, 1) if active else 0, "datatype": "Percent", "indicator": "Green"},
		{"label": "Retiring in 12 months", "value": sum(row["retiring_12m"] for row in rows), "datatype": "Int", "indicator": "Orange"},
	]
	chart = {
		"data": {
			"labels": [row["label"] for row in rows],
			"datasets": [
				{"name": "Active staff", "values": [row["active"] for row in rows]},
				{"name": "Verified", "values": [row["verified"] for row in rows]},
			],
		},
		"type": "bar",
		"colors": ["#1F7A4D", "#C8962E"],
		"barOptions": {"spaceRatio": 0.4},
	}
	return columns, data, None, chart, summary


def _state_total(rows):
	total = {key: sum(row[key] or 0 for row in rows) for key in SUMMED}
	total["label"] = "All LGAs in scope"
	total["share_pct"] = 100 if total["active"] else 0
	total["verified_pct"] = round(total["verified"] * 100 / total["active"], 1) if total["active"] else 0
	gendered = total["male"] + total["female"]
	total["female_pct"] = round(total["female"] * 100 / gendered, 1) if gendered else 0
	for key in ("average_age", "average_service", "bvn_pct", "nin_pct", "photo_pct", "bank_pct"):
		# Weight each LGA's average/percentage by its active headcount.
		weighted = [(row[key], row["active"]) for row in rows if row[key] is not None and row["active"]]
		weight = sum(count for _value, count in weighted)
		total[key] = round(sum(value * count for value, count in weighted) / weight, 1) if weight else None
	total["bold"] = 1
	return total

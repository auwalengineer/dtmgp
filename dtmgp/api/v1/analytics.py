from collections import defaultdict
from datetime import date

import frappe
from frappe.utils import add_days, add_months, flt, get_first_day, get_last_day, getdate, now_datetime, nowdate

from dtmgp.permissions.scope import (
	can_compare_lgas,
	can_view_finance,
	can_view_governance,
	can_view_hr,
	can_view_projects,
	can_view_traditional,
	get_requested_companies,
	require_analytics_access,
	get_user_roles,
)

EXPORT_ROLES = {"State Administrator", "State Executive Viewer", "State Auditor", "LGA Chairman", "LGA Secretary", "Treasurer", "Internal Auditor"}


KPI_REGISTRY = {
	"governance.actions_overdue": {"label": "Overdue actions", "domain": "governance", "source": "DTMGP Resolution Action", "format": "number", "drilldown": "/workspace/governance/resolutions/overdue-actions"},
	"governance.returns_overdue": {"label": "Overdue returns", "domain": "governance", "source": "DTMGP Statutory Return", "format": "number", "drilldown": "/workspace/governance/statutory-returns/overdue-returns"},
	"workforce.active": {"label": "Active workforce", "domain": "workforce", "source": "Employee", "format": "number", "drilldown": "/workspace/hr/staff/staff-directory"},
	"workforce.verification_rate": {"label": "Staff verified", "domain": "workforce", "source": "Employee", "format": "percent", "drilldown": "/workspace/hr/verification-biometrics/pending-verification"},
	"finance.revenue_collected": {"label": "Revenue collected", "domain": "finance", "source": "DTMGP Revenue Receipt", "format": "currency", "drilldown": "/workspace/finance/revenue/revenue-performance"},
	"finance.collection_rate": {"label": "Collection rate", "domain": "finance", "source": "DTMGP Revenue Assessment", "format": "percent", "drilldown": "/workspace/finance/revenue/revenue-performance"},
	"projects.ongoing": {"label": "Ongoing projects", "domain": "projects", "source": "Project", "format": "number", "drilldown": "/workspace/projects/projects/ongoing-projects"},
	"projects.delayed": {"label": "Delayed projects", "domain": "projects", "source": "Project", "format": "number", "drilldown": "/workspace/projects/projects/delayed-projects"},
	"traditional.open_petitions": {"label": "Open petitions", "domain": "traditional", "source": "DTMGP Chieftaincy Petition", "format": "number", "drilldown": "/workspace/traditional/petitions-disputes/petition-register"},
}


@frappe.whitelist()
def get_dashboard(company=None, from_date=None, to_date=None):
	require_analytics_access()
	companies = get_requested_companies(company)
	period = _period(from_date, to_date)
	access = _domain_access()
	metrics = _metrics(companies, period, access)
	return {
		"scope": "Statewide" if can_compare_lgas() and not company else (companies[0] if companies else "No LGA assigned"),
		"period": period,
		"generated_at": now_datetime(),
		"can_compare_lgas": can_compare_lgas(),
		"domains": access,
		"metrics": metrics,
		"completeness": _completeness(companies, access),
	}


@frappe.whitelist()
def get_scorecards(from_date=None, to_date=None):
	require_analytics_access(statewide=True)
	companies = get_requested_companies()
	period = _period(from_date, to_date)
	rows = [_scorecard(company, period) for company in companies]
	ranked = sorted((row for row in rows if row["score"] is not None), key=lambda row: row["score"], reverse=True)
	for rank, row in enumerate(ranked, 1):
		row["rank"] = rank
	return {"period": period, "rows": rows, "ranked_count": len(ranked), "unranked_count": len(rows) - len(ranked)}


@frappe.whitelist()
def get_trends(company=None, months=6):
	require_analytics_access()
	companies = get_requested_companies(company)
	months = min(max(int(months or 6), 3), 12)
	start = get_first_day(add_months(nowdate(), -(months - 1)))
	periods = []
	cursor = getdate(start)
	for _ in range(months):
		periods.append({"key": cursor.strftime("%Y-%m"), "label": cursor.strftime("%b %Y"), "revenue": 0.0, "payments": 0.0, "projects": 0, "returns": 0})
		cursor = getdate(add_months(cursor, 1))
	index = {row["key"]: row for row in periods}
	if can_view_finance():
		_accumulate(index, "DTMGP Revenue Receipt", "posting_date", companies, start, "revenue", "amount", {"docstatus": 1})
		_accumulate(index, "DTMGP Payment Request", "request_date", companies, start, "payments", "amount", {"status": "Paid"})
	if can_view_projects():
		_accumulate(index, "Project", "creation", companies, start, "projects")
	if can_view_governance():
		_accumulate(index, "DTMGP Statutory Return", "submitted_date", companies, start, "returns", filters={"status": ["in", ["Submitted", "State Reviewed"]]})
	return {"months": periods, "generated_at": now_datetime()}


@frappe.whitelist()
def get_alerts(company=None):
	require_analytics_access()
	companies = get_requested_companies(company)
	alerts = []
	if can_view_governance():
		alerts += _dated_alerts("DTMGP Resolution Action", companies, "due_date", {"status": ["!=", "Completed"]}, "Overdue resolution action", "High", "/workspace/governance/resolutions/overdue-actions")
		alerts += _dated_alerts("DTMGP Statutory Return", companies, "due_date", {"status": ["not in", ["Submitted", "State Reviewed"]]}, "Overdue statutory return", "Critical", "/workspace/governance/statutory-returns/overdue-returns")
	if can_view_projects():
		alerts += _dated_alerts("Project", companies, "expected_end_date", {"status": ["not in", ["Completed", "Cancelled"]]}, "Delayed project", "High", "/workspace/projects/projects/delayed-projects", title_field="project_name")
	if can_view_finance():
		for company_name in companies:
			assessed = _sum("DTMGP Revenue Assessment", "amount", [company_name], {"docstatus": 1})
			collected = _sum("DTMGP Revenue Receipt", "amount", [company_name], {"docstatus": 1})
			if assessed and collected / assessed < 0.6:
				alerts.append({"type": "Revenue shortfall", "severity": "High", "company": company_name, "title": "Revenue collection is below 60%", "age_days": None, "to": "/workspace/finance/revenue/revenue-performance"})
	severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
	alerts.sort(key=lambda item: (severity_order[item["severity"]], -(item["age_days"] or 0)))
	return {"items": alerts[:100], "total": len(alerts), "generated_at": now_datetime()}


@frappe.whitelist()
def get_maps(company=None):
	require_analytics_access()
	companies = get_requested_companies(company)
	if not can_view_projects():
		return {"projects": [], "inspections": [], "generated_at": now_datetime()}
	projects = frappe.get_all("Project", filters={"company": ["in", companies], "dtmgp_location": ["is", "set"]}, fields=["name", "project_name as label", "company", "status", "dtmgp_location"])
	for project in projects:
		location = frappe.db.get_value("Location", project.dtmgp_location, ["latitude", "longitude"], as_dict=True)
		project.update({"latitude": location.latitude if location else None, "longitude": location.longitude if location else None})
	inspections = frappe.get_all("DTMGP Project Inspection", filters={"company": ["in", companies], "latitude": ["is", "set"], "longitude": ["is", "set"]}, fields=["name", "project as label", "company", "status", "latitude", "longitude"])
	return {"projects": [item for item in projects if item.latitude and item.longitude], "inspections": [item for item in inspections if item.latitude and item.longitude], "generated_at": now_datetime()}


@frappe.whitelist(methods=["POST"])
def export_executive_summary(purpose, company=None, from_date=None, to_date=None):
	require_analytics_access()
	if frappe.session.user != "Administrator" and not get_user_roles().intersection(EXPORT_ROLES):
		frappe.throw("You are not permitted to export executive analytics", frappe.PermissionError)
	purpose = (purpose or "").strip()
	if len(purpose) < 10:
		frappe.throw("An export purpose of at least 10 characters is required")
	dashboard = get_dashboard(company, from_date, to_date)
	rows = [["Metric", "Domain", "Value", "Format", "Source", "Freshness", "Period", "Classification"]]
	for metric in dashboard["metrics"]:
		rows.append([metric["label"], metric["domain"], metric["value"], metric["format"], metric["source"], metric["freshness"]["status"], dashboard["period"]["label"], "Internal"])
	content = "\n".join(",".join(_csv(value) for value in row) for row in rows)
	from dtmgp.audit import record_event

	record_event(
		"data_export", "Executive analytics summary exported", company=company,
		metadata={"purpose": purpose, "from_date": str(dashboard["period"]["from_date"]), "to_date": str(dashboard["period"]["to_date"]), "row_count": len(rows) - 1, "classification": "Internal"},
	)
	return {"filename": f"dtmgp-executive-summary-{nowdate()}.csv", "content": content, "classification": "Internal", "row_count": len(rows) - 1}


def _domain_access():
	return {"governance": can_view_governance(), "workforce": can_view_hr(), "finance": can_view_finance(), "projects": can_view_projects(), "traditional": can_view_traditional()}


def _period(from_date=None, to_date=None):
	end = getdate(to_date or nowdate())
	start = getdate(from_date or date(end.year, 1, 1))
	if start > end:
		frappe.throw("From Date cannot be after To Date")
	if (end - start).days > 366:
		frappe.throw("Analytics period cannot exceed 366 days")
	return {"from_date": start, "to_date": end, "label": f"{start.strftime('%d %b %Y')} - {end.strftime('%d %b %Y')}"}


def _metrics(companies, period, access):
	metrics = []
	if access["governance"]:
		metrics += [_metric("governance.actions_overdue", _count("DTMGP Resolution Action", companies, {"status": ["!=", "Completed"], "due_date": ["<", nowdate()]}), companies), _metric("governance.returns_overdue", _count("DTMGP Statutory Return", companies, {"status": ["not in", ["Submitted", "State Reviewed"]], "due_date": ["<", nowdate()]}), companies)]
	if access["workforce"]:
		total = _count("Employee", companies)
		verified = _count("Employee", companies, {"dtmgp_verification_status": "Verified"})
		metrics += [_metric("workforce.active", _count("Employee", companies, {"status": "Active"}), companies), _metric("workforce.verification_rate", _rate(verified, total), companies)]
	if access["finance"]:
		assessed = _sum("DTMGP Revenue Assessment", "amount", companies, {"docstatus": 1, "assessment_date": ["between", [period["from_date"], period["to_date"]]]})
		collected = _sum("DTMGP Revenue Receipt", "amount", companies, {"docstatus": 1, "posting_date": ["between", [period["from_date"], period["to_date"]]]})
		metrics += [_metric("finance.revenue_collected", collected, companies), _metric("finance.collection_rate", _rate(collected, assessed), companies)]
	if access["projects"]:
		projects = frappe.get_all("Project", filters={"company": ["in", companies]}, fields=["status", "expected_end_date"]) if companies else []
		ongoing = [item for item in projects if item.status not in {"Completed", "Cancelled"}]
		metrics += [_metric("projects.ongoing", len(ongoing), companies), _metric("projects.delayed", sum(1 for item in ongoing if item.expected_end_date and getdate(item.expected_end_date) < getdate(nowdate())), companies)]
	if access["traditional"]:
		metrics.append(_metric("traditional.open_petitions", _count("DTMGP Chieftaincy Petition", companies, {"status": ["not in", ["Decided", "Closed"]]}), companies))
	return metrics


def _metric(key, value, companies):
	definition = KPI_REGISTRY[key]
	return {"key": key, "value": value, **definition, "freshness": _freshness(definition["source"], companies), "classification": "Internal"}


def _freshness(doctype, companies=None):
	if not frappe.db.exists("DocType", doctype):
		return {"status": "missing", "last_updated": None}
	filters = {"company": ["in", companies]} if companies and frappe.get_meta(doctype).has_field("company") else None
	modified = frappe.get_all(doctype, filters=filters, pluck="modified", order_by="modified desc", limit=1)
	modified = modified[0] if modified else None
	if not modified:
		return {"status": "missing", "last_updated": None}
	age = (now_datetime() - modified).days
	return {"status": "fresh" if age <= 30 else "stale", "last_updated": modified}


def _completeness(companies, access):
	sources = sorted({item["source"] for item in KPI_REGISTRY.values() if access[item["domain"]]})
	checks = []
	for source in sources:
		freshness = _freshness(source, companies)
		checks.append({"source": source, **freshness})
	complete = sum(1 for item in checks if item["status"] == "fresh")
	return {"percent": round(complete / len(checks) * 100) if checks else 100, "sources": checks, "missing": [item["source"] for item in checks if item["status"] == "missing"], "stale": [item["source"] for item in checks if item["status"] == "stale"]}


def _scorecard(company, period):
	returns_total = _count("DTMGP Statutory Return", [company])
	returns_done = _count("DTMGP Statutory Return", [company], {"status": ["in", ["Submitted", "State Reviewed"]]})
	actions_total = _count("DTMGP Resolution Action", [company])
	actions_done = _count("DTMGP Resolution Action", [company], {"status": "Completed"})
	projects_total = _count("Project", [company])
	projects_done = _count("Project", [company], {"status": "Completed"})
	employees = _count("Employee", [company])
	verified = _count("Employee", [company], {"dtmgp_verification_status": "Verified"})
	assessed = _sum("DTMGP Revenue Assessment", "amount", [company], {"docstatus": 1, "assessment_date": ["between", [period["from_date"], period["to_date"]]]})
	collected = _sum("DTMGP Revenue Receipt", "amount", [company], {"docstatus": 1, "posting_date": ["between", [period["from_date"], period["to_date"]]]})
	values = [_optional_rate(returns_done, returns_total), _optional_rate(actions_done, actions_total), _optional_rate(projects_done, projects_total), _optional_rate(verified, employees), _optional_rate(collected, assessed)]
	missing = [label for label, value in zip(["statutory returns", "resolution actions", "projects", "staff verification", "revenue assessments"], values) if value is None]
	stale = [source for source in ("DTMGP Statutory Return", "DTMGP Resolution Action", "Project", "Employee", "DTMGP Revenue Assessment") if _freshness(source, [company])["status"] == "stale"]
	complete = not missing and not stale
	return {"company": company, "score": round(sum(values) / len(values), 1) if complete else None, "rank": None, "completeness": round((len(values) - len(missing)) / len(values) * 100), "missing": missing, "stale": stale, "metrics": {"returns": values[0], "actions": values[1], "projects": values[2], "workforce": values[3], "revenue": values[4]}}


def _count(doctype, companies, filters=None):
	if not companies:
		return 0
	return frappe.db.count(doctype, filters={"company": ["in", companies], **(filters or {})})


def _sum(doctype, field, companies, filters=None):
	if not companies:
		return 0.0
	return sum(flt(value) for value in frappe.get_all(doctype, filters={"company": ["in", companies], **(filters or {})}, pluck=field))


def _rate(numerator, denominator):
	return round(flt(numerator) / flt(denominator) * 100, 1) if denominator else 0


def _optional_rate(numerator, denominator):
	return _rate(numerator, denominator) if denominator else None


def _accumulate(index, doctype, date_field, companies, start, target, value_field=None, filters=None):
	if not companies:
		return
	fields = [date_field] + ([value_field] if value_field else [])
	rows = frappe.get_all(doctype, filters={"company": ["in", companies], date_field: [">=", start], **(filters or {})}, fields=fields)
	for row in rows:
		value = row.get(date_field)
		if not value:
			continue
		key = getdate(value).strftime("%Y-%m")
		if key in index:
			index[key][target] += flt(row.get(value_field)) if value_field else 1


def _dated_alerts(doctype, companies, date_field, filters, alert_type, severity, to, title_field="name"):
	if not companies:
		return []
	rows = frappe.get_all(doctype, filters={"company": ["in", companies], date_field: ["<", nowdate()], **filters}, fields=["name", "company", date_field, title_field], order_by=f"{date_field} asc", limit=50)
	return [{"type": alert_type, "severity": severity, "company": row.company, "title": row.get(title_field) or row.name, "age_days": (getdate(nowdate()) - getdate(row.get(date_field))).days, "to": to} for row in rows]


def _csv(value):
	return f'"{str(value if value is not None else "").replace(chr(34), chr(34) * 2)}"'

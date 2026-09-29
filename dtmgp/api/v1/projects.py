import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate

from dtmgp.permissions.scope import get_requested_companies, is_state_user, require_projects_access


RECORD_FIELDS = {
	"Asset": ["company", "asset_name", "asset_category", "location", "custodian", "status", "purchase_date", "gross_purchase_amount", "docstatus"],
	"Asset Movement": ["company", "purpose", "transaction_date", "docstatus"],
	"Asset Maintenance": ["company", "asset_name", "maintenance_team"],
	"Vehicle": ["company", "make", "model", "last_odometer", "location", "employee", "insurance_company", "policy_no", "end_date"],
	"DTMGP Project Inspection": ["company", "project", "scheduled_date", "inspector", "status", "latitude", "longitude", "findings"],
	"DTMGP Asset Verification": ["company", "asset", "verification_date", "verified_by", "condition"],
	"DTMGP Project Proposal": ["company", "title", "department", "location", "funding_source", "estimated_cost", "expected_start_date", "expected_end_date", "status", "approved_project", "approval_reference"],
	"DTMGP Asset Disposal": ["company", "asset", "request_date", "disposal_method", "valuation_amount", "status", "approval_reference", "journal_entry", "disposal_date", "proceeds"],
	"DTMGP Contractor Document": ["company", "supplier", "document_type", "reference_number", "issue_date", "expiry_date", "file", "classification", "retention_category", "verification_status"],
}
EDITABLE_FIELDS = {
	"Asset": {"company", "asset_name", "item_code", "asset_category", "location", "custodian", "department", "purchase_date", "gross_purchase_amount", "available_for_use_date", "asset_owner"},
	"Asset Movement": {"company", "purpose", "transaction_date", "assets"},
	"Asset Maintenance": {"company", "asset_name", "maintenance_team"},
	"Vehicle": {"company", "license_plate", "make", "model", "last_odometer", "acquisition_date", "location", "employee", "chassis_no", "vehicle_value", "insurance_company", "policy_no", "start_date", "end_date", "fuel_type", "uom", "color", "wheels", "doors"},
	"DTMGP Project Inspection": {"company", "project", "scheduled_date", "inspector", "status", "latitude", "longitude", "photo_evidence", "findings", "recommendation", "exception_reason"},
	"DTMGP Asset Verification": {"company", "asset", "verification_date", "verified_by", "condition", "remarks"},
	"DTMGP Project Proposal": {"company", "title", "department", "location", "funding_source", "estimated_cost", "expected_start_date", "expected_end_date", "status", "business_case", "approval_reference"},
	"DTMGP Asset Disposal": {"company", "asset", "request_date", "disposal_method", "reason", "valuation_amount", "status", "approval_reference", "journal_entry", "disposal_date", "proceeds"},
	"DTMGP Contractor Document": {"company", "supplier", "document_type", "reference_number", "issue_date", "expiry_date", "file", "classification", "retention_category", "verification_status"},
}

# Status filters the frontend is allowed to request per doctype (an allowlist, not a
# passthrough, so list_records can't be used to run an arbitrary filter).
STATUS_FILTERS = {
	"Asset": {"Submitted", "In Maintenance", "Out of Order", "Scrapped", "Sold"},
	"DTMGP Project Inspection": {"Scheduled", "In Progress", "Completed", "Exception"},
}

# Role sets here follow docs/role-permission-matrix.md's "Projects/assets" column
# (Project Officer is the sole CRUSA role; State Administrator/LGA Chairman/LGA
# Secretary are RA -- approve, not create) rather than dtmgp.permissions.scope.
# PROJECTS_MANAGE_ROLES, which is the broader "may call a write endpoint at all"
# gate already applied by require_projects_access(write=True) above each function.
TRANSITIONS = {
	"Project": {
		("Open", "On hold"): {"Project Officer", "State Administrator"},
		("On hold", "Open"): {"Project Officer", "State Administrator"},
		("Open", "Completed"): {"Project Officer", "State Administrator"},
		("Open", "Cancelled"): {"State Administrator", "LGA Chairman", "LGA Secretary"},
		("On hold", "Cancelled"): {"State Administrator", "LGA Chairman", "LGA Secretary"},
	},
	"DTMGP Project Inspection": {
		("Scheduled", "In Progress"): {"Project Officer", "State Administrator"},
		("In Progress", "Completed"): {"Project Officer", "State Administrator"},
		("In Progress", "Exception"): {"Project Officer", "State Administrator"},
		("Scheduled", "Exception"): {"Project Officer", "State Administrator"},
	},
}

# Project.status is only Open/On hold/Completed/Cancelled; the nav's Ongoing/Delayed/
# Suspended/Abandoned views are derived, not stored, so project listing/dashboard
# counts are computed in Python rather than as a SQL filter.
PROJECT_VIEWS = {"register", "new", "ongoing", "completed", "delayed", "suspended", "abandoned"}


def _project_view(project):
	if project.status == "Completed":
		return "completed"
	if project.status == "Cancelled":
		return "abandoned"
	if project.status == "On hold":
		return "suspended"
	if project.expected_end_date and getdate(project.expected_end_date) < getdate(nowdate()):
		return "delayed"
	return "ongoing"


@frappe.whitelist()
def get_dashboard(company=None):
	require_projects_access()
	companies = get_requested_companies(company)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	projects = frappe.get_all("Project", filters=filters, fields=["status", "expected_end_date"])
	views = {"ongoing": 0, "completed": 0, "delayed": 0, "suspended": 0, "abandoned": 0}
	for project in projects:
		views[_project_view(project)] += 1
	inspection_filters = {**filters, "status": ["in", ["Scheduled", "In Progress"]]}
	exception_filters = {**filters, "status": "Exception"}
	insurance_due = frappe.db.count("Vehicle", filters={**filters, "end_date": ["between", [nowdate(), add_days(nowdate(), 30)]]})
	return {
		"scope": "Statewide" if is_state_user() and not company else (companies[0] if companies else "No LGA assigned"),
		"lga_count": len(companies),
		"projects": {"total": len(projects), **views},
		"inspections": {"open": frappe.db.count("DTMGP Project Inspection", filters=inspection_filters), "exceptions": frappe.db.count("DTMGP Project Inspection", filters=exception_filters)},
		"assets": {"registered": frappe.db.count("Asset", filters={**filters, "docstatus": 1})},
		"fleet": {"vehicles": frappe.db.count("Vehicle", filters=filters), "insurance_due": insurance_due},
		"can_manage": _can_manage(),
	}


def _can_manage():
	from dtmgp.permissions.scope import can_manage_projects

	return can_manage_projects()


@frappe.whitelist()
def get_form_options(company=None):
	require_projects_access()
	companies = get_requested_companies(company)
	selected = companies[0] if len(companies) == 1 else company
	if not selected:
		return {"employees": [], "locations": [], "asset_categories": [], "items": [], "open_projects": []}
	return {
		"employees": frappe.get_all("Employee", filters={"company": selected, "status": "Active"}, fields=["name", "employee_name"], order_by="employee_name"),
		"locations": frappe.get_all("Location", filters={"is_group": 0}, fields=["name", "latitude", "longitude"], order_by="location_name"),
		"asset_categories": frappe.get_all("Asset Category", pluck="name", order_by="name"),
		"items": frappe.get_all("Item", filters={"is_fixed_asset": 1}, fields=["name", "item_name"], order_by="item_name"),
		"open_projects": frappe.get_all("Project", filters={"company": selected, "status": ["!=", "Cancelled"]}, fields=["name", "project_name"], order_by="modified desc"),
	}


@frappe.whitelist()
def list_projects(company=None, view="register", search=None, page=1, page_size=25):
	require_projects_access()
	if view not in PROJECT_VIEWS:
		frappe.throw("Unsupported project view", frappe.PermissionError)
	companies = get_requested_companies(company)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	if view == "new":
		filters["status"] = "Open"
		filters["creation"] = [">=", add_days(nowdate(), -30)]
	or_filters = {"project_name": ["like", f"%{search.strip()}%"]} if search and search.strip() else None
	rows = frappe.get_all(
		"Project", filters=filters, or_filters=or_filters,
		fields=["name", "project_name", "company", "status", "percent_complete", "expected_start_date", "expected_end_date", "dtmgp_location", "dtmgp_funding_source", "department", "priority", "creation"],
		order_by="modified desc",
	)
	if view not in ("register", "new"):
		rows = [row for row in rows if _project_view(row) == view]
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	total = len(rows)
	start = (page - 1) * page_size
	return {"items": rows[start : start + page_size], "total": total, "page": page, "page_size": page_size}


PROJECT_EDITABLE_FIELDS = {"company", "project_name", "project_type", "status", "priority", "department", "expected_start_date", "expected_end_date", "dtmgp_location", "dtmgp_funding_source", "notes"}


@frappe.whitelist(methods=["POST"])
def save_project(values, name=None):
	require_projects_access(write=True)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	if not isinstance(values, dict):
		frappe.throw("Record values must be an object")
	if name:
		doc = frappe.get_doc("Project", name)
		if doc.company not in get_requested_companies():
			frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	else:
		doc = frappe.new_doc("Project")
		doc.status = "Open"
	for field in PROJECT_EDITABLE_FIELDS:
		if field in values:
			doc.set(field, values[field])
	doc.save()
	return {"name": doc.name, "status": doc.status}


TASK_EDITABLE_FIELDS = {"project", "subject", "is_milestone", "status", "priority", "exp_start_date", "exp_end_date", "description"}


def _project_company(project):
	company = frappe.db.get_value("Project", project, "company")
	if not company or company not in get_requested_companies():
		frappe.throw("Project is outside your permitted scope", frappe.PermissionError)
	return company


@frappe.whitelist()
def list_tasks(project=None, company=None, is_milestone=None, status=None, page=1, page_size=25):
	require_projects_access()
	companies = get_requested_companies(company)
	if project:
		_project_company(project)
		filters = {"project": project}
	else:
		project_names = frappe.get_all("Project", filters={"company": ["in", companies]}, pluck="name") if companies else []
		filters = {"project": ["in", project_names or [""]]}
	if is_milestone is not None:
		filters["is_milestone"] = cint(is_milestone)
	if status:
		filters["status"] = status
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	items = frappe.get_all(
		"Task", filters=filters, fields=["name", "project", "subject", "is_milestone", "status", "priority", "exp_start_date", "exp_end_date", "progress"],
		start=(page - 1) * page_size, page_length=page_size, order_by="modified desc",
	)
	return {"items": items, "total": frappe.db.count("Task", filters=filters), "page": page, "page_size": page_size}


@frappe.whitelist(methods=["POST"])
def save_task(values, name=None):
	require_projects_access(write=True)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	if not isinstance(values, dict):
		frappe.throw("Record values must be an object")
	if name:
		doc = frappe.get_doc("Task", name)
		_project_company(doc.project)
	else:
		if not values.get("project"):
			frappe.throw("Project is required")
		_project_company(values["project"])
		doc = frappe.new_doc("Task")
	for field in TASK_EDITABLE_FIELDS:
		if field in values:
			doc.set(field, values[field])
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def list_records(doctype, company=None, search=None, page=1, page_size=25, status=None):
	require_projects_access()
	if doctype not in RECORD_FIELDS:
		frappe.throw("Unsupported record type", frappe.PermissionError)
	companies = get_requested_companies(company)
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	if status:
		if status not in STATUS_FILTERS.get(doctype, set()):
			frappe.throw("Unsupported status filter", frappe.PermissionError)
		filters["status"] = status
	or_filters = None
	if search and search.strip():
		term = f"%{search.strip()}%"
		search_fields = [field for field in ("asset_name", "make", "model") if field in RECORD_FIELDS[doctype]]
		or_filters = {field: ["like", term] for field in search_fields} or None
	items = frappe.get_all(
		doctype, filters=filters, or_filters=or_filters, fields=["name", *RECORD_FIELDS[doctype]],
		start=(page - 1) * page_size, page_length=page_size, order_by="modified desc",
	)
	total = frappe.db.count(doctype, filters=filters)
	return {"items": items, "total": total, "page": page, "page_size": page_size}


@frappe.whitelist(methods=["POST"])
def save_record(doctype, values, name=None):
	require_projects_access(write=True)
	if doctype not in EDITABLE_FIELDS:
		frappe.throw("Unsupported record type", frappe.PermissionError)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	if not isinstance(values, dict):
		frappe.throw("Record values must be an object")
	if name:
		doc = frappe.get_doc(doctype, name)
		if doc.company not in get_requested_companies():
			frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	else:
		doc = frappe.new_doc(doctype)
	for field in EDITABLE_FIELDS[doctype]:
		if field in values:
			doc.set(field, values[field])
	doc.save()
	return {"name": doc.name, "doctype": doc.doctype, "status": doc.get("status"), "docstatus": doc.docstatus}


@frappe.whitelist(methods=["POST"])
def submit_record(doctype, name):
	require_projects_access(write=True)
	if doctype not in {"Asset", "Asset Movement"}:
		frappe.throw("This record type cannot be submitted through this service", frappe.PermissionError)
	doc = frappe.get_doc(doctype, name)
	if doc.company not in get_requested_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	doc.submit()
	return {"name": doc.name, "docstatus": doc.docstatus, "status": doc.get("status")}


@frappe.whitelist(methods=["POST"])
def transition_record(doctype, name, target_status):
	require_projects_access(write=True)
	if doctype not in TRANSITIONS:
		frappe.throw("This record does not support workflow transitions", frappe.PermissionError)
	doc = frappe.get_doc(doctype, name)
	if doc.company not in get_requested_companies():
		frappe.throw("Record is outside your permitted scope", frappe.PermissionError)
	if (doc.status, target_status) not in TRANSITIONS[doctype]:
		frappe.throw(f"Transition from {doc.status} to {target_status} is not allowed")
	roles = set(frappe.get_roles())
	required_roles = TRANSITIONS[doctype][(doc.status, target_status)]
	if frappe.session.user != "Administrator" and not roles.intersection(required_roles | {"State Administrator"}):
		frappe.throw("Your role cannot perform this workflow transition", frappe.PermissionError)
	doc.status = target_status
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def list_contractors(search=None, status=None, page=1, page_size=25):
	"""Suppliers are shared statewide (no `company` field), same as they're already
	treated in dtmgp/finance.py's DTMGPProcurementCase.recommended_supplier."""
	require_projects_access()
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	filters = {}
	if status == "blacklisted":
		filters["disabled"] = 1
	elif status == "on_hold":
		filters["on_hold"] = 1
	or_filters = {"supplier_name": ["like", f"%{search.strip()}%"]} if search and search.strip() else None
	items = frappe.get_all(
		"Supplier", filters=filters, or_filters=or_filters,
		fields=["name", "supplier_name", "supplier_type", "supplier_group", "disabled", "on_hold", "hold_type"],
		start=(page - 1) * page_size, page_length=page_size, order_by="modified desc",
	)
	return {"items": items, "total": frappe.db.count("Supplier", filters=filters), "page": page, "page_size": page_size}


@frappe.whitelist(methods=["POST"])
def set_contractor_hold(supplier, on_hold, hold_type=None):
	require_projects_access(write=True)
	doc = frappe.get_doc("Supplier", supplier)
	doc.on_hold = cint(on_hold)
	doc.hold_type = hold_type or "All" if cint(on_hold) else ""
	doc.save()
	return {"name": doc.name, "on_hold": doc.on_hold}


@frappe.whitelist()
def get_contractor_performance(company=None):
	"""Derived read-only view over DTMGP Procurement Case -- no new schema. Cross-domain
	read of dtmgp/finance.py's own DocType, same as its own dashboard reads back across
	Revenue/Procurement/Payments/Audit."""
	require_projects_access()
	companies = get_requested_companies(company)
	filters = {"company": ["in", companies], "recommended_supplier": ["is", "set"]} if companies else {"name": ""}
	cases = frappe.get_all("DTMGP Procurement Case", filters=filters, fields=["recommended_supplier", "status", "estimated_amount", "evaluated_amount"])
	by_supplier = {}
	for case in cases:
		row = by_supplier.setdefault(case.recommended_supplier, {"supplier": case.recommended_supplier, "cases": 0, "completed": 0, "estimated_total": 0.0, "evaluated_total": 0.0})
		row["cases"] += 1
		row["completed"] += case.status == "Completed"
		row["estimated_total"] += flt(case.estimated_amount)
		row["evaluated_total"] += flt(case.evaluated_amount)
	return {"items": sorted(by_supplier.values(), key=lambda row: -row["cases"])}


@frappe.whitelist()
def list_vehicle_logs(license_plate=None, company=None, page=1, page_size=25):
	require_projects_access()
	if license_plate:
		vehicle_company = frappe.db.get_value("Vehicle", license_plate, "company")
		if not vehicle_company or vehicle_company not in get_requested_companies():
			frappe.throw("Vehicle is outside your permitted scope", frappe.PermissionError)
		filters = {"license_plate": license_plate}
	else:
		companies = get_requested_companies(company)
		vehicle_names = frappe.get_all("Vehicle", filters={"company": ["in", companies]}, pluck="name") if companies else []
		filters = {"license_plate": ["in", vehicle_names or [""]]}
	page, page_size = max(cint(page), 1), min(max(cint(page_size), 1), 100)
	items = frappe.get_all(
		"Vehicle Log", filters=filters, fields=["name", "license_plate", "employee", "date", "odometer", "fuel_qty", "price", "supplier", "invoice", "docstatus"],
		start=(page - 1) * page_size, page_length=page_size, order_by="date desc",
	)
	return {"items": items, "total": frappe.db.count("Vehicle Log", filters=filters), "page": page, "page_size": page_size}


VEHICLE_LOG_EDITABLE_FIELDS = {"license_plate", "employee", "date", "odometer", "fuel_qty", "price", "supplier", "invoice"}


@frappe.whitelist(methods=["POST"])
def save_vehicle_log(values, name=None):
	require_projects_access(write=True)
	values = frappe.parse_json(values) if isinstance(values, str) else values
	if not isinstance(values, dict):
		frappe.throw("Record values must be an object")
	license_plate = values.get("license_plate") or (name and frappe.db.get_value("Vehicle Log", name, "license_plate"))
	company = frappe.db.get_value("Vehicle", license_plate, "company") if license_plate else None
	if not company or company not in get_requested_companies():
		frappe.throw("Vehicle is outside your permitted scope", frappe.PermissionError)
	doc = frappe.get_doc("Vehicle Log", name) if name else frappe.new_doc("Vehicle Log")
	for field in VEHICLE_LOG_EDITABLE_FIELDS:
		if field in values:
			doc.set(field, values[field])
	doc.save()
	return {"name": doc.name, "docstatus": doc.docstatus}


@frappe.whitelist()
def get_maps_data(company=None):
	require_projects_access()
	companies = get_requested_companies(company)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	projects = frappe.get_all("Project", filters={**filters, "dtmgp_location": ["is", "set"]}, fields=["name", "project_name", "company", "dtmgp_location"])
	for project in projects:
		loc = frappe.db.get_value("Location", project.dtmgp_location, ["latitude", "longitude"], as_dict=True)
		project.update({"latitude": loc.latitude if loc else None, "longitude": loc.longitude if loc else None})
	assets = frappe.get_all("Asset", filters={**filters, "location": ["is", "set"]}, fields=["name", "asset_name", "company", "location"])
	for asset in assets:
		loc = frappe.db.get_value("Location", asset.location, ["latitude", "longitude"], as_dict=True)
		asset.update({"latitude": loc.latitude if loc else None, "longitude": loc.longitude if loc else None})
	inspections = frappe.get_all("DTMGP Project Inspection", filters={**filters, "latitude": ["is", "set"]}, fields=["name", "project", "company", "latitude", "longitude", "status"])
	return {
		"projects": [row for row in projects if row.latitude and row.longitude],
		"assets": [row for row in assets if row.latitude and row.longitude],
		"inspections": [row for row in inspections if row.latitude and row.longitude],
	}


@frappe.whitelist()
def get_reports(company=None):
	require_projects_access()
	companies = get_requested_companies(company)
	filters = {"company": ["in", companies]} if companies else {"name": ""}
	projects = frappe.get_all("Project", filters=filters, fields=["status", "expected_end_date", "percent_complete"])
	views = {"ongoing": 0, "completed": 0, "delayed": 0, "suspended": 0, "abandoned": 0}
	for project in projects:
		views[_project_view(project)] += 1
	inspections = frappe.get_all("DTMGP Project Inspection", filters=filters, fields=["status"])
	inspection_counts = {}
	for row in inspections:
		inspection_counts[row.status] = inspection_counts.get(row.status, 0) + 1
	assets = frappe.get_all("Asset", filters=filters, fields=["status"])
	asset_counts = {}
	for row in assets:
		asset_counts[row.status] = asset_counts.get(row.status, 0) + 1
	fleet_filters = {"company": ["in", companies]} if companies else {"name": ""}
	fuel_cost = frappe.db.sql(
		"select coalesce(sum(fuel_qty * price), 0) from `tabVehicle Log` where license_plate in (select name from `tabVehicle` where company in %(companies)s)",
		{"companies": companies or [""]},
	)[0][0]
	return {
		"project_status": {"total": len(projects), **views},
		"project_performance": {"average_percent_complete": round(sum(flt(p.percent_complete) for p in projects) / len(projects), 1) if projects else 0, "delayed": views["delayed"]},
		"inspections": inspection_counts,
		"assets": asset_counts,
		"fleet": {"vehicle_count": frappe.db.count("Vehicle", filters=fleet_filters), "total_fuel_cost": flt(fuel_cost)},
	}


@frappe.whitelist()
def get_project_financials(company=None):
	require_projects_access()
	companies = get_requested_companies(company)
	projects = frappe.get_all("Project", filters={"company": ["in", companies]}, fields=["name", "project_name", "company"], order_by="project_name")
	rows = []
	for project in projects:
		budget = frappe.db.sql("""select coalesce(sum(ba.budget_amount), 0) from `tabBudget Account` ba
			inner join `tabBudget` b on b.name=ba.parent where b.docstatus=1 and b.project=%s""", project.name)[0][0]
		actual = frappe.db.sql("select coalesce(sum(debit-credit), 0) from `tabGL Entry` where is_cancelled=0 and project=%s and company=%s", (project.name, project.company))[0][0]
		rows.append({**project, "budget": flt(budget), "actual": flt(actual), "drawdown": flt(actual / budget * 100) if budget else 0})
	variations = frappe.get_all("DTMGP Contract Variation", filters={"company": ["in", companies], "project": ["is", "set"]}, fields=["name", "project", "contract", "variation_type", "amount_change", "days_change", "status", "approval_reference"], order_by="modified desc")
	return {"projects": rows, "variations": variations}

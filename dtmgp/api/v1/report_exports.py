import csv
import io

import frappe
from frappe.utils import nowdate

from dtmgp.audit import record_event
from dtmgp.permissions.scope import (
	get_requested_companies,
	get_user_roles,
	require_analytics_access,
	require_finance_access,
	require_governance_access,
	require_hr_access,
	require_projects_access,
	require_payroll_access,
	require_staff_audit_access,
	require_traditional_access,
)


EXPORT_ROLES = {
	"System Manager", "State Administrator", "State Executive Viewer", "State Auditor",
	"LGA Administrator", "LGA Chairman", "LGA Secretary", "Treasurer", "Revenue Officer",
	"HR Officer", "Procurement Officer", "Project Officer", "Traditional Affairs Officer", "Internal Auditor",
}
REPORT_DOMAINS = {
	"hr": require_hr_access,
	"finance": require_finance_access,
	"governance": require_governance_access,
	"projects": require_projects_access,
	"traditional": require_traditional_access,
	"analytics": require_analytics_access,
}
REPORT_COLUMNS = {
	"hr.staff-strength": ["Department", "Staff"],
	"hr.staff-distribution": ["Gender", "Staff"],
	"hr.workforce-by-lga": ["LGA", "Active staff", "Verified", "Verified %"],
	"hr.retirement-forecast": ["Measure", "Value"],
	"hr.leave": ["Leave type", "Days taken"],
	"hr.establishment": ["Measure", "Value"],
	"hr.payroll": ["Status", "Salary slips"],
	"hr.staff-audit": ["Exception", "Count"],
	"finance.budget-performance": ["Account", "Budget", "Actual", "Variance"],
	"finance.revenue-performance": ["Measure", "Amount"],
	"finance.expenditure": ["Measure", "Amount"],
	"finance.cash-flow": ["Measure", "Amount"],
	"finance.trial-balance": ["Account", "Root type", "Debit", "Credit"],
	"finance.general-ledger": ["Date", "Account", "Debit", "Credit", "Voucher"],
	"governance.summary": ["Area", "Measure", "Value"],
	"projects.status": ["Status", "Count"],
	"projects.performance": ["Measure", "Value"],
	"projects.inspections": ["Status", "Count"],
	"projects.assets": ["Status", "Count"],
	"projects.fleet": ["Measure", "Value"],
	"traditional.institutions": ["Type", "Count"],
	"traditional.rulers": ["Status", "Count"],
	"traditional.appointments": ["Stage", "Count"],
	"traditional.succession": ["Status", "Count"],
	"traditional.petitions": ["Status", "Count"],
}
REPORT_GATES = {"hr.payroll": require_payroll_access, "hr.staff-audit": require_staff_audit_access}


def _safe_csv_cell(value):
	if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
		return f"'{value}"
	return value


@frappe.whitelist(methods=["POST"])
def export_report(report_id, title, purpose, columns, rows, company=None):
	domain = (report_id or "").split(".", 1)[0]
	gate = REPORT_GATES.get(report_id) or REPORT_DOMAINS.get(domain)
	if not gate or report_id not in REPORT_COLUMNS:
		frappe.throw("This report is not approved for export", frappe.PermissionError)
	gate()
	if frappe.session.user != "Administrator" and not get_user_roles().intersection(EXPORT_ROLES):
		frappe.throw("You are not permitted to export reports", frappe.PermissionError)
	companies = get_requested_companies(company)
	selected_company = company if company in companies else None
	purpose = (purpose or "").strip()
	if len(purpose) < 10:
		frappe.throw("An export purpose of at least 10 characters is required")
	if isinstance(columns, str):
		columns = frappe.parse_json(columns)
	if isinstance(rows, str):
		rows = frappe.parse_json(rows)
	if columns != REPORT_COLUMNS[report_id]:
		frappe.throw("The report columns do not match the approved export layout")
	if not isinstance(rows, list) or len(rows) > 5000 or any(not isinstance(row, list) or len(row) != len(columns) for row in rows):
		frappe.throw("The report rows are invalid or exceed the 5,000-row export limit")

	output = io.StringIO()
	writer = csv.writer(output)
	writer.writerow(columns)
	writer.writerows([[_safe_csv_cell(value) for value in row] for row in rows])
	record_event(
		"data_export", f"{title} exported", company=selected_company,
		metadata={"purpose": purpose, "report_id": report_id, "row_count": len(rows), "classification": "Internal"},
	)
	filename = f"{report_id.replace('.', '-')}-{nowdate()}.csv"
	return {"filename": filename, "content": output.getvalue(), "classification": "Internal", "row_count": len(rows)}

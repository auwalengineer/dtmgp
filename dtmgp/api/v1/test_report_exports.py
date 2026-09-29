from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.report_exports import export_report


class TestReportExports(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_unknown_report_is_denied(self):
		with self.assertRaises(frappe.PermissionError):
			export_report("unknown.report", "Unknown", "Monthly management review", [], [])

	@patch("dtmgp.api.v1.report_exports.record_event")
	@patch("dtmgp.api.v1.report_exports.get_requested_companies", return_value=["Test LGA"])
	@patch("dtmgp.api.v1.report_exports.require_hr_access")
	def test_export_has_approved_layout_and_audit_event(self, _access, _companies, audit):
		result = export_report(
			"hr.staff-strength", "Staff Strength Report", "Monthly management review",
			["Department", "Staff"], [["Finance", 12]], "Test LGA",
		)
		self.assertIn("Department,Staff", result["content"])
		self.assertEqual(result["row_count"], 1)
		audit.assert_called_once()

	@patch("dtmgp.api.v1.report_exports.get_requested_companies", return_value=["Test LGA"])
	@patch("dtmgp.api.v1.report_exports.require_hr_access")
	def test_changed_columns_are_rejected(self, _access, _companies):
		with self.assertRaises(frappe.ValidationError):
			export_report(
				"hr.staff-strength", "Staff Strength Report", "Monthly management review",
				["Private field"], [["value"]], "Test LGA",
			)

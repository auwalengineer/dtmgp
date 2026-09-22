from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.analytics import export_executive_summary, get_alerts, get_dashboard, get_maps, get_scorecards, get_trends
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup


class TestAnalyticsScope(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.hr_officer = self._make_user("HR Officer", self.makurdi)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_lga_dashboard_is_scoped_and_domain_filtered(self):
		frappe.set_user(self.hr_officer.name)
		result = get_dashboard()
		self.assertEqual(result["scope"], self.makurdi)
		self.assertTrue(result["domains"]["workforce"])
		self.assertFalse(result["domains"]["finance"])
		self.assertFalse(result["can_compare_lgas"])
		self.assertTrue(all(metric["domain"] != "finance" for metric in result["metrics"]))
		with self.assertRaises(frappe.PermissionError):
			get_dashboard(self.gboko)

	def test_lga_user_cannot_compare_or_export(self):
		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			get_scorecards()
		with self.assertRaises(frappe.PermissionError):
			export_executive_summary("Quarterly management review")

	def test_state_scorecard_includes_all_lgas_and_does_not_rank_incomplete_data(self):
		frappe.set_user("Administrator")
		result = get_scorecards()
		self.assertEqual(len(result["rows"]), 23)
		for row in result["rows"]:
			if row["completeness"] < 100 or row["stale"]:
				self.assertIsNone(row["score"])
				self.assertIsNone(row["rank"])

	def test_operational_feeds_and_audited_export_are_available(self):
		frappe.set_user("Administrator")
		self.assertEqual(len(get_trends(self.makurdi, months=6)["months"]), 6)
		self.assertIn("items", get_alerts(self.makurdi))
		self.assertIn("projects", get_maps(self.makurdi))
		exported = export_executive_summary("Quarterly management review", self.makurdi)
		self.assertEqual(exported["classification"], "Internal")
		self.assertIn("Metric", exported["content"])
		self.assertTrue(frappe.db.exists("DTMGP Audit Event", {"event_type": "data_export", "company": self.makurdi}))

	def _make_user(self, role, company):
		return frappe.get_doc({
			"doctype": "User", "email": f"analytics-{uuid4().hex}@example.com", "first_name": "Analytics",
			"enabled": 1, "send_welcome_email": 0, "dtmgp_lga": company, "roles": [{"role": role}],
		}).insert()

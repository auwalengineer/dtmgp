from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.people import get_workforce_dashboard
from dtmgp.dtmgp.dashboard_chart_source.dtmgp_workforce_breakdown.dtmgp_workforce_breakdown import CHART_BREAKDOWNS, get_data
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup
from dtmgp.workforce import BREAKDOWNS, short_lga


class TestWorkforceDashboard(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.hr_officer = self._make_user("HR Officer", self.makurdi)
		self.treasurer = self._make_user("Treasurer", self.makurdi)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_lga_user_sees_only_own_lga_totals(self):
		frappe.set_user(self.hr_officer.name)
		before = get_workforce_dashboard()["totals"]["active"]
		frappe.set_user("Administrator")
		self._make_employee(self.makurdi)
		self._make_employee(self.gboko)

		frappe.set_user(self.hr_officer.name)
		summary = get_workforce_dashboard()
		self.assertEqual(summary["totals"]["active"], before + 1)
		self.assertEqual({row["company"] for row in summary["breakdowns"]["lga"]}, {self.makurdi})
		self.assertFalse(summary["scope"]["is_statewide"])

	def test_state_user_sees_every_lga(self):
		self._make_employee(self.makurdi)
		self._make_employee(self.gboko)
		summary = get_workforce_dashboard()
		self.assertTrue(summary["scope"]["is_statewide"])
		self.assertTrue({self.makurdi, self.gboko} <= {row["company"] for row in summary["breakdowns"]["lga"]})
		self.assertEqual(set(summary["breakdowns"]), set(BREAKDOWNS))

	def test_lga_user_cannot_request_another_lga(self):
		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			get_workforce_dashboard(self.gboko)
		with self.assertRaises(frappe.PermissionError):
			get_data(chart_name="Workforce by LGA", filters={"company": self.gboko})

	def test_non_hr_role_is_denied(self):
		frappe.set_user(self.treasurer.name)
		with self.assertRaises(frappe.PermissionError):
			get_workforce_dashboard()
		with self.assertRaises(frappe.PermissionError):
			get_data(chart_name="Workforce by LGA")

	def test_desk_chart_is_scoped_per_user_not_cached_by_chart_name(self):
		self._make_employee(self.gboko)
		statewide = get_data(chart_name="Workforce by LGA", refresh=1)
		self.assertIn(short_lga(self.gboko), statewide["labels"])

		frappe.set_user(self.hr_officer.name)
		scoped = get_data(chart_name="Workforce by LGA")
		self.assertNotIn(short_lga(self.gboko), scoped["labels"])

	def test_every_desk_chart_maps_to_a_known_breakdown(self):
		for chart_name, breakdown in CHART_BREAKDOWNS.items():
			self.assertIn(breakdown, BREAKDOWNS)
			self.assertTrue(frappe.db.exists("Dashboard Chart", chart_name), chart_name)
			result = get_data(chart_name=chart_name)
			self.assertEqual(len(result["labels"]), len(result["datasets"][0]["values"]))
		with self.assertRaises(frappe.ValidationError):
			get_data(chart_name="Not A Workforce Chart")

	def _make_employee(self, company):
		gender = frappe.get_all("Gender", pluck="name", limit=1)[0]
		return frappe.get_doc(
			{
				"doctype": "Employee", "first_name": "Workforce", "last_name": uuid4().hex[:6], "company": company,
				"gender": gender, "date_of_birth": "1985-01-01", "date_of_joining": "2015-01-01", "status": "Active",
			}
		).insert().name

	def _make_user(self, role, company):
		return frappe.get_doc(
			{
				"doctype": "User", "email": f"workforce-{uuid4().hex}@example.com", "first_name": "Workforce",
				"last_name": "Test", "enabled": 1, "send_welcome_email": 0, "dtmgp_lga": company, "roles": [{"role": role}],
			}
		).insert()

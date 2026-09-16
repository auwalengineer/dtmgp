from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.people import get_dashboard, list_employees, save_employee
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup


class TestPeopleScope(FrappeTestCase):
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

	def test_hr_officer_can_create_and_list_employee_in_assigned_lga(self):
		frappe.set_user(self.hr_officer.name)
		gender = frappe.get_all("Gender", pluck="name", limit=1)[0]
		created = save_employee(
			"Aondo",
			self.makurdi,
			gender,
			"1990-01-01",
			"2020-01-01",
			last_name="Test",
			grade_level="GL 08",
			verification_status="Verified",
		)

		items = list_employees(self.makurdi, search=created["name"])["items"]
		self.assertEqual(len(items), 1)
		self.assertEqual(items[0].company, self.makurdi)
		self.assertEqual(get_dashboard(self.makurdi)["verified"], 1)

	def test_non_hr_role_cannot_access_people_api(self):
		frappe.set_user(self.treasurer.name)
		with self.assertRaises(frappe.PermissionError):
			get_dashboard(self.makurdi)

	def test_hr_officer_cannot_request_another_lga(self):
		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			list_employees(self.gboko)

	def _make_user(self, role, company):
		email = f"people-{uuid4().hex}@example.com"
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "People",
				"last_name": "Test",
				"enabled": 1,
				"send_welcome_email": 0,
				"dtmgp_lga": company,
				"roles": [{"role": role}],
			}
		).insert()

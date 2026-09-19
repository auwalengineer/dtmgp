from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.governance import get_dashboard, list_departments, list_records, save_department, save_record, transition_record
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup


class TestGovernanceScope(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.secretary = self._make_user("LGA Secretary", self.makurdi)
		self.gboko_secretary = self._make_user("LGA Secretary", self.gboko)
		self.treasurer = self._make_user("Treasurer", self.makurdi)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_secretary_creates_lists_and_registers_correspondence_in_own_lga(self):
		frappe.set_user(self.secretary.name)
		record = save_record("DTMGP Correspondence", {
			"company": self.makurdi, "correspondence_type": "Incoming", "subject": "State circular",
			"correspondent": "Office of the Governor", "correspondence_date": "2026-09-19",
		})
		self.assertTrue(record["name"].startswith("COR-MKD-2026-"))
		self.assertEqual(transition_record("DTMGP Correspondence", record["name"], "Registered")["status"], "Registered")

		result = list_records("DTMGP Correspondence", self.makurdi, search="State circular")
		self.assertEqual(result["items"][0].company, self.makurdi)
		self.assertEqual(get_dashboard(self.makurdi)["correspondence"]["registered"], 1)

	def test_cross_lga_access_is_rejected(self):
		frappe.set_user(self.secretary.name)
		with self.assertRaises(frappe.PermissionError):
			list_records("DTMGP Correspondence", self.gboko)
		with self.assertRaises(frappe.PermissionError):
			save_record("DTMGP Correspondence", {
				"company": self.gboko, "correspondence_type": "Incoming", "subject": "Outside",
				"correspondent": "Someone", "correspondence_date": "2026-09-19",
			})

	def test_non_manage_role_cannot_write_correspondence(self):
		frappe.set_user(self.treasurer.name)
		with self.assertRaises(frappe.PermissionError):
			save_record("DTMGP Correspondence", {
				"company": self.makurdi, "correspondence_type": "Incoming", "subject": "Blocked",
				"correspondent": "Someone", "correspondence_date": "2026-09-19",
			})
		# Read access is still granted via the broader GOVERNANCE_VIEW_ROLES set.
		self.assertEqual(list_records("DTMGP Correspondence", self.makurdi)["total"], 0)

	def test_department_scope_is_lga_isolated(self):
		frappe.set_user(self.secretary.name)
		department = save_department({"department_name": f"Registry {uuid4().hex[:6]}", "company": self.makurdi})
		names = [row.name for row in list_departments(self.makurdi)]
		self.assertIn(department["name"], names)

		frappe.set_user(self.gboko_secretary.name)
		names = [row.name for row in list_departments(self.gboko)]
		self.assertNotIn(department["name"], names)
		with self.assertRaises(frappe.PermissionError):
			save_department({"department_name": "Outside attempt", "company": self.makurdi})

	def _make_user(self, role, company):
		return frappe.get_doc({
			"doctype": "User", "email": f"governance-{uuid4().hex}@example.com", "first_name": "Governance",
			"enabled": 1, "send_welcome_email": 0, "dtmgp_lga": company, "roles": [{"role": role}],
		}).insert()

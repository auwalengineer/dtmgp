from uuid import uuid4

import frappe
from frappe.client import get as client_get
from frappe.tests.utils import FrappeTestCase

from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup

"""Stage 2 cross-LGA denial coverage for the governance module, exercising the
permission_query_conditions/has_permission hooks directly (frappe.client.get, raw
get_list, direct doc.save()) rather than through dtmgp.api.v1.governance, which is
already covered in test_governance_scope.py. Mirrors dtmgp/permissions/test_isolation.py
for DTMGP Correspondence, and separately proves Department's native (non-dtmgp) Company
User Permission scoping holds for direct reads and writes too."""


class TestGovernanceCrossLGAIsolation(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.makurdi_secretary = self._make_user("LGA Secretary", self.makurdi)
		self.gboko_secretary = self._make_user("LGA Secretary", self.gboko)
		self.makurdi_correspondence = self._make_correspondence(self.makurdi)
		self.makurdi_department = self._make_department(self.makurdi)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_direct_document_read_by_guessed_name_is_denied_across_lga(self):
		frappe.set_user(self.gboko_secretary.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Correspondence", self.makurdi_correspondence.name)

		frappe.set_user(self.makurdi_secretary.name)
		result = client_get("DTMGP Correspondence", self.makurdi_correspondence.name)
		self.assertEqual(result["name"], self.makurdi_correspondence.name)

	def test_direct_write_is_denied_across_lga_even_without_the_api_layer(self):
		frappe.set_user(self.gboko_secretary.name)
		doc = frappe.get_doc("DTMGP Correspondence", self.makurdi_correspondence.name)
		doc.subject = "Tampered"
		with self.assertRaises(frappe.PermissionError):
			doc.save()

	def test_list_query_excludes_other_lga_records_without_api_help(self):
		frappe.set_user(self.gboko_secretary.name)
		names = frappe.get_list("DTMGP Correspondence", pluck="name")
		self.assertNotIn(self.makurdi_correspondence.name, names)

	def test_department_direct_read_and_write_are_denied_across_lga(self):
		frappe.set_user(self.gboko_secretary.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("Department", self.makurdi_department.name)

		doc = frappe.get_doc("Department", self.makurdi_department.name)
		doc.flags.ignore_permissions = False
		with self.assertRaises(frappe.PermissionError):
			doc.save()

		names = frappe.get_list("Department", pluck="name")
		self.assertNotIn(self.makurdi_department.name, names)

	def _make_correspondence(self, company):
		return frappe.get_doc(
			{
				"doctype": "DTMGP Correspondence",
				"company": company,
				"correspondence_type": "Incoming",
				"subject": "Isolation Test Correspondence",
				"correspondent": "Test Sender",
				"correspondence_date": "2026-09-19",
			}
		).insert(ignore_permissions=True)

	def _make_department(self, company):
		return frappe.get_doc(
			{
				"doctype": "Department",
				"department_name": f"Isolation Test {uuid4().hex[:6]}",
				"company": company,
			}
		).insert(ignore_permissions=True)

	def _make_user(self, role, company):
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": f"gov-iso-{uuid4().hex}@example.com",
				"first_name": "Governance Isolation",
				"enabled": 1,
				"send_welcome_email": 0,
				"dtmgp_lga": company,
				"roles": [{"role": role}],
			}
		).insert()

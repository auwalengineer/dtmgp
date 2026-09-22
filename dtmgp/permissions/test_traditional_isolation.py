from uuid import uuid4

import frappe
from frappe.client import get as client_get
from frappe.tests.utils import FrappeTestCase

from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup

"""Cross-LGA denial coverage for the Traditional Affairs module, exercising the
permission_query_conditions/has_permission hooks directly (frappe.client.get, raw
get_list, direct doc.save()) rather than through dtmgp.api.v1.traditional, which is
already covered in test_traditional_scope.py. Mirrors
dtmgp/permissions/test_governance_isolation.py."""


class TestTraditionalCrossLGAIsolation(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.makurdi_officer = self._make_user("Traditional Affairs Officer", self.makurdi)
		self.gboko_officer = self._make_user("Traditional Affairs Officer", self.gboko)
		self.makurdi_institution = self._make_institution(self.makurdi)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_direct_document_read_by_guessed_name_is_denied_across_lga(self):
		frappe.set_user(self.gboko_officer.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Traditional Institution", self.makurdi_institution.name)

		frappe.set_user(self.makurdi_officer.name)
		result = client_get("DTMGP Traditional Institution", self.makurdi_institution.name)
		self.assertEqual(result["name"], self.makurdi_institution.name)

	def test_direct_write_is_denied_across_lga_even_without_the_api_layer(self):
		frappe.set_user(self.gboko_officer.name)
		doc = frappe.get_doc("DTMGP Traditional Institution", self.makurdi_institution.name)
		doc.seat_location = "Tampered"
		with self.assertRaises(frappe.PermissionError):
			doc.save()

	def test_list_query_excludes_other_lga_records_without_api_help(self):
		frappe.set_user(self.gboko_officer.name)
		names = frappe.get_list("DTMGP Traditional Institution", pluck="name")
		self.assertNotIn(self.makurdi_institution.name, names)

	def test_ruler_and_petition_are_scoped_the_same_way(self):
		ruler = self._make_ruler(self.makurdi, self.makurdi_institution.name)
		petition = self._make_petition(self.makurdi, self.makurdi_institution.name)
		frappe.set_user(self.gboko_officer.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Traditional Ruler", ruler.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Chieftaincy Petition", petition.name)
		self.assertNotIn(ruler.name, frappe.get_list("DTMGP Traditional Ruler", pluck="name"))
		self.assertNotIn(petition.name, frappe.get_list("DTMGP Chieftaincy Petition", pluck="name"))

	def _make_institution(self, company):
		return frappe.get_doc({
			"doctype": "DTMGP Traditional Institution", "company": company,
			"institution_name": f"Isolation Test Stool {uuid4().hex[:6]}", "institution_type": "District Headship", "status": "Active",
		}).insert(ignore_permissions=True)

	def _make_ruler(self, company, institution):
		return frappe.get_doc({
			"doctype": "DTMGP Traditional Ruler", "company": company, "ruler_name": "Isolation Test Ruler",
			"institution": institution, "appointment_date": "2026-01-01",
		}).insert(ignore_permissions=True)

	def _make_petition(self, company, institution):
		return frappe.get_doc({
			"doctype": "DTMGP Chieftaincy Petition", "company": company, "institution": institution,
			"petitioner_name": "Isolation Test Petitioner", "petition_type": "Rival Claim",
			"petition_date": "2026-01-01", "description": "Isolation test",
		}).insert(ignore_permissions=True)

	def _make_user(self, role, company):
		return frappe.get_doc({
			"doctype": "User", "email": f"trad-iso-{uuid4().hex}@example.com", "first_name": "Traditional Isolation",
			"enabled": 1, "send_welcome_email": 0, "dtmgp_lga": company, "roles": [{"role": role}],
		}).insert()

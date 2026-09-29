from uuid import uuid4

import frappe
from frappe.client import get as client_get
from frappe.core.doctype.file.file import has_permission as file_has_permission
from frappe.tests.utils import FrappeTestCase

from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup

"""Stage 2 cross-LGA denial coverage for the restricted HR doctypes (DTMGP Personnel
File, DTMGP Next of Kin, DTMGP Staff Document) that dtmgp/permissions/test_hr_extensions.py
only exercises through the dtmgp.api.v1.hr list_restricted_hr_records/
save_restricted_hr_record wrapper functions -- this proves the permission_query_conditions/
has_permission hooks themselves (dtmgp/permissions/hr.py) hold for direct document URLs,
raw list/report queries and attachments, mirroring dtmgp/permissions/test_isolation.py
and test_projects_isolation.py. Closes part of the "extend the same direct-hook
coverage to ... restricted HR records" gap noted in docs/implementation-status.md's
FND-005 row. No role currently holds doctype-level export=1 on any of these three
doctypes (see the *_personnel_file.json/*_next_of_kin.json/*_staff_document.json
DocPerm rows), so there is no export-permission case to cover here, unlike Revenue
Head/Procurement Case/Audit Query."""


class TestRestrictedHRCrossLGAIsolation(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.makurdi_hr = self._make_user("HR Officer", self.makurdi)
		self.gboko_hr = self._make_user("HR Officer", self.gboko)
		self.makurdi_employee = self._make_employee(self.makurdi)
		self.gboko_employee = self._make_employee(self.gboko)
		self.makurdi_file = self._make_personnel_file(self.makurdi, self.makurdi_employee.name)
		self.gboko_file = self._make_personnel_file(self.gboko, self.gboko_employee.name)
		self.makurdi_kin = self._make_next_of_kin(self.makurdi, self.makurdi_employee.name)
		self.makurdi_document = self._make_staff_document(self.makurdi, self.makurdi_employee.name)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	# ------------------------------------------------------------------ Personnel File

	def test_personnel_file_read_and_list_are_denied_across_lga(self):
		frappe.set_user(self.gboko_hr.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Personnel File", self.makurdi_file.name)
		self.assertNotIn(self.makurdi_file.name, frappe.get_list("DTMGP Personnel File", pluck="name"))

		frappe.set_user(self.makurdi_hr.name)
		result = client_get("DTMGP Personnel File", self.makurdi_file.name)
		self.assertEqual(result["name"], self.makurdi_file.name)

	def test_personnel_file_direct_write_is_denied_across_lga(self):
		frappe.set_user(self.gboko_hr.name)
		doc = frappe.get_doc("DTMGP Personnel File", self.makurdi_file.name)
		doc.physical_file_reference = "Tampered"
		with self.assertRaises(frappe.PermissionError):
			doc.save()

	# -------------------------------------------------------------------- Next of Kin

	def test_next_of_kin_read_and_list_are_denied_across_lga(self):
		frappe.set_user(self.gboko_hr.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Next of Kin", self.makurdi_kin.name)
		self.assertNotIn(self.makurdi_kin.name, frappe.get_list("DTMGP Next of Kin", pluck="name"))

	# ------------------------------------------------------------------ Staff Document

	def test_staff_document_read_and_list_are_denied_across_lga(self):
		frappe.set_user(self.gboko_hr.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Staff Document", self.makurdi_document.name)
		self.assertNotIn(self.makurdi_document.name, frappe.get_list("DTMGP Staff Document", pluck="name"))

	def test_staff_document_private_attachment_is_scoped_to_the_owning_documents_lga(self):
		frappe.set_user("Administrator")
		attachment = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "appointment-letter.txt",
				"content": "confidential personnel document",
				"is_private": 1,
				"attached_to_doctype": "DTMGP Staff Document",
				"attached_to_name": self.makurdi_document.name,
			}
		).insert(ignore_permissions=True)

		self.assertFalse(file_has_permission(attachment, ptype="read", user=self.gboko_hr.name))
		self.assertTrue(file_has_permission(attachment, ptype="read", user=self.makurdi_hr.name))

	# ----------------------------------------------------------------------- fixtures

	def _make_employee(self, company):
		return frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": f"Isolation Test Staff {uuid4().hex[:6]}",
				"company": company,
				"status": "Active",
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
			}
		).insert(ignore_permissions=True)

	def _make_personnel_file(self, company, employee):
		return frappe.get_doc(
			{
				"doctype": "DTMGP Personnel File",
				"company": company,
				"employee": employee,
				"file_status": "Active",
				"classification": "Restricted",
				"retention_category": "Personnel record",
			}
		).insert(ignore_permissions=True)

	def _make_next_of_kin(self, company, employee):
		return frappe.get_doc(
			{
				"doctype": "DTMGP Next of Kin",
				"company": company,
				"employee": employee,
				"full_name": "Isolation Test Contact",
				"relationship": "Spouse",
				"phone": "08000000000",
			}
		).insert(ignore_permissions=True)

	def _make_staff_document(self, company, employee):
		private_file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": f"isolation-test-{uuid4().hex[:6]}.txt",
				"content": "confidential personnel document",
				"is_private": 1,
			}
		).insert(ignore_permissions=True)
		return frappe.get_doc(
			{
				"doctype": "DTMGP Staff Document",
				"company": company,
				"employee": employee,
				"document_type": "Appointment Letter",
				"file": private_file.file_url,
				"classification": "Restricted",
				"retention_category": "Personnel record",
				"verification_status": "Pending",
			}
		).insert(ignore_permissions=True)

	def _make_user(self, role, company):
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": f"hr-iso-{uuid4().hex}@example.com",
				"first_name": "HR Isolation",
				"enabled": 1,
				"send_welcome_email": 0,
				"dtmgp_lga": company,
				"roles": [{"role": role}],
			}
		).insert()

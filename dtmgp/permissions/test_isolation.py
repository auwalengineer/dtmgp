from uuid import uuid4

import frappe
from frappe.client import get as client_get
from frappe.core.doctype.file.file import has_permission as file_has_permission
from frappe.tests.utils import FrappeTestCase

from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup

"""Stage 2 cross-LGA denial coverage that exercises the permission_query_conditions
and has_permission hooks directly (frappe.client.get, raw get_list, has_permission,
file access) rather than through dtmgp's own API guard functions, which are already
covered in test_finance_scope.py. This proves the hooks themselves hold for direct
document URLs, reports, exports and attachments, per the Stage 2 gate in
docs/role-permission-matrix.md ("Mandatory authorization tests")."""


class TestCrossLGAIsolation(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.makurdi_treasurer = self._make_user("Treasurer", self.makurdi)
		self.gboko_treasurer = self._make_user("Treasurer", self.gboko)
		self.gboko_auditor = self._make_user("Internal Auditor", self.gboko)
		self.makurdi_head = self._make_revenue_head(self.makurdi)
		self.gboko_head = self._make_revenue_head(self.gboko)
		self.makurdi_admin = self._make_user("LGA Administrator", self.makurdi)
		self.gboko_admin = self._make_user("LGA Administrator", self.gboko)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_direct_document_read_by_guessed_name_is_denied_across_lga(self):
		frappe.set_user(self.gboko_treasurer.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Revenue Head", self.makurdi_head.name)

		frappe.set_user(self.makurdi_treasurer.name)
		result = client_get("DTMGP Revenue Head", self.makurdi_head.name)
		self.assertEqual(result["name"], self.makurdi_head.name)

	def test_direct_user_read_by_guessed_name_is_denied_across_lga(self):
		"""System Administration's user-management reads (dtmgp/api/v1/users.py,
		dtmgp/api/v1/administration.py) are already covered for their own API-layer
		scoping (test_user_scope.py, test_administration.py) -- this proves the
		underlying dtmgp.permissions.user has_permission/get_permission_query_conditions
		hooks themselves deny a direct, guessed-name read of another LGA's User record,
		the same "Stage 2" guarantee test_isolation.py already gives Revenue Head."""
		frappe.set_user(self.gboko_admin.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("User", self.makurdi_admin.name)

		frappe.set_user(self.makurdi_admin.name)
		result = client_get("User", self.makurdi_admin.name)
		self.assertEqual(result["name"], self.makurdi_admin.name)

	def test_direct_write_is_denied_across_lga_even_without_the_api_layer(self):
		frappe.set_user(self.gboko_treasurer.name)
		doc = frappe.get_doc("DTMGP Revenue Head", self.makurdi_head.name)
		doc.revenue_name = "Tampered"
		with self.assertRaises(frappe.PermissionError):
			doc.save()

	def test_submit_and_cancel_are_denied_across_lga(self):
		frappe.set_user("Administrator")
		assessment = frappe.get_doc(
			{
				"doctype": "DTMGP Revenue Assessment",
				"company": self.makurdi,
				"revenue_head": self.makurdi_head.name,
				"taxpayer_name": "Cross LGA Test",
				"assessment_date": "2026-09-16",
				"due_date": "2026-09-30",
				"amount": 1000,
			}
		).insert(ignore_permissions=True)

		frappe.set_user(self.gboko_treasurer.name)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc("DTMGP Revenue Assessment", assessment.name).submit()

		frappe.set_user("Administrator")
		submitted = frappe.get_doc("DTMGP Revenue Assessment", assessment.name)
		submitted.flags.ignore_permissions = True
		submitted.submit()

		frappe.set_user(self.gboko_treasurer.name)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc("DTMGP Revenue Assessment", assessment.name).cancel()

	def test_report_and_list_queries_exclude_other_lga_records_without_api_help(self):
		frappe.set_user(self.gboko_treasurer.name)
		names = frappe.get_list("DTMGP Revenue Head", pluck="name")
		self.assertIn(self.gboko_head.name, names)
		self.assertNotIn(self.makurdi_head.name, names)

		exists_in_db = frappe.db.count("DTMGP Revenue Head", filters={"name": self.makurdi_head.name})
		self.assertEqual(exists_in_db, 1)  # the row exists...
		visible = frappe.get_list("DTMGP Revenue Head", filters={"name": self.makurdi_head.name}, ignore_permissions=False)
		self.assertEqual(visible, [])  # ...but the permission-aware query hides it

	def test_export_permission_is_denied_across_lga_even_when_the_role_allows_export(self):
		# Internal Auditor has doctype-level export=1, but the has_permission hook must
		# still deny it for a document outside the auditor's assigned LGA.
		self.assertFalse(frappe.has_permission("DTMGP Revenue Head", "export", doc=self.makurdi_head.name, user=self.gboko_auditor.name))
		self.assertTrue(frappe.has_permission("DTMGP Revenue Head", "export", doc=self.gboko_head.name, user=self.gboko_auditor.name))

	def test_private_attachment_is_scoped_to_the_owning_documents_lga(self):
		frappe.set_user("Administrator")
		attachment = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "evidence.txt",
				"content": "confidential",
				"is_private": 1,
				"attached_to_doctype": "DTMGP Revenue Head",
				"attached_to_name": self.makurdi_head.name,
			}
		).insert(ignore_permissions=True)

		self.assertFalse(file_has_permission(attachment, ptype="read", user=self.gboko_treasurer.name))
		self.assertTrue(file_has_permission(attachment, ptype="read", user=self.makurdi_treasurer.name))

	def _make_revenue_head(self, company):
		return frappe.get_doc(
			{
				"doctype": "DTMGP Revenue Head",
				"company": company,
				"revenue_code": f"ISO-{uuid4().hex[:6]}",
				"revenue_name": "Isolation Test Head",
				"legal_authority": "Test",
				"rate_type": "Fixed",
				"default_rate": 100,
				"valid_from": "2026-01-01",
				"approval_status": "Approved",
			}
		).insert(ignore_permissions=True)

	def _make_user(self, role, company):
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": f"iso-{uuid4().hex}@example.com",
				"first_name": "Isolation",
				"enabled": 1,
				"send_welcome_email": 0,
				"dtmgp_lga": company,
				"roles": [{"role": role}],
			}
		).insert()

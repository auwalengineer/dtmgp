from uuid import uuid4

import frappe
from frappe.client import get as client_get
from frappe.core.doctype.file.file import has_permission as file_has_permission
from frappe.tests.utils import FrappeTestCase

from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup

"""Stage 2 cross-LGA denial coverage for the Finance, Revenue & Procurement doctypes
that dtmgp/permissions/test_finance_scope.py only exercises through the dtmgp.api.v1.
finance wrapper functions -- this proves the permission_query_conditions/has_permission
hooks themselves (dtmgp/permissions/finance.py) hold for direct document URLs, raw
list/report queries, exports and attachments, mirroring dtmgp/permissions/
test_isolation.py and test_projects_isolation.py. Closes the "extend the same
direct-hook coverage to procurement and audit-query record types" gap noted in
docs/implementation-status.md's FND-005 row."""


class TestFinanceCrossLGAIsolation(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.makurdi_officer = self._make_user("Procurement Officer", self.makurdi)
		self.gboko_officer = self._make_user("Procurement Officer", self.gboko)
		self.gboko_auditor = self._make_user("Internal Auditor", self.gboko)
		self.makurdi_plan = self._make_procurement_plan(self.makurdi)
		self.gboko_plan = self._make_procurement_plan(self.gboko)
		self.makurdi_case = self._make_procurement_case(self.makurdi, self.makurdi_plan.name)
		self.gboko_case = self._make_procurement_case(self.gboko, self.gboko_plan.name)
		self.makurdi_query = self._make_audit_query(self.makurdi)
		self.gboko_query = self._make_audit_query(self.gboko)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	# ---------------------------------------------------------------- Procurement Plan

	def test_procurement_plan_read_and_list_are_denied_across_lga(self):
		frappe.set_user(self.gboko_officer.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Procurement Plan", self.makurdi_plan.name)
		self.assertNotIn(self.makurdi_plan.name, frappe.get_list("DTMGP Procurement Plan", pluck="name"))

		frappe.set_user(self.makurdi_officer.name)
		result = client_get("DTMGP Procurement Plan", self.makurdi_plan.name)
		self.assertEqual(result["name"], self.makurdi_plan.name)

	def test_procurement_plan_direct_write_is_denied_across_lga(self):
		frappe.set_user(self.gboko_officer.name)
		doc = frappe.get_doc("DTMGP Procurement Plan", self.makurdi_plan.name)
		doc.title = "Tampered"
		with self.assertRaises(frappe.PermissionError):
			doc.save()

	# ---------------------------------------------------------------- Procurement Case

	def test_procurement_case_read_and_list_are_denied_across_lga(self):
		frappe.set_user(self.gboko_officer.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Procurement Case", self.makurdi_case.name)
		self.assertNotIn(self.makurdi_case.name, frappe.get_list("DTMGP Procurement Case", pluck="name"))

		frappe.set_user(self.makurdi_officer.name)
		result = client_get("DTMGP Procurement Case", self.makurdi_case.name)
		self.assertEqual(result["name"], self.makurdi_case.name)

	def test_procurement_case_direct_write_is_denied_across_lga(self):
		frappe.set_user(self.gboko_officer.name)
		doc = frappe.get_doc("DTMGP Procurement Case", self.makurdi_case.name)
		doc.title = "Tampered"
		with self.assertRaises(frappe.PermissionError):
			doc.save()

	def test_procurement_case_export_permission_is_denied_across_lga_even_when_the_role_allows_export(self):
		# Internal Auditor has doctype-level export=1 on DTMGP Procurement Case, but the
		# has_permission hook must still deny it for a case outside the auditor's LGA.
		self.assertFalse(frappe.has_permission("DTMGP Procurement Case", "export", doc=self.makurdi_case.name, user=self.gboko_auditor.name))
		self.assertTrue(frappe.has_permission("DTMGP Procurement Case", "export", doc=self.gboko_case.name, user=self.gboko_auditor.name))

	def test_procurement_case_private_attachment_is_scoped_to_the_owning_documents_lga(self):
		frappe.set_user("Administrator")
		attachment = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "evaluation-report.txt",
				"content": "confidential bid evaluation",
				"is_private": 1,
				"attached_to_doctype": "DTMGP Procurement Case",
				"attached_to_name": self.makurdi_case.name,
			}
		).insert(ignore_permissions=True)

		self.assertFalse(file_has_permission(attachment, ptype="read", user=self.gboko_officer.name))
		self.assertTrue(file_has_permission(attachment, ptype="read", user=self.makurdi_officer.name))

	# --------------------------------------------------------------------- Audit Query

	def test_audit_query_read_and_list_are_denied_across_lga(self):
		frappe.set_user(self.gboko_auditor.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Audit Query", self.makurdi_query.name)
		self.assertNotIn(self.makurdi_query.name, frappe.get_list("DTMGP Audit Query", pluck="name"))

		result = client_get("DTMGP Audit Query", self.gboko_query.name)
		self.assertEqual(result["name"], self.gboko_query.name)

	def test_audit_query_direct_write_is_denied_across_lga(self):
		frappe.set_user(self.gboko_auditor.name)
		doc = frappe.get_doc("DTMGP Audit Query", self.makurdi_query.name)
		doc.subject = "Tampered"
		with self.assertRaises(frappe.PermissionError):
			doc.save()

	def test_audit_query_export_permission_is_denied_across_lga_even_when_the_role_allows_export(self):
		# Internal Auditor has doctype-level export=1 on DTMGP Audit Query, but the
		# has_permission hook must still deny it for a query outside the auditor's LGA.
		self.assertFalse(frappe.has_permission("DTMGP Audit Query", "export", doc=self.makurdi_query.name, user=self.gboko_auditor.name))
		self.assertTrue(frappe.has_permission("DTMGP Audit Query", "export", doc=self.gboko_query.name, user=self.gboko_auditor.name))

	def test_audit_query_private_attachment_is_scoped_to_the_owning_documents_lga(self):
		frappe.set_user("Administrator")
		attachment = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "supporting-evidence.txt",
				"content": "confidential audit evidence",
				"is_private": 1,
				"attached_to_doctype": "DTMGP Audit Query",
				"attached_to_name": self.makurdi_query.name,
			}
		).insert(ignore_permissions=True)

		self.assertFalse(file_has_permission(attachment, ptype="read", user=self.gboko_auditor.name))

	# ----------------------------------------------------------------------- fixtures

	def _make_procurement_plan(self, company):
		fiscal_year = frappe.get_all("Fiscal Year", filters={"disabled": 0}, pluck="name", limit=1)[0]
		department = frappe.get_all("Department", filters={"company": company}, pluck="name", limit=1)
		if not department:
			department = [frappe.get_doc({"doctype": "Department", "department_name": f"Isolation Test {uuid4().hex[:6]}", "company": company}).insert(ignore_permissions=True).name]
		account = frappe.get_all("Account", filters={"company": company, "is_group": 0}, pluck="name", limit=1)[0]
		return frappe.get_doc(
			{
				"doctype": "DTMGP Procurement Plan",
				"company": company,
				"fiscal_year": fiscal_year,
				"title": f"Isolation Plan {uuid4().hex[:6]}",
				"requesting_department": department[0],
				"procurement_category": "Works",
				"procurement_method": "Open Competitive Bidding",
				"estimated_amount": 500000,
				"budget_account": account,
				"planned_start_date": "2026-09-16",
				"planned_end_date": "2026-12-31",
				"description": "Isolation test plan",
			}
		).insert(ignore_permissions=True)

	def _make_procurement_case(self, company, plan_name):
		return frappe.get_doc(
			{
				"doctype": "DTMGP Procurement Case",
				"company": company,
				"title": f"Isolation Case {uuid4().hex[:6]}",
				"procurement_plan": plan_name,
				"estimated_amount": 500000,
				"applicable_threshold": "Test threshold",
				"procurement_committee": "Test committee minute",
				"description": "Isolation test case",
			}
		).insert(ignore_permissions=True)

	def _make_audit_query(self, company):
		return frappe.get_doc(
			{
				"doctype": "DTMGP Audit Query",
				"company": company,
				"query_date": "2026-09-16",
				"query_type": "Finance",
				"severity": "Medium",
				"subject": f"Isolation Query {uuid4().hex[:6]}",
				"finding": "Isolation test finding",
				"assigned_to": "Administrator",
				"response_due_date": "2026-09-30",
			}
		).insert(ignore_permissions=True)

	def _make_user(self, role, company):
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": f"finance-iso-{uuid4().hex}@example.com",
				"first_name": "Finance Isolation",
				"enabled": 1,
				"send_welcome_email": 0,
				"dtmgp_lga": company,
				"roles": [{"role": role}],
			}
		).insert()

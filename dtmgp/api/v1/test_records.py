from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.records import _serialize_fields, get_record, get_record_timeline
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup


class TestRecordDetails(FrappeTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_unknown_doctype_is_denied(self):
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.PermissionError):
			get_record("User", "Administrator")

	def test_guest_cannot_read_allowed_doctype(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.AuthenticationError):
			get_record("Employee", "missing")

	def test_employee_dto_excludes_restricted_personal_fields(self):
		doc = frappe._dict({
			"doctype": "Employee", "employee_name": "Test Officer", "company": "Test LGA",
			"date_of_birth": "1990-01-01", "bank_ac_no": "1234567890", "personal_email": "private@example.com",
		})
		fieldnames = {
			field["label"]
			for section in _serialize_fields(doc, frappe.get_meta("Employee"))
			for field in section["fields"]
		}
		self.assertIn("Full Name", fieldnames)
		self.assertIn("LGA", fieldnames)
		self.assertNotIn("Company", fieldnames)
		self.assertNotIn("Date of Birth", fieldnames)
		self.assertNotIn("Bank Account No", fieldnames)
		self.assertNotIn("Personal Email", fieldnames)
		self.assertTrue(any(section["label"] == "LGA Details" for section in _serialize_fields(doc, frappe.get_meta("Employee"))))

	def test_get_record_timeline_returns_this_records_own_audit_events_and_is_scoped(self):
		"""DTMGP Audit Event's own doctype permissions restrict read to audit roles
		(Internal Auditor, State Auditor/Administrator); get_record_timeline must still
		let an ordinary business-role user (here, Procurement Officer) see their own
		record's history, since they already proved they can read the record itself --
		but not another LGA's record."""
		frappe.set_user("Administrator")
		seed_security_setup()
		makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		officer = self._make_user("Procurement Officer", makurdi)
		plan = self._make_procurement_plan(makurdi)
		gboko_plan = self._make_procurement_plan(gboko)

		frappe.set_user(officer.name)
		timeline = get_record_timeline("DTMGP Procurement Plan", plan.name)
		self.assertTrue(timeline["items"])
		self.assertTrue(any(event["event_type"] for event in timeline["items"]))

		with self.assertRaises(frappe.PermissionError):
			get_record_timeline("DTMGP Procurement Plan", gboko_plan.name)

	def _make_procurement_plan(self, company):
		fiscal_year = frappe.get_all("Fiscal Year", filters={"disabled": 0}, pluck="name", limit=1)[0]
		department = frappe.get_all("Department", filters={"company": company}, pluck="name", limit=1)
		if not department:
			department = [frappe.get_doc({"doctype": "Department", "department_name": f"Timeline Test {uuid4().hex[:6]}", "company": company}).insert(ignore_permissions=True).name]
		account = frappe.get_all("Account", filters={"company": company, "is_group": 0}, pluck="name", limit=1)[0]
		return frappe.get_doc(
			{
				"doctype": "DTMGP Procurement Plan",
				"company": company,
				"fiscal_year": fiscal_year,
				"title": f"Timeline Plan {uuid4().hex[:6]}",
				"requesting_department": department[0],
				"procurement_category": "Works",
				"procurement_method": "Open Competitive Bidding",
				"estimated_amount": 500000,
				"budget_account": account,
				"description": "Timeline test plan",
			}
		).insert(ignore_permissions=True)

	def _make_user(self, role, company):
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": f"records-timeline-{uuid4().hex}@example.com",
				"first_name": "Records Timeline",
				"enabled": 1,
				"send_welcome_email": 0,
				"dtmgp_lga": company,
				"roles": [{"role": role}],
			}
		).insert()

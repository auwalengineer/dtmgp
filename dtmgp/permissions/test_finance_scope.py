from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.finance import get_dashboard, list_records, save_record, submit_record, transition_record
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup


class TestFinanceScope(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.treasurer = self._make_user("Treasurer", self.makurdi)
		self.hr_officer = self._make_user("HR Officer", self.makurdi)
		self.chairman = self._make_user("LGA Chairman", self.makurdi)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_treasurer_creates_and_lists_only_assigned_lga_assessments(self):
		frappe.set_user(self.treasurer.name)
		head = save_record("DTMGP Revenue Head", {
			"company": self.makurdi, "revenue_code": f"MKT-{uuid4().hex[:6]}",
			"revenue_name": "Market Stall Fee", "legal_authority": "Approved council rate",
			"collection_frequency": "Annually", "rate_type": "Fixed", "default_rate": 5000,
		})
		assessment = save_record("DTMGP Revenue Assessment", {
			"company": self.makurdi, "revenue_head": head["name"], "taxpayer_name": "Test Payer",
			"assessment_date": "2026-09-16", "due_date": "2026-09-30", "amount": 5000,
		})
		submit_record("DTMGP Revenue Assessment", assessment["name"])

		result = list_records("DTMGP Revenue Assessment", self.makurdi, search="Test Payer")
		self.assertEqual(result["items"][0].company, self.makurdi)
		self.assertEqual(result["items"][0].status, "Unpaid")
		self.assertEqual(get_dashboard(self.makurdi)["revenue"]["assessed"], 5000)

	def test_cross_lga_access_is_rejected(self):
		frappe.set_user(self.treasurer.name)
		with self.assertRaises(frappe.PermissionError):
			list_records("DTMGP Revenue Assessment", self.gboko)
		with self.assertRaises(frappe.PermissionError):
			save_record("DTMGP Revenue Head", {
				"company": self.gboko, "revenue_code": "OUTSIDE", "revenue_name": "Outside",
				"legal_authority": "Test", "rate_type": "Fixed",
			})

	def test_non_finance_role_cannot_access_api(self):
		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			get_dashboard(self.makurdi)

	def test_approval_transition_requires_amount_limit(self):
		frappe.set_user("Administrator")
		department = frappe.get_all("Department", filters={"company": self.makurdi}, pluck="name", limit=1)
		if not department:
			department = [frappe.get_doc({"doctype": "Department", "department_name": f"Finance Test {uuid4().hex[:6]}", "company": self.makurdi}).insert().name]
		expense_account = frappe.get_all("Account", filters={"company": self.makurdi, "is_group": 0}, pluck="name", limit=1)[0]
		cost_center = frappe.get_all("Cost Center", filters={"company": self.makurdi, "is_group": 0}, pluck="name", limit=1)[0]
		request = frappe.get_doc({
			"doctype": "DTMGP Payment Request", "company": self.makurdi, "request_date": "2026-09-16",
			"requesting_department": department[0], "payee_type": "Other", "payee": "Test Payee",
			"description": "Test controlled payment", "amount": 1000, "expense_account": expense_account,
			"cost_center": cost_center, "justification": "Test", "status": "Pending Approval",
		}).insert(ignore_permissions=True)
		frappe.set_user(self.chairman.name)
		with self.assertRaises(frappe.PermissionError):
			transition_record("DTMGP Payment Request", request.name, "Approved")

		frappe.set_user("Administrator")
		frappe.get_doc({
			"doctype": "DTMGP Approval Limit", "company": self.makurdi, "transaction_type": "Payment Request",
			"approving_role": "LGA Chairman", "minimum_amount": 0, "maximum_amount": 5000, "active": 1,
		}).insert(ignore_permissions=True)
		frappe.set_user(self.chairman.name)
		self.assertEqual(transition_record("DTMGP Payment Request", request.name, "Approved")["status"], "Approved")

	def _make_user(self, role, company):
		return frappe.get_doc({
			"doctype": "User", "email": f"finance-{uuid4().hex}@example.com", "first_name": "Finance",
			"enabled": 1, "send_welcome_email": 0, "dtmgp_lga": company, "roles": [{"role": role}],
		}).insert()

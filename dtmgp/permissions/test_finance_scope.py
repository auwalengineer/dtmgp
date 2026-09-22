from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.finance import (
	get_budget_performance,
	get_dashboard,
	list_allocations,
	list_budgets,
	list_records,
	save_budget,
	save_record,
	submit_budget,
	submit_record,
	transition_record,
)
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
		self.procurement_officer = self._make_user("Procurement Officer", self.makurdi)

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

	def test_approval_limit_is_cross_lga_scoped(self):
		"""DTMGP Approval Limit is consumed by _validate_approval_limit but, until
		System Administration's Workflow Setup section, had no CRUD surface at all."""
		frappe.set_user(self.treasurer.name)
		limit = save_record("DTMGP Approval Limit", {
			# A distinct, inactive transaction_type/amount band so this doesn't
			# accidentally satisfy test_approval_transition_requires_amount_limit's
			# "no limit exists yet" assertion -- FrappeTestCase shares one
			# uncommitted transaction across every test in this class (rollback is
			# class-scoped, not per-test), so records created here are still visible
			# to tests that run later in the same class.
			"company": self.makurdi, "transaction_type": "Revenue Adjustment",
			"approving_role": "LGA Chairman", "minimum_amount": 0, "maximum_amount": 500000, "active": 1,
		})
		try:
			result = list_records("DTMGP Approval Limit", self.makurdi)
			self.assertIn(limit["name"], {item.name for item in result["items"]})

			with self.assertRaises(frappe.PermissionError):
				list_records("DTMGP Approval Limit", self.gboko)
			with self.assertRaises(frappe.PermissionError):
				save_record("DTMGP Approval Limit", {
					"company": self.gboko, "transaction_type": "Revenue Adjustment",
					"approving_role": "LGA Chairman", "minimum_amount": 0, "maximum_amount": 100,
				})
		finally:
			frappe.set_user("Administrator")
			frappe.delete_doc("DTMGP Approval Limit", limit["name"], force=1)

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

	def test_allocation_scope_and_transition(self):
		frappe.set_user(self.treasurer.name)
		fiscal_year = frappe.get_all("Fiscal Year", filters={"disabled": 0}, pluck="name", limit=1)[0]
		allocation = save_record("DTMGP Allocation", {
			"company": self.makurdi, "fiscal_year": fiscal_year, "tier": "Federal Allocation",
			"source": "FAAC", "tranche_period": "September 2026", "amount": 100000,
		})
		self.assertEqual(transition_record("DTMGP Allocation", allocation["name"], "Received")["status"], "Received")

		with self.assertRaises(frappe.PermissionError):
			list_allocations(self.gboko)
		with self.assertRaises(frappe.PermissionError):
			save_record("DTMGP Allocation", {
				"company": self.gboko, "fiscal_year": fiscal_year, "tier": "Federal Allocation",
				"source": "FAAC", "tranche_period": "September 2026", "amount": 100000,
			})

		self.assertEqual(list_allocations(self.makurdi)["items"][0]["company"], self.makurdi)

	def test_contract_and_variation_scope(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("Supplier", {"supplier_name": "Test Finance Contractor"}):
			supplier = frappe.get_doc({
				"doctype": "Supplier", "supplier_name": "Test Finance Contractor", "supplier_type": "Company",
			}).insert(ignore_permissions=True)
		else:
			supplier = frappe.get_doc("Supplier", {"supplier_name": "Test Finance Contractor"})

		# Procurement Case and Contract are Procurement-Officer-created, Treasurer-approved
		# doctypes (mirrors the existing DTMGP Procurement Case permission asymmetry).
		frappe.set_user(self.procurement_officer.name)
		fiscal_year = frappe.get_all("Fiscal Year", filters={"disabled": 0}, pluck="name", limit=1)[0]
		plan = save_record("DTMGP Procurement Plan", {
			"company": self.makurdi, "fiscal_year": fiscal_year, "title": f"Plan {uuid4().hex[:6]}",
			"requesting_department": frappe.get_all("Department", filters={"company": self.makurdi}, pluck="name", limit=1)[0],
			"procurement_category": "Works", "procurement_method": "Open Competitive Bidding",
			"estimated_amount": 500000, "budget_account": frappe.get_all("Account", filters={"company": self.makurdi, "is_group": 0}, pluck="name", limit=1)[0],
			"planned_start_date": "2026-09-16", "planned_end_date": "2026-12-31", "description": "Test",
		})
		case = save_record("DTMGP Procurement Case", {
			"company": self.makurdi, "title": f"Case {uuid4().hex[:6]}", "procurement_plan": plan["name"],
			"estimated_amount": 500000, "description": "Test",
		})

		contract = save_record("DTMGP Contract", {
			"company": self.makurdi, "title": f"Contract {uuid4().hex[:6]}", "procurement_case": case["name"],
			"contractor": supplier.name, "contract_value": 500000, "start_date": "2026-09-16",
		})
		self.assertEqual(transition_record("DTMGP Contract", contract["name"], "Active")["status"], "Active")

		variation = save_record("DTMGP Contract Variation", {
			"company": self.makurdi, "contract": contract["name"], "variation_type": "Cost Variation",
			"amount_change": 50000, "description": "Additional scope",
		})
		transition_record("DTMGP Contract Variation", variation["name"], "Pending Approval")
		with self.assertRaises(frappe.PermissionError):
			transition_record("DTMGP Contract Variation", variation["name"], "Approved")

		frappe.set_user("Administrator")
		frappe.get_doc({
			"doctype": "DTMGP Approval Limit", "company": self.makurdi, "transaction_type": "Contract Variation",
			"approving_role": "Treasurer", "minimum_amount": 0, "maximum_amount": 100000, "active": 1,
		}).insert(ignore_permissions=True)
		frappe.set_user(self.treasurer.name)
		self.assertEqual(transition_record("DTMGP Contract Variation", variation["name"], "Approved")["status"], "Approved")

		frappe.set_user(self.procurement_officer.name)
		with self.assertRaises(frappe.PermissionError):
			save_record("DTMGP Contract", {
				"company": self.gboko, "title": "Outside", "procurement_case": case["name"],
				"contractor": supplier.name, "contract_value": 500000, "start_date": "2026-09-16",
			})

	def test_budget_scope_and_submit(self):
		frappe.set_user(self.treasurer.name)
		fiscal_year = frappe.get_all("Fiscal Year", filters={"disabled": 0}, pluck="name", limit=1)[0]
		cost_center = frappe.get_all("Cost Center", filters={"company": self.makurdi, "is_group": 0}, pluck="name", limit=1)[0]
		account = frappe.get_all("Account", filters={"company": self.makurdi, "is_group": 0, "root_type": "Expense"}, pluck="name", limit=1)[0]
		budget = save_budget(
			self.makurdi, fiscal_year, "Cost Center", cost_center=cost_center,
			accounts=[{"account": account, "budget_amount": 250000}],
		)
		self.assertEqual(submit_budget(budget["name"])["docstatus"], 1)
		self.assertEqual(list_budgets(self.makurdi)["items"][0]["company"], self.makurdi)
		self.assertEqual(get_budget_performance(self.makurdi, fiscal_year)["rows"][0]["account"], account)

		with self.assertRaises(frappe.PermissionError):
			save_budget(self.gboko, fiscal_year, "Cost Center", cost_center=cost_center, accounts=[])

	def _make_user(self, role, company):
		return frappe.get_doc({
			"doctype": "User", "email": f"finance-{uuid4().hex}@example.com", "first_name": "Finance",
			"enabled": 1, "send_welcome_email": 0, "dtmgp_lga": company, "roles": [{"role": role}],
		}).insert()

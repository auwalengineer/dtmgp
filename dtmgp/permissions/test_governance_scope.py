from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.governance import (
	get_approvals_inbox,
	get_dashboard,
	get_form_options,
	get_reports,
	list_departments,
	list_records,
	save_department,
	save_record,
	transition_record,
)
from dtmgp.setup.governance import seed_governance_catalogue
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup


class TestGovernanceScope(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		seed_governance_catalogue()
		for doctype in ("DTMGP Statutory Return Type", "DTMGP Compliance Requirement"):
			frappe.db.set_value(doctype, {}, {"approval_status": "Approved", "legal_authority": "Test authority", "effective_from": "2026-01-01"})
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.secretary = self._make_user("LGA Secretary", self.makurdi)
		self.gboko_secretary = self._make_user("LGA Secretary", self.gboko)
		self.treasurer = self._make_user("Treasurer", self.makurdi)
		self.chairman = self._make_user("LGA Chairman", self.makurdi)
		self.state_auditor = self._make_user("State Auditor", self.makurdi)

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

	def test_meeting_resolution_and_action_lifecycle(self):
		frappe.set_user(self.secretary.name)
		meeting = save_record("DTMGP Meeting", {
			"company": self.makurdi, "meeting_type": "Council", "title": "Sept Council Meeting", "meeting_date": "2026-09-21",
		})
		self.assertTrue(meeting["name"].startswith("CM-MKD-2026-"))
		resolution = save_record("DTMGP Resolution", {
			"company": self.makurdi, "meeting": meeting["name"], "title": "Approve market renovation",
			"category": "Financial", "resolution_text": "Resolved to renovate the central market.",
		})
		self.assertTrue(resolution["name"].startswith("RES-MKD-2026-"))

		# Adoption requires LGA Chairman/Administrator, not the Secretary who proposed it.
		with self.assertRaises(frappe.PermissionError):
			transition_record("DTMGP Resolution", resolution["name"], "Adopted")

		frappe.set_user(self.chairman.name)
		self.assertEqual(transition_record("DTMGP Resolution", resolution["name"], "Adopted")["status"], "Adopted")
		self.assertIsNotNone(frappe.db.get_value("DTMGP Resolution", resolution["name"], "adopted_date"))

		frappe.set_user(self.secretary.name)
		action = save_record("DTMGP Resolution Action", {
			"company": self.makurdi, "resolution": resolution["name"], "action_description": "Prepare BOQ", "due_date": "2026-10-01",
		})
		self.assertEqual(transition_record("DTMGP Resolution Action", action["name"], "Completed")["status"], "Completed")
		self.assertIsNotNone(frappe.db.get_value("DTMGP Resolution Action", action["name"], "completed_date"))

		with self.assertRaises(frappe.PermissionError):
			save_record("DTMGP Resolution", {
				"company": self.gboko, "meeting": meeting["name"], "title": "Outside", "resolution_text": "x",
			})

	def test_statutory_return_final_review_requires_a_state_role(self):
		frappe.set_user(self.secretary.name)
		options = get_form_options(self.makurdi)
		return_type = next(item["name"] for item in options["return_types"] if item["frequency"] == "Quarterly")
		record = save_record("DTMGP Statutory Return", {"company": self.makurdi, "return_type": return_type, "period": "2026-Q3", "due_date": "2026-09-30"})
		self.assertTrue(record["name"].startswith("RET-MKD-2026-"))
		transition_record("DTMGP Statutory Return", record["name"], "Prepared")
		transition_record("DTMGP Statutory Return", record["name"], "Submitted")

		with self.assertRaises(frappe.PermissionError):
			transition_record("DTMGP Statutory Return", record["name"], "State Reviewed")

		frappe.set_user(self.state_auditor.name)
		self.assertEqual(transition_record("DTMGP Statutory Return", record["name"], "State Reviewed")["status"], "State Reviewed")
		self.assertGreaterEqual(get_reports(self.makurdi)["statutory_returns"]["submitted"], 1)

	def test_compliance_submission_verification_requires_audit_role(self):
		frappe.set_user(self.secretary.name)
		options = get_form_options(self.makurdi)
		requirement = options["compliance_requirements"][0]["name"]
		record = save_record("DTMGP Compliance Submission", {"company": self.makurdi, "requirement": requirement, "period": "2026-Q3", "due_date": "2026-09-30"})
		transition_record("DTMGP Compliance Submission", record["name"], "Submitted")

		with self.assertRaises(frappe.PermissionError):
			transition_record("DTMGP Compliance Submission", record["name"], "Verified")

		frappe.set_user(self.state_auditor.name)
		self.assertEqual(transition_record("DTMGP Compliance Submission", record["name"], "Verified")["status"], "Verified")

	def test_approval_delegation_lets_a_delegate_act_for_the_role(self):
		frappe.set_user(self.secretary.name)
		meeting = save_record("DTMGP Meeting", {"company": self.makurdi, "meeting_type": "Council", "title": "Delegation Test Meeting", "meeting_date": "2026-09-21"})
		resolution = save_record("DTMGP Resolution", {"company": self.makurdi, "meeting": meeting["name"], "title": "Delegated resolution", "resolution_text": "x"})

		# The Secretary has no adoption rights by role, and no delegation yet.
		with self.assertRaises(frappe.PermissionError):
			transition_record("DTMGP Resolution", resolution["name"], "Adopted")

		frappe.set_user("Administrator")
		frappe.get_doc({
			"doctype": "DTMGP Approval Delegation", "company": self.makurdi, "delegator": self.chairman.name,
			"delegate": self.secretary.name, "role": "LGA Chairman", "start_date": "2026-01-01", "end_date": "2026-12-31", "active": 1,
		}).insert(ignore_permissions=True)

		frappe.set_user(self.secretary.name)
		self.assertEqual(transition_record("DTMGP Resolution", resolution["name"], "Adopted")["status"], "Adopted")

	def test_approvals_inbox_is_scoped_by_role_and_lga(self):
		frappe.set_user(self.secretary.name)
		options = get_form_options(self.makurdi)
		return_type = options["return_types"][0]["name"]
		record = save_record("DTMGP Statutory Return", {"company": self.makurdi, "return_type": return_type, "period": "2026-Q3", "due_date": "2026-09-30"})
		transition_record("DTMGP Statutory Return", record["name"], "Prepared")
		transition_record("DTMGP Statutory Return", record["name"], "Submitted")

		# The Secretary proposed/submitted it but isn't the role that reviews it.
		secretary_inbox = get_approvals_inbox(self.makurdi)
		self.assertNotIn(record["name"], [item["name"] for item in secretary_inbox])

		frappe.set_user(self.state_auditor.name)
		auditor_inbox = get_approvals_inbox(self.makurdi)
		self.assertIn(record["name"], [item["name"] for item in auditor_inbox])

	def _make_user(self, role, company):
		return frappe.get_doc({
			"doctype": "User", "email": f"governance-{uuid4().hex}@example.com", "first_name": "Governance",
			"enabled": 1, "send_welcome_email": 0, "dtmgp_lga": company, "roles": [{"role": role}],
		}).insert()

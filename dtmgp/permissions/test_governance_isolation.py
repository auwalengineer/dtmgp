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
		self.makurdi_meeting = self._make_meeting(self.makurdi)
		self.makurdi_resolution = self._make_resolution(self.makurdi, self.makurdi_meeting.name)
		self.makurdi_action = self._make_resolution_action(self.makurdi, self.makurdi_resolution.name)
		self.makurdi_return = self._make_statutory_return(self.makurdi)
		self.makurdi_compliance = self._make_compliance_submission(self.makurdi)
		self.makurdi_delegation = self._make_delegation(self.makurdi)

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

	def _assert_denied_across_lga(self, doctype, name):
		frappe.set_user(self.gboko_secretary.name)
		with self.assertRaises(frappe.PermissionError):
			client_get(doctype, name)
		doc = frappe.get_doc(doctype, name)
		with self.assertRaises(frappe.PermissionError):
			doc.save()
		names = frappe.get_list(doctype, pluck="name")
		self.assertNotIn(name, names)

		frappe.set_user(self.makurdi_secretary.name)
		result = client_get(doctype, name)
		self.assertEqual(result["name"], name)

	def test_meeting_is_denied_across_lga(self):
		self._assert_denied_across_lga("DTMGP Meeting", self.makurdi_meeting.name)

	def test_resolution_is_denied_across_lga(self):
		self._assert_denied_across_lga("DTMGP Resolution", self.makurdi_resolution.name)

	def test_resolution_action_is_denied_across_lga(self):
		self._assert_denied_across_lga("DTMGP Resolution Action", self.makurdi_action.name)

	def test_statutory_return_is_denied_across_lga(self):
		self._assert_denied_across_lga("DTMGP Statutory Return", self.makurdi_return.name)

	def test_compliance_submission_is_denied_across_lga(self):
		self._assert_denied_across_lga("DTMGP Compliance Submission", self.makurdi_compliance.name)

	def test_approval_delegation_is_denied_across_lga(self):
		self._assert_denied_across_lga("DTMGP Approval Delegation", self.makurdi_delegation.name)

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

	def _make_meeting(self, company):
		return frappe.get_doc({
			"doctype": "DTMGP Meeting", "company": company, "meeting_type": "Council",
			"title": "Isolation Test Meeting", "meeting_date": "2026-09-21",
		}).insert(ignore_permissions=True)

	def _make_resolution(self, company, meeting):
		return frappe.get_doc({
			"doctype": "DTMGP Resolution", "company": company, "meeting": meeting,
			"title": "Isolation Test Resolution", "resolution_text": "x",
		}).insert(ignore_permissions=True)

	def _make_resolution_action(self, company, resolution):
		return frappe.get_doc({
			"doctype": "DTMGP Resolution Action", "company": company, "resolution": resolution,
			"action_description": "Isolation Test Action", "due_date": "2026-10-01",
		}).insert(ignore_permissions=True)

	def _make_statutory_return(self, company):
		return_type = frappe.db.exists("DTMGP Statutory Return Type", {"disabled": 0})
		if not return_type:
			return_type = frappe.get_doc({"doctype": "DTMGP Statutory Return Type", "return_name": f"Isolation Test Return {uuid4().hex[:6]}", "frequency": "Annually"}).insert(ignore_permissions=True).name
		return frappe.get_doc({
			"doctype": "DTMGP Statutory Return", "company": company, "return_type": return_type,
			"period": "2026-Q3", "due_date": "2026-09-30",
		}).insert(ignore_permissions=True)

	def _make_compliance_submission(self, company):
		requirement = frappe.db.exists("DTMGP Compliance Requirement", {"disabled": 0})
		if not requirement:
			requirement = frappe.get_doc({"doctype": "DTMGP Compliance Requirement", "requirement_name": f"Isolation Test Requirement {uuid4().hex[:6]}", "frequency": "Annually"}).insert(ignore_permissions=True).name
		return frappe.get_doc({
			"doctype": "DTMGP Compliance Submission", "company": company, "requirement": requirement,
			"period": "2026-Q3", "due_date": "2026-09-30",
		}).insert(ignore_permissions=True)

	def _make_delegation(self, company):
		return frappe.get_doc({
			"doctype": "DTMGP Approval Delegation", "company": company,
			"delegator": self.makurdi_secretary.name, "delegate": "Administrator", "role": "LGA Chairman",
			"start_date": "2026-01-01", "end_date": "2026-12-31", "active": 1,
		}).insert(ignore_permissions=True)

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

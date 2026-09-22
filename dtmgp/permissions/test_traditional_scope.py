from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.traditional import get_dashboard, list_records, save_record, transition_record, update_recognition
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup


class TestTraditionalScope(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.officer = self._make_user("Traditional Affairs Officer", self.makurdi)
		self.gboko_officer = self._make_user("Traditional Affairs Officer", self.gboko)
		self.read_only = self._make_user("Read-only Officer", self.makurdi)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_officer_creates_institution_and_ruler_in_own_lga(self):
		frappe.set_user(self.officer.name)
		institution = save_record("DTMGP Traditional Institution", {
			"company": self.makurdi, "institution_name": f"Test Stool {uuid4().hex[:6]}", "institution_type": "District Headship", "status": "Vacant",
		})
		self.assertTrue(institution["name"].startswith("INST-MKD-"))

		ruler = save_record("DTMGP Traditional Ruler", {
			"company": self.makurdi, "ruler_name": "Test Ruler", "institution": institution["name"], "appointment_date": "2026-01-01",
		})
		self.assertTrue(ruler["name"].startswith("RUL-MKD-"))

		result = list_records("DTMGP Traditional Ruler", self.makurdi, search="Test Ruler")
		self.assertEqual(result["items"][0].institution, institution["name"])
		self.assertEqual(get_dashboard(self.makurdi)["reigning_rulers"], 1)

	def test_second_reigning_ruler_on_same_institution_is_rejected(self):
		frappe.set_user(self.officer.name)
		institution = save_record("DTMGP Traditional Institution", {
			"company": self.makurdi, "institution_name": f"Test Stool {uuid4().hex[:6]}", "institution_type": "District Headship", "status": "Active",
		})
		save_record("DTMGP Traditional Ruler", {"company": self.makurdi, "ruler_name": "First Ruler", "institution": institution["name"], "appointment_date": "2020-01-01"})
		with self.assertRaises(frappe.ValidationError):
			save_record("DTMGP Traditional Ruler", {"company": self.makurdi, "ruler_name": "Second Ruler", "institution": institution["name"], "appointment_date": "2026-01-01"})

	def test_appointment_advances_through_the_full_chain_and_requires_gazette_reference(self):
		frappe.set_user(self.officer.name)
		institution = save_record("DTMGP Traditional Institution", {
			"company": self.makurdi, "institution_name": f"Test Stool {uuid4().hex[:6]}", "institution_type": "District Headship", "status": "Vacant",
		})
		appointment = save_record("DTMGP Traditional Appointment", {
			"company": self.makurdi, "institution": institution["name"], "candidate_name": "Test Candidate", "application_date": "2026-01-01",
		})
		for target in ["Kingmakers Selection", "Council Endorsed", "Ministry Vetting", "Exco Approved", "Governor Approved"]:
			self.assertEqual(transition_record("DTMGP Traditional Appointment", appointment["name"], target)["status"], target)

		with self.assertRaises(frappe.ValidationError):
			transition_record("DTMGP Traditional Appointment", appointment["name"], "Gazetted")

		save_record("DTMGP Traditional Appointment", {"gazette_reference": "GAZ-2026-001"}, name=appointment["name"])
		self.assertEqual(transition_record("DTMGP Traditional Appointment", appointment["name"], "Gazetted")["status"], "Gazetted")
		self.assertEqual(transition_record("DTMGP Traditional Appointment", appointment["name"], "Installed")["status"], "Installed")

		with self.assertRaises(frappe.ValidationError):
			transition_record("DTMGP Traditional Appointment", appointment["name"], "Nominated")

	def test_appointment_recognition_can_be_suspended_with_a_reason(self):
		frappe.set_user(self.officer.name)
		institution = save_record("DTMGP Traditional Institution", {
			"company": self.makurdi, "institution_name": f"Test Stool {uuid4().hex[:6]}", "institution_type": "District Headship", "status": "Vacant",
		})
		appointment = save_record("DTMGP Traditional Appointment", {
			"company": self.makurdi, "institution": institution["name"], "candidate_name": "Test Candidate", "application_date": "2026-01-01",
		})
		result = update_recognition(appointment["name"], "Suspended", reason="Under investigation")
		self.assertEqual(result["recognition_status"], "Suspended")

	def test_petition_and_allowance_transitions(self):
		frappe.set_user(self.officer.name)
		institution = save_record("DTMGP Traditional Institution", {
			"company": self.makurdi, "institution_name": f"Test Stool {uuid4().hex[:6]}", "institution_type": "District Headship", "status": "Active",
		})
		petition = save_record("DTMGP Chieftaincy Petition", {
			"company": self.makurdi, "institution": institution["name"], "petitioner_name": "Test Petitioner",
			"petition_type": "Rival Claim", "petition_date": "2026-01-01", "description": "Test description",
		})
		self.assertEqual(transition_record("DTMGP Chieftaincy Petition", petition["name"], "Council Hearing")["status"], "Council Hearing")

		ruler = save_record("DTMGP Traditional Ruler", {"company": self.makurdi, "ruler_name": "Allowance Ruler", "institution": institution["name"], "appointment_date": "2020-01-01"})
		allowance = save_record("DTMGP Traditional Allowance", {
			"company": self.makurdi, "ruler": ruler["name"], "allowance_type": "Stipend", "amount": 50000, "period_start": "2026-01-01", "period_end": "2026-01-31",
		})
		self.assertEqual(transition_record("DTMGP Traditional Allowance", allowance["name"], "Approved")["status"], "Approved")
		self.assertEqual(transition_record("DTMGP Traditional Allowance", allowance["name"], "Paid")["status"], "Paid")

	def test_cross_lga_access_is_rejected(self):
		frappe.set_user(self.officer.name)
		institution = save_record("DTMGP Traditional Institution", {
			"company": self.makurdi, "institution_name": f"Test Stool {uuid4().hex[:6]}", "institution_type": "District Headship", "status": "Active",
		})
		frappe.set_user(self.gboko_officer.name)
		with self.assertRaises(frappe.PermissionError):
			list_records("DTMGP Traditional Institution", self.makurdi)
		with self.assertRaises(frappe.PermissionError):
			save_record("DTMGP Traditional Institution", {"company": self.makurdi, "institution_name": "Outside", "institution_type": "District Headship", "status": "Active"})
		with self.assertRaises(frappe.PermissionError):
			save_record("DTMGP Traditional Institution", {"institution_name": "Tampered"}, name=institution["name"])

	def test_non_manage_role_cannot_write(self):
		existing = frappe.get_doc({
			"doctype": "DTMGP Traditional Institution", "company": self.makurdi,
			"institution_name": f"Read-only Fixture {uuid4().hex[:6]}", "institution_type": "District Headship", "status": "Active",
		}).insert(ignore_permissions=True)

		frappe.set_user(self.read_only.name)
		with self.assertRaises(frappe.PermissionError):
			save_record("DTMGP Traditional Institution", {"company": self.makurdi, "institution_name": "Blocked", "institution_type": "District Headship", "status": "Active"})
		# Read access is still granted via the broader TRADITIONAL_VIEW_ROLES set.
		names = [row.name for row in list_records("DTMGP Traditional Institution", self.makurdi)["items"]]
		self.assertIn(existing.name, names)

	def _make_user(self, role, company):
		return frappe.get_doc({
			"doctype": "User", "email": f"traditional-{uuid4().hex}@example.com", "first_name": "Traditional",
			"enabled": 1, "send_welcome_email": 0, "dtmgp_lga": company, "roles": [{"role": role}],
		}).insert()

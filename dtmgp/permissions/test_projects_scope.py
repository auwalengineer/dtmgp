from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.projects import (
	get_dashboard,
	get_maps_data,
	get_project_financials,
	get_reports,
	list_projects,
	list_records,
	list_vehicle_services,
	save_project,
	save_record,
	transition_record,
)
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup

"""API-layer scope coverage for the Projects, Assets & Field Monitoring module,
mirroring dtmgp/permissions/test_finance_scope.py: every function goes through
dtmgp.api.v1.projects (require_projects_access + get_requested_companies), not raw
frappe.get_doc, so this proves the module's endpoints -- not just the doctype hooks --
respect LGA scope."""


class TestProjectsScope(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.project_officer = self._make_user("Project Officer", self.makurdi)
		self.gboko_officer = self._make_user("Project Officer", self.gboko)
		self.chairman = self._make_user("LGA Chairman", self.makurdi)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_project_officer_creates_and_lists_only_assigned_lga_projects(self):
		frappe.set_user(self.project_officer.name)
		created = save_project({
			"company": self.makurdi, "project_name": f"Isolation Test Project {uuid4().hex[:6]}",
			"status": "Open", "expected_start_date": "2026-01-01", "expected_end_date": "2026-12-31",
		})
		self.assertEqual(created["status"], "Open")

		result = list_projects(self.makurdi, view="ongoing")
		self.assertTrue(any(row.name == created["name"] for row in result["items"]))

		frappe.set_user(self.gboko_officer.name)
		with self.assertRaises(frappe.PermissionError):
			list_projects(self.makurdi)

	def test_lga_chairman_can_approve_but_not_create_a_project(self):
		"""docs/role-permission-matrix.md gives LGA Chairman "RA" (approve an existing
		record) for Projects/assets, not "C" (create) -- only Project Officer/State
		Administrator may create; the approve-capable roles (State Administrator, LGA
		Chairman, LGA Secretary) may cancel one."""
		frappe.set_user(self.chairman.name)
		with self.assertRaises(frappe.PermissionError):
			save_project({"company": self.makurdi, "project_name": f"Chairman Attempt {uuid4().hex[:6]}", "status": "Open"})

		frappe.set_user(self.project_officer.name)
		created = save_project({"company": self.makurdi, "project_name": f"Transition Test {uuid4().hex[:6]}", "status": "Open"})

		frappe.set_user("Administrator")
		treasurer = self._make_user("Treasurer", self.makurdi)
		frappe.set_user(treasurer.name)
		with self.assertRaises(frappe.PermissionError):
			transition_record("Project", created["name"], "Cancelled")

		frappe.set_user(self.chairman.name)
		result = transition_record("Project", created["name"], "Cancelled")
		self.assertEqual(result["status"], "Cancelled")

	def test_project_officer_can_put_a_project_on_hold(self):
		frappe.set_user(self.project_officer.name)
		created = save_project({"company": self.makurdi, "project_name": f"Hold Test {uuid4().hex[:6]}", "status": "Open"})
		result = transition_record("Project", created["name"], "On hold")
		self.assertEqual(result["status"], "On hold")

	def test_inspection_and_asset_records_are_scoped_through_list_records(self):
		frappe.set_user(self.project_officer.name)
		project = save_project({"company": self.makurdi, "project_name": f"Inspection Host {uuid4().hex[:6]}", "status": "Open"})
		inspection = save_record("DTMGP Project Inspection", {
			"company": self.makurdi, "project": project["name"], "scheduled_date": "2026-02-01", "status": "Scheduled",
		})

		result = list_records("DTMGP Project Inspection", self.makurdi)
		self.assertTrue(any(row.name == inspection["name"] for row in result["items"]))

		frappe.set_user(self.gboko_officer.name)
		with self.assertRaises(frappe.PermissionError):
			list_records("DTMGP Project Inspection", self.makurdi)

	def test_dashboard_is_scoped_and_denied_for_unauthorized_roles(self):
		frappe.set_user(self.project_officer.name)
		dashboard = get_dashboard(self.makurdi)
		self.assertEqual(dashboard["lga_count"], 1)

		frappe.set_user("Administrator")
		unauthorized = self._make_user("HR Officer", self.makurdi)
		frappe.set_user(unauthorized.name)
		with self.assertRaises(frappe.PermissionError):
			get_dashboard(self.makurdi)

	def test_record_detail_apis_reject_an_out_of_scope_company(self):
		"""Record-detail/aggregate endpoints (as opposed to list_records-style item
		queries) must reject an explicitly requested out-of-scope company rather than
		silently falling back to the caller's own allowed companies -- covers the
		"record-detail APIs" isolation gap alongside the doctype-hook tests in
		test_isolation.py/test_finance_isolation.py/test_hr_isolation.py."""
		frappe.set_user(self.project_officer.name)
		with self.assertRaises(frappe.PermissionError):
			get_project_financials(self.gboko)
		with self.assertRaises(frappe.PermissionError):
			list_vehicle_services(company=self.gboko)
		with self.assertRaises(frappe.PermissionError):
			get_maps_data(self.gboko)
		with self.assertRaises(frappe.PermissionError):
			get_reports(self.gboko)

	def _make_user(self, role, company):
		return frappe.get_doc({
			"doctype": "User", "email": f"projects-scope-{uuid4().hex}@example.com", "first_name": "Projects Scope",
			"enabled": 1, "send_welcome_email": 0, "dtmgp_lga": company, "roles": [{"role": role}],
		}).insert()

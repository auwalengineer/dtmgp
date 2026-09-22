from uuid import uuid4

import frappe
from frappe.client import get as client_get
from frappe.tests.utils import FrappeTestCase

from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup

"""Cross-LGA denial coverage for the Projects, Assets & Field Monitoring module,
exercising the permission_query_conditions/has_permission hooks directly (frappe.client
.get, raw get_list, direct doc.save()) rather than through dtmgp.api.v1.projects, which
is already covered in test_projects_scope.py. Project/Task isolation is already proven
in dtmgp/permissions/test_hr_extensions.py (added for HR-005's exit-clearance
checklist, and the hook is generic -- it doesn't filter by what the Project is for) so
it isn't duplicated here. Mirrors dtmgp/permissions/test_traditional_isolation.py."""


class TestProjectsCrossLGAIsolation(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.makurdi_officer = self._make_user("Project Officer", self.makurdi)
		self.gboko_officer = self._make_user("Project Officer", self.gboko)
		self._ensure_asset_fixtures()

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_asset_read_and_list_are_denied_across_lga(self):
		asset = self._make_asset(self.makurdi)
		frappe.set_user(self.gboko_officer.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("Asset", asset.name)
		self.assertNotIn(asset.name, frappe.get_list("Asset", pluck="name"))

		frappe.set_user(self.makurdi_officer.name)
		result = client_get("Asset", asset.name)
		self.assertEqual(result["name"], asset.name)

	def test_asset_direct_write_is_denied_across_lga(self):
		asset = self._make_asset(self.makurdi)
		frappe.set_user(self.gboko_officer.name)
		doc = frappe.get_doc("Asset", asset.name)
		doc.asset_name = "Tampered"
		with self.assertRaises(frappe.PermissionError):
			doc.save()

	def test_vehicle_read_and_list_are_denied_across_lga(self):
		vehicle = self._make_vehicle(self.makurdi)
		frappe.set_user(self.gboko_officer.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("Vehicle", vehicle.name)
		self.assertNotIn(vehicle.name, frappe.get_list("Vehicle", pluck="name"))

		frappe.set_user(self.makurdi_officer.name)
		result = client_get("Vehicle", vehicle.name)
		self.assertEqual(result["name"], vehicle.name)

	def test_vehicle_log_is_scoped_through_its_vehicle(self):
		vehicle = self._make_vehicle(self.makurdi)
		employee = self._make_employee(self.makurdi)
		log = frappe.get_doc({
			"doctype": "Vehicle Log", "license_plate": vehicle.name, "employee": employee.name, "date": "2026-02-01", "odometer": 1200,
		}).insert(ignore_permissions=True)

		frappe.set_user(self.gboko_officer.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("Vehicle Log", log.name)
		self.assertNotIn(log.name, frappe.get_list("Vehicle Log", pluck="name"))

		frappe.set_user(self.makurdi_officer.name)
		result = client_get("Vehicle Log", log.name)
		self.assertEqual(result["name"], log.name)

	def test_project_inspection_and_asset_verification_are_denied_across_lga(self):
		project = frappe.get_doc({
			"doctype": "Project", "project_name": f"Isolation Host Project {uuid4().hex[:6]}", "company": self.makurdi, "status": "Open",
		}).insert(ignore_permissions=True)
		inspection = frappe.get_doc({
			"doctype": "DTMGP Project Inspection", "company": self.makurdi, "project": project.name,
			"scheduled_date": "2026-02-01", "status": "Scheduled",
		}).insert(ignore_permissions=True)
		asset = self._make_asset(self.makurdi)
		verification = frappe.get_doc({
			"doctype": "DTMGP Asset Verification", "company": self.makurdi, "asset": asset.name,
			"verification_date": "2026-02-01", "condition": "Good",
		}).insert(ignore_permissions=True)

		frappe.set_user(self.gboko_officer.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Project Inspection", inspection.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Asset Verification", verification.name)
		self.assertNotIn(inspection.name, frappe.get_list("DTMGP Project Inspection", pluck="name"))
		self.assertNotIn(verification.name, frappe.get_list("DTMGP Asset Verification", pluck="name"))

	def _make_asset(self, company):
		return frappe.get_doc({
			"doctype": "Asset", "asset_name": f"Isolation Test Asset {uuid4().hex[:6]}",
			"item_code": "Isolation Test Fixed Asset", "asset_category": "Isolation Test Category",
			"company": company, "location": "Isolation Test Location", "purchase_date": "2026-01-01",
			"gross_purchase_amount": 100000, "calculate_depreciation": 0, "is_existing_asset": 1,
		}).insert(ignore_permissions=True)

	def _make_vehicle(self, company):
		return frappe.get_doc({
			"doctype": "Vehicle", "license_plate": f"ISO-{uuid4().hex[:8].upper()}", "make": "Toyota", "model": "Hilux",
			"last_odometer": 0, "fuel_type": "Diesel", "uom": "Nos", "company": company,
		}).insert(ignore_permissions=True)

	def _make_employee(self, company):
		return frappe.get_doc({
			"doctype": "Employee", "first_name": f"Isolation Test Driver {uuid4().hex[:6]}", "company": company,
			"status": "Active", "gender": "Male", "date_of_birth": "1990-01-01", "date_of_joining": "2020-01-01",
		}).insert(ignore_permissions=True)

	def _ensure_asset_fixtures(self):
		if not frappe.db.exists("Asset Category", "Isolation Test Category"):
			category = frappe.get_doc({"doctype": "Asset Category", "asset_category_name": "Isolation Test Category"})
			for company in (self.makurdi, self.gboko):
				category.append("accounts", {
					"company_name": company,
					"fixed_asset_account": frappe.db.get_value("Account", {"company": company, "account_type": "Fixed Asset"}, "name"),
					"accumulated_depreciation_account": frappe.db.get_value("Account", {"company": company, "account_type": "Accumulated Depreciation"}, "name"),
					"depreciation_expense_account": frappe.db.get_value("Account", {"company": company, "account_type": "Depreciation"}, "name"),
				})
			category.insert(ignore_permissions=True)
		if not frappe.db.exists("Item", "Isolation Test Fixed Asset"):
			frappe.get_doc({
				"doctype": "Item", "item_code": "Isolation Test Fixed Asset", "item_name": "Isolation Test Fixed Asset",
				"item_group": "All Item Groups", "stock_uom": "Nos", "is_stock_item": 0, "is_fixed_asset": 1,
				"asset_category": "Isolation Test Category",
			}).insert(ignore_permissions=True)
		if not frappe.db.exists("Location", "Isolation Test Location"):
			frappe.get_doc({"doctype": "Location", "location_name": "Isolation Test Location"}).insert(ignore_permissions=True)

	def _make_user(self, role, company):
		return frappe.get_doc({
			"doctype": "User", "email": f"projects-iso-{uuid4().hex}@example.com", "first_name": "Projects Isolation",
			"enabled": 1, "send_welcome_email": 0, "dtmgp_lga": company, "roles": [{"role": role}],
		}).insert()

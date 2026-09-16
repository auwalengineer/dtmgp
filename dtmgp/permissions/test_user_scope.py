from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.administration import get_dashboard
from dtmgp.api.v1.overview import get_overview
from dtmgp.api.v1.users import create_user, list_users, update_user
from dtmgp.permissions.scope import get_allowed_companies
from dtmgp.permissions.user import has_permission
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup


class TestUserScope(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.makurdi_admin = self._make_user("LGA Administrator", self.makurdi)
		self.gboko_admin = self._make_user("LGA Administrator", self.gboko)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_lga_administrator_only_lists_users_in_own_lga(self):
		frappe.set_user(self.makurdi_admin.name)

		self.assertEqual(get_allowed_companies(), [self.makurdi])
		items = list_users()["items"]
		names = {item.name for item in items}
		self.assertIn(self.makurdi_admin.name, names)
		self.assertNotIn(self.gboko_admin.name, names)

	def test_lga_administrator_cannot_access_user_in_another_lga(self):
		frappe.set_user(self.makurdi_admin.name)

		self.assertTrue(has_permission(self.makurdi_admin, permission_type="write"))
		self.assertFalse(has_permission(self.gboko_admin, permission_type="write"))

	def test_frontend_creation_is_limited_to_administrators_lga(self):
		frappe.set_user(self.makurdi_admin.name)
		email = f"staff-{uuid4().hex}@example.com"
		self.assertTrue(frappe.has_permission("User", "create"))

		created = create_user(email, "Test", "HR Officer", self.makurdi)
		self.assertEqual(created["company"], self.makurdi)
		self.assertEqual(frappe.db.get_value("User", email, "dtmgp_lga"), self.makurdi)
		self.assertEqual(
			frappe.db.get_value("User Permission", {"user": email, "allow": "Company"}, "for_value"),
			self.makurdi,
		)

		with self.assertRaises(frappe.PermissionError):
			create_user(f"staff-{uuid4().hex}@example.com", "Other", "HR Officer", self.gboko)

	def test_overview_is_scoped_and_administration_requires_admin_role(self):
		staff = self._make_user("HR Officer", self.makurdi)
		frappe.set_user(staff.name)

		overview = get_overview()
		self.assertEqual(overview["scope"], self.makurdi)
		self.assertFalse(overview["is_statewide"])
		self.assertGreaterEqual(overview["user_count"], 2)
		with self.assertRaises(frappe.PermissionError):
			get_dashboard()

	def test_administration_dashboard_and_update_remain_in_lga_scope(self):
		staff = self._make_user("HR Officer", self.makurdi)
		frappe.set_user(self.makurdi_admin.name)

		dashboard = get_dashboard()
		self.assertEqual(dashboard["scope"], self.makurdi)
		self.assertGreaterEqual(dashboard["active_user_count"], 2)
		updated = update_user(staff.name, "Updated", "Treasurer", self.makurdi, "Officer")
		self.assertEqual(updated["role"], "Treasurer")
		self.assertEqual(frappe.db.get_value("User", staff.name, "dtmgp_lga"), self.makurdi)

		with self.assertRaises(frappe.PermissionError):
			update_user(self.gboko_admin.name, "Outside", "Treasurer", self.makurdi)
		with self.assertRaises(frappe.PermissionError):
			update_user(staff.name, "Outside", "Treasurer", self.gboko)

	def test_requested_overview_company_must_be_in_scope(self):
		frappe.set_user(self.makurdi_admin.name)
		with self.assertRaises(frappe.PermissionError):
			get_overview(self.gboko)

	def _make_user(self, role, company):
		email = f"scope-{uuid4().hex}@example.com"
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Scope",
				"last_name": "Test",
				"enabled": 1,
				"send_welcome_email": 0,
				"dtmgp_lga": company,
				"roles": [{"role": role}],
			}
		).insert()

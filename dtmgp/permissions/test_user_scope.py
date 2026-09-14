from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.users import create_user, list_users
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

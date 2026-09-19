import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import PLATFORM_ROLES, seed_role_profiles, seed_security_setup


class TestRoleProfileSeed(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_every_platform_role_has_a_matching_role_profile(self):
		for role_name in PLATFORM_ROLES:
			self.assertTrue(frappe.db.exists("Role Profile", role_name))
			roles = frappe.get_all("Has Role", filters={"parent": role_name, "parenttype": "Role Profile"}, pluck="role")
			self.assertEqual(roles, [role_name])

	def test_seeding_is_idempotent(self):
		before = frappe.db.count("Role Profile")
		result = seed_role_profiles()
		self.assertEqual(result["created"], [])
		self.assertEqual(frappe.db.count("Role Profile"), before)

	def test_assigning_a_role_profile_reproducibly_grants_exactly_that_role(self):
		lga = BENUE_LGAS[0].company_name
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": f"profile-{frappe.generate_hash(length=8)}@example.com",
				"first_name": "Profile",
				"enabled": 1,
				"send_welcome_email": 0,
				"dtmgp_lga": lga,
				"role_profile_name": "Treasurer",
			}
		).insert()
		try:
			self.assertEqual(set(frappe.get_roles(user.name)) & set(PLATFORM_ROLES), {"Treasurer"})

			user.reload()
			user.role_profile_name = "HR Officer"
			user.save()
			self.assertEqual(set(frappe.get_roles(user.name)) & set(PLATFORM_ROLES), {"HR Officer"})
		finally:
			frappe.delete_doc("User", user.name, force=True)

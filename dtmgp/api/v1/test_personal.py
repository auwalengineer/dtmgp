from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.personal import get_my_approvals, get_my_tasks
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup


class TestPersonalWorkspaces(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_my_tasks_are_scoped_to_the_caller(self):
		mine = self._make_user("Treasurer", self.makurdi)
		someone_else = self._make_user("Treasurer", self.makurdi)
		frappe.get_doc({"doctype": "ToDo", "allocated_to": mine.name, "description": "Review the September allocation", "status": "Open"}).insert(ignore_permissions=True)
		frappe.get_doc({"doctype": "ToDo", "allocated_to": someone_else.name, "description": "Not mine", "status": "Open"}).insert(ignore_permissions=True)

		frappe.set_user(mine.name)
		tasks = get_my_tasks()["items"]
		descriptions = {task.description for task in tasks}
		self.assertIn("Review the September allocation", descriptions)
		self.assertNotIn("Not mine", descriptions)

	def test_my_approvals_is_empty_but_not_denied_for_a_role_outside_governance(self):
		revenue_officer = self._make_user("Revenue Officer", self.makurdi)
		frappe.set_user(revenue_officer.name)
		result = get_my_approvals()
		self.assertEqual(result["items"], [])
		self.assertTrue(result["governance_scoped"])

	def test_my_approvals_surfaces_the_governance_inbox_for_a_governance_role(self):
		lga_admin = self._make_user("LGA Administrator", self.makurdi)
		frappe.set_user(lga_admin.name)
		result = get_my_approvals()
		self.assertIsInstance(result["items"], list)

	def _make_user(self, role, company):
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": f"personal-{uuid4().hex}@example.com",
				"first_name": "Personal",
				"enabled": 1,
				"send_welcome_email": 0,
				"dtmgp_lga": company,
				"roles": [{"role": role}],
			}
		).insert()

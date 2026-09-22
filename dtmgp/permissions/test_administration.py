from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.administration import (
	get_document_numbering_reference,
	get_system_health,
	list_audit_events,
	list_lga_access,
	list_login_history,
	list_platform_roles,
	list_reference_records,
	list_role_profiles,
	list_user_sessions,
	save_reference_record,
)
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup


class TestAdministrationScope(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.makurdi_admin = self._make_user("LGA Administrator", self.makurdi)
		self.gboko_admin = self._make_user("LGA Administrator", self.gboko)
		self.hr_officer = self._make_user("HR Officer", self.makurdi)
		self.state_admin = self._make_user("State Administrator", None)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_lga_administrator_sees_only_own_lga_access(self):
		frappe.set_user(self.makurdi_admin.name)
		rows = list_lga_access()
		companies = {row["company"] for row in rows}
		self.assertEqual(companies, {self.makurdi})
		users = {user["name"] for row in rows for user in row["users"]}
		self.assertIn(self.makurdi_admin.name, users)
		self.assertNotIn(self.gboko_admin.name, users)

	def test_lga_administrator_sees_only_own_lga_sessions(self):
		self._insert_session(self.makurdi_admin.name)
		self._insert_session(self.gboko_admin.name)
		try:
			frappe.set_user(self.makurdi_admin.name)
			rows = list_user_sessions()
			users = {row["user"] for row in rows}
			self.assertIn(self.makurdi_admin.name, users)
			self.assertNotIn(self.gboko_admin.name, users)
			self.assertTrue(all(row["sid"] is None or row["sid"].endswith("…") for row in rows))
		finally:
			self._delete_session(self.makurdi_admin.name)
			self._delete_session(self.gboko_admin.name)

	def test_non_admin_role_denied_user_management_reads(self):
		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			list_platform_roles()
		with self.assertRaises(frappe.PermissionError):
			list_role_profiles()
		with self.assertRaises(frappe.PermissionError):
			list_lga_access()
		with self.assertRaises(frappe.PermissionError):
			list_user_sessions()

	def test_state_only_endpoints_deny_lga_administrator(self):
		frappe.set_user(self.makurdi_admin.name)
		with self.assertRaises(frappe.PermissionError):
			get_document_numbering_reference()
		with self.assertRaises(frappe.PermissionError):
			list_audit_events()
		with self.assertRaises(frappe.PermissionError):
			list_login_history()
		with self.assertRaises(frappe.PermissionError):
			save_reference_record("Fiscal Year", {"year": "2099", "year_start_date": "2099-01-01", "year_end_date": "2099-12-31"})

	def test_state_only_endpoints_allow_state_administrator(self):
		frappe.set_user(self.state_admin.name)
		self.assertIsInstance(get_document_numbering_reference(), list)
		self.assertIn("items", list_audit_events())
		self.assertIn("items", list_login_history())

	def test_designation_write_allowed_for_lga_administrator_but_not_fiscal_year(self):
		"""Designation and Fiscal Year are both global (no `company` field), but only
		Fiscal Year drives every LGA's ledger, so its write is state-admin only even
		though Organization Setup as a whole is visible to LGA Administrator."""
		frappe.set_user(self.makurdi_admin.name)
		name = f"Test Designation {uuid4().hex[:6]}"
		result = save_reference_record("Designation", {"designation_name": name})
		self.assertEqual(result["name"], name)
		frappe.set_user("Administrator")
		frappe.delete_doc("Designation", name, force=1)

		frappe.set_user(self.makurdi_admin.name)
		with self.assertRaises(frappe.PermissionError):
			save_reference_record("Fiscal Year", {"year": "2098", "year_start_date": "2098-01-01", "year_end_date": "2098-12-31"})

	def test_system_health_denied_to_state_administrator(self):
		"""System Operations is narrower than STATE_ONLY_ROLES: System Manager only."""
		frappe.set_user(self.state_admin.name)
		with self.assertRaises(frappe.PermissionError):
			get_system_health()

	def test_document_numbering_reflects_real_autoname_not_a_fabricated_convention(self):
		frappe.set_user(self.state_admin.name)
		by_doctype = {row["doctype"]: row["autoname"] for row in get_document_numbering_reference()}
		self.assertEqual(by_doctype["DTMGP Correspondence"], "COR-{LGA_CODE}-{YYYY}-{#####}")
		# Finance doctypes predate the LGA-dated convention and genuinely lack the
		# LGA_CODE segment -- the reference must report that honestly, not claim
		# every doctype follows docs/naming-and-coding-conventions.md.
		self.assertNotIn("LGA_CODE", by_doctype["DTMGP Payment Request"])

	def test_reference_records_unsupported_doctype_rejected(self):
		frappe.set_user(self.state_admin.name)
		with self.assertRaises(frappe.PermissionError):
			list_reference_records("User")

	def _make_user(self, role, company):
		return frappe.get_doc({
			"doctype": "User", "email": f"admin-{uuid4().hex}@example.com", "first_name": "Admin",
			"enabled": 1, "send_welcome_email": 0, "dtmgp_lga": company, "roles": [{"role": role}],
		}).insert()

	def _insert_session(self, user):
		frappe.db.sql(
			"insert into `tabSessions` (`user`, `sid`, `sessiondata`, `ipaddress`, `lastupdate`, `status`) "
			"values (%s, %s, %s, %s, now(), 'Active')",
			(user, f"test-sid-{uuid4().hex}", "{}", "127.0.0.1"),
		)

	def _delete_session(self, user):
		frappe.db.sql("delete from `tabSessions` where `user` = %s and `sid` like 'test-sid-%%'", (user,))

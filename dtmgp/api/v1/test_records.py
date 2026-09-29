import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.records import _serialize_fields, get_record


class TestRecordDetails(FrappeTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_unknown_doctype_is_denied(self):
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.PermissionError):
			get_record("User", "Administrator")

	def test_guest_cannot_read_allowed_doctype(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.AuthenticationError):
			get_record("Employee", "missing")

	def test_employee_dto_excludes_restricted_personal_fields(self):
		doc = frappe._dict({
			"doctype": "Employee", "employee_name": "Test Officer", "company": "Test LGA",
			"date_of_birth": "1990-01-01", "bank_ac_no": "1234567890", "personal_email": "private@example.com",
		})
		fieldnames = {
			field["label"]
			for section in _serialize_fields(doc, frappe.get_meta("Employee"))
			for field in section["fields"]
		}
		self.assertIn("Full Name", fieldnames)
		self.assertNotIn("Date of Birth", fieldnames)
		self.assertNotIn("Bank Account No", fieldnames)
		self.assertNotIn("Personal Email", fieldnames)

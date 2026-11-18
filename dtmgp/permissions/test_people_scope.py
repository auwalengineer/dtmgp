from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.api.v1.people import (
	get_dashboard,
	get_employee_for_edit,
	get_employee_profile,
	list_employees,
	save_employee,
	set_employee_image,
	update_employee,
)
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup


class TestPeopleScope(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.hr_officer = self._make_user("HR Officer", self.makurdi)
		self.treasurer = self._make_user("Treasurer", self.makurdi)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_hr_officer_can_create_and_list_employee_in_assigned_lga(self):
		# Count deltas rather than an absolute total: this LGA may already carry
		# real, persistent Employee records (e.g. from dtmgp.setup.demo_data)
		# outside this test's own transaction.
		verified_before = get_dashboard(self.makurdi)["verified"]

		frappe.set_user(self.hr_officer.name)
		gender = frappe.get_all("Gender", pluck="name", limit=1)[0]
		created = save_employee(
			"Aondo",
			self.makurdi,
			gender,
			"1990-01-01",
			"2020-01-01",
			last_name="Test",
			grade_level="GL 08",
			verification_status="Verified",
		)

		items = list_employees(self.makurdi, search=created["name"])["items"]
		self.assertEqual(len(items), 1)
		self.assertEqual(items[0].company, self.makurdi)
		self.assertEqual(get_dashboard(self.makurdi)["verified"], verified_before + 1)

	def test_non_hr_role_cannot_access_people_api(self):
		frappe.set_user(self.treasurer.name)
		with self.assertRaises(frappe.PermissionError):
			get_dashboard(self.makurdi)

	def test_hr_officer_cannot_request_another_lga(self):
		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			list_employees(self.gboko)

	def test_hr_officer_sets_and_clears_photo_for_employee_in_own_lga(self):
		employee = self._make_employee(self.makurdi)
		file_url = self._attach_image(employee)

		frappe.set_user(self.hr_officer.name)
		set_employee_image(employee, file_url)
		self.assertEqual(get_employee_profile(employee)["image"], file_url)
		listed = list_employees(self.makurdi, search=employee)["items"]
		self.assertEqual(listed[0].image, file_url)

		set_employee_image(employee, None)
		self.assertIsNone(get_employee_profile(employee)["image"])

	def test_photo_cannot_be_set_across_lga(self):
		employee = self._make_employee(self.gboko)
		file_url = self._attach_image(employee)
		photo = frappe.get_doc("File", {"file_url": file_url})
		gboko_hr = self._make_user("HR Officer", self.gboko)
		# The private photo file is readable only by staff scoped to the employee's LGA.
		self.assertTrue(frappe.has_permission("File", "read", doc=photo, user=gboko_hr.name))
		self.assertFalse(frappe.has_permission("File", "read", doc=photo, user=self.hr_officer.name))

		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			set_employee_image(employee, file_url)

	def test_photo_must_be_an_image_attached_to_the_same_employee(self):
		employee = self._make_employee(self.makurdi)
		other = self._make_employee(self.makurdi)
		other_file = self._attach_image(other)
		not_image = self._attach_image(employee, extension="txt")

		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.ValidationError):
			set_employee_image(employee, other_file)
		with self.assertRaises(frappe.ValidationError):
			set_employee_image(employee, not_image)

	def test_hr_officer_edits_nominal_roll_fields_and_change_is_audited(self):
		employee = self._make_employee(self.makurdi)
		frappe.set_user(self.hr_officer.name)
		result = update_employee(employee, {
			"dtmgp_step": 4, "dtmgp_rank": "Senior Officer", "dtmgp_bvn": "22212345678", "cell_number": "08030000000",
			"dtmgp_date_of_first_appointment": "2015-03-01", "dtmgp_local_govt_of_payment": "Makurdi",
			"date_of_birth": "1990-01-01",  # unchanged: must not be reported as changed
		})
		self.assertNotIn("date_of_birth", result["changed"])
		self.assertIn("dtmgp_bvn", result["changed"])
		values = get_employee_for_edit(employee)["values"]
		self.assertEqual(values["dtmgp_step"], 4)
		self.assertEqual(values["dtmgp_rank"], "Senior Officer")
		# Retirement dates are re-derived from the new first-appointment date (35 years of service).
		self.assertEqual(str(get_employee_for_edit(employee)["readonly"]["dtmgp_retire_year_by_appointment"]), "2050-03-01")

		frappe.set_user("Administrator")
		event = frappe.get_last_doc("DTMGP Audit Event", filters={"reference_name": employee, "event_type": "hr_record_change"})
		self.assertIn("dtmgp_bvn", event.metadata_json)
		self.assertNotIn("22212345678", event.metadata_json)

	def test_edit_rejects_fields_outside_allowlist(self):
		employee = self._make_employee(self.makurdi)
		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.ValidationError):
			update_employee(employee, {"company": self.gboko})
		with self.assertRaises(frappe.ValidationError):
			update_employee(employee, {"bank_ac_no": "0123456789"})
		with self.assertRaises(frappe.ValidationError):
			update_employee(employee, {"first_name": "  "})
		with self.assertRaises(frappe.ValidationError):
			update_employee(employee, {"dtmgp_bvn": "123"})

	def test_edit_is_denied_across_lga_and_for_read_only_roles(self):
		employee = self._make_employee(self.gboko)
		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			get_employee_for_edit(employee)
		with self.assertRaises(frappe.PermissionError):
			update_employee(employee, {"dtmgp_rank": "X"})

		frappe.set_user("Administrator")
		own = self._make_employee(self.makurdi)
		viewer = self._make_user("Read-only Officer", self.makurdi)
		frappe.set_user(viewer.name)
		with self.assertRaises(frappe.PermissionError):
			get_employee_for_edit(own)
		with self.assertRaises(frappe.PermissionError):
			update_employee(own, {"dtmgp_rank": "X"})

	def _make_employee(self, company):
		gender = frappe.get_all("Gender", pluck="name", limit=1)[0]
		return frappe.get_doc(
			{
				"doctype": "Employee", "first_name": "Photo", "last_name": uuid4().hex[:6], "company": company,
				"gender": gender, "date_of_birth": "1990-01-01", "date_of_joining": "2020-01-01", "status": "Active",
			}
		).insert().name

	def _attach_image(self, employee, extension="png"):
		return frappe.get_doc(
			{
				"doctype": "File", "file_name": f"photo-{uuid4().hex[:8]}.{extension}", "content": uuid4().hex.encode(),
				"attached_to_doctype": "Employee", "attached_to_name": employee, "is_private": 1,
			}
		).insert().file_url

	def _make_user(self, role, company):
		email = f"people-{uuid4().hex}@example.com"
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "People",
				"last_name": "Test",
				"enabled": 1,
				"send_welcome_email": 0,
				"dtmgp_lga": company,
				"roles": [{"role": role}],
			}
		).insert()

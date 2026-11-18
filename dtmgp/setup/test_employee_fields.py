import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate

from dtmgp.hr import validate_employee_record
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import _employee_fields, seed_security_setup


class TestEmployeeNominalRollFields(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def _employee(self, **values):
		return frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": "Nominal",
				"last_name": f"Roll {frappe.generate_hash(length=6)}",
				"gender": "Male",
				"company": BENUE_LGAS[0].company_name,
				"date_of_birth": "1975-10-16",
				"date_of_joining": "1997-10-14",
				"status": "Active",
				**values,
			}
		)

	def test_template_fields_exist_and_seeding_is_idempotent(self):
		seed_security_setup()
		meta = frappe.get_meta("Employee")
		for field in _employee_fields():
			self.assertIsNotNone(meta.get_field(field["fieldname"]), field["fieldname"])
		self.assertEqual(meta.get_field("bank_name").fieldtype, "Select")
		self.assertIn("Stanbic IBTC Bank Plc", meta.get_field("bank_name").options)
		self.assertEqual(meta.get_label("employee_number"), "File No")

	def test_retirement_dates_take_the_earlier_of_age_and_service(self):
		doc = self._employee(dtmgp_date_of_first_appointment="1997-10-14")
		validate_employee_record(doc)
		self.assertEqual(getdate(doc.dtmgp_retire_year_by_age), getdate("2035-10-16"))
		self.assertEqual(getdate(doc.dtmgp_retire_year_by_appointment), getdate("2032-10-14"))
		self.assertEqual(getdate(doc.date_of_retirement), getdate("2032-10-14"))

	def test_explicit_date_of_retirement_is_kept(self):
		doc = self._employee(date_of_retirement="2036-01-01")
		validate_employee_record(doc)
		self.assertEqual(getdate(doc.date_of_retirement), getdate("2036-01-01"))

	def test_bvn_and_nin_must_be_eleven_digits(self):
		for fieldname in ("dtmgp_bvn", "dtmgp_nin"):
			for bad in ("2.22E+10", "12345", "221958198851"):
				doc = self._employee(**{fieldname: bad})
				with self.assertRaises(frappe.ValidationError):
					validate_employee_record(doc)
		doc = self._employee(dtmgp_bvn=" 22195819885 ", dtmgp_nin="25945463471")
		validate_employee_record(doc)
		self.assertEqual(doc.dtmgp_bvn, "22195819885")

	def test_present_appointment_is_not_restricted_by_first_appointment(self):
		doc = self._employee(dtmgp_date_of_first_appointment="2005-01-05", dtmgp_date_of_present_appointment="2004-01-01")
		validate_employee_record(doc)
		self.assertEqual(str(doc.dtmgp_date_of_present_appointment), "2004-01-01")

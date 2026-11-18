from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, add_months, getdate, nowdate

from dtmgp.api.v1.hr import get_hr_report, get_hr_report_options
from dtmgp.api.v1.report_exports import export_report
from dtmgp.hr_reports import REPORTS
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup

SENSITIVE = ("bvn", "nin", "bank_ac_no", "dtmgp_bvn", "dtmgp_nin", "iban")


class TestHRReports(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		self.hr_officer = self._make_user("HR Officer", self.makurdi)
		# A fresh department isolates this test's counts from other data in the LGA.
		self.department = self._make_department(self.makurdi)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_every_report_runs_in_scope_with_a_uniform_shape(self):
		self._make_employee(grade="GL 08")
		frappe.set_user(self.hr_officer.name)
		for report in REPORTS:
			result = get_hr_report(report, company=self.makurdi)
			self.assertEqual(set(result), {"columns", "rows", "totals", "summary", "note", "truncated"}, report)
			keys = {column["key"] for column in result["columns"]}
			for row in result["rows"]:
				self.assertLessEqual(set(row) & keys, keys)
				self.assertFalse(set(row) & set(SENSITIVE), report)
			# A single-LGA user never gets an LGA column.
			self.assertNotIn("LGA", [column["label"] for column in result["columns"]], report)

	def test_reports_deny_other_lgas_and_non_hr_roles(self):
		treasurer = self._make_user("Treasurer", self.makurdi)
		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			get_hr_report("nominal-roll", company=self.gboko)
		frappe.set_user(treasurer.name)
		with self.assertRaises(frappe.PermissionError):
			get_hr_report("staff-strength", company=self.makurdi)

	def test_nominal_roll_lists_only_scoped_staff_with_filters(self):
		mine = self._make_employee(grade="GL 10")
		left = self._make_employee(grade="GL 10", status="Left")
		other = self._make_employee(company=self.gboko, grade="GL 10", department=None)
		frappe.set_user(self.hr_officer.name)

		listed = self._names(get_hr_report("nominal-roll", company=self.makurdi, department=self.department))
		self.assertEqual(listed, {mine})
		everyone = self._names(get_hr_report("nominal-roll", company=self.makurdi, department=self.department, status="All"))
		self.assertEqual(everyone, {mine, left})
		self.assertNotIn(other, self._names(get_hr_report("nominal-roll", company=self.makurdi, status="All")))
		with self.assertRaises(frappe.ValidationError):
			get_hr_report("nominal-roll", company=self.makurdi, status="Retired")

	def test_staff_strength_counts_by_gender_cadre_and_status(self):
		self._make_employee(gender="Female", grade="GL 04")
		self._make_employee(gender="Male", grade="GL 08")
		self._make_employee(gender="Female", grade="GL 14")
		self._make_employee(gender="Male", grade="GL 08", status="Suspended")
		frappe.set_user(self.hr_officer.name)

		result = get_hr_report("staff-strength", company=self.makurdi, department=self.department, group_by="grade_band")
		totals = result["totals"]
		self.assertEqual(
			{key: totals[key] for key in ("active", "male", "female", "junior", "senior", "management", "suspended_inactive", "on_roll")},
			{"active": 3, "male": 1, "female": 2, "junior": 1, "senior": 1, "management": 1, "suspended_inactive": 1, "on_roll": 4},
		)
		self.assertEqual(sum(row["active"] for row in result["rows"]), 3)
		with self.assertRaises(frappe.ValidationError):
			get_hr_report("staff-strength", company=self.makurdi, group_by="favourite_colour")

	def test_distribution_by_grade_level_and_age_band(self):
		self._make_employee(grade="GL 07")
		self._make_employee(grade="GL 07")
		self._make_employee(grade="GL 12", date_of_birth=add_months(nowdate(), -12 * 58))
		frappe.set_user(self.hr_officer.name)

		grades = get_hr_report("staff-distribution", company=self.makurdi, department=self.department, dimension="grade_level")
		self.assertEqual({row["group"]: row["staff"] for row in grades["rows"]}, {"GL 07": 2, "GL 12": 1})
		ages = get_hr_report("staff-distribution", company=self.makurdi, department=self.department, dimension="age_band")
		self.assertEqual(next(row["staff"] for row in ages["rows"] if row["group"] == "55 - 59"), 1)
		self.assertEqual(ages["totals"]["staff"], 3)

	def test_retirement_forecast_lists_overdue_and_upcoming_with_basis(self):
		overdue = self._make_employee(date_of_retirement=add_days(nowdate(), -30))
		soon = self._make_employee(date_of_retirement=add_months(nowdate(), 6))
		later = self._make_employee(date_of_retirement=add_months(nowdate(), 30))
		frappe.set_user(self.hr_officer.name)

		result = get_hr_report("retirement-forecast", company=self.makurdi, department=self.department, months=12)
		timing = {row["name"]: row["timing"] for row in result["rows"]}
		self.assertEqual(timing, {overdue: "Overdue", soon: "Within 12 months"})
		self.assertNotIn(later, timing)
		self.assertIn(later, self._names(get_hr_report("retirement-forecast", company=self.makurdi, department=self.department, months=36)))
		self.assertEqual(result["summary"][0]["value"], 1)
		with self.assertRaises(frappe.ValidationError):
			get_hr_report("retirement-forecast", company=self.makurdi, months=7)

	def test_appointments_and_exits_in_period(self):
		this_year = f"{getdate(nowdate()).year}-01-15"
		appointed = self._make_employee(date_of_joining=this_year)
		exited = self._make_employee(date_of_joining="2010-01-01", status="Left", relieving_date=this_year)
		frappe.set_user(self.hr_officer.name)

		result = get_hr_report("appointments-exits", company=self.makurdi, department=self.department)
		movements = {row["name"]: row["movement"] for row in result["rows"]}
		self.assertEqual(movements.get(appointed), "Appointed")
		self.assertEqual(movements.get(exited), "Exited")
		with self.assertRaises(frappe.ValidationError):
			get_hr_report("appointments-exits", company=self.makurdi, from_date="2026-12-31", to_date="2026-01-01")

	def test_verification_and_completeness_rates(self):
		self._make_employee(verification="Verified", bvn="22212345678")
		self._make_employee(verification="Pending")
		frappe.set_user(self.hr_officer.name)

		verification = get_hr_report("verification", company=self.makurdi, department=self.department)
		self.assertEqual((verification["totals"]["verified"], verification["totals"]["verified_pct"]), (1, 50.0))
		completeness = get_hr_report("records-completeness", company=self.makurdi, department=self.department)
		self.assertEqual(completeness["totals"]["bvn_pct"], 50.0)
		self.assertNotIn("22212345678", frappe.as_json(completeness))

	def test_statewide_user_gets_lga_grouping_and_column(self):
		state_admin = self._make_user("State Administrator", None)
		frappe.set_user(state_admin.name)
		options = get_hr_report_options()
		self.assertTrue(options["is_statewide"])
		self.assertIn("lga", [option["value"] for option in options["group_by"]])
		strength = get_hr_report("staff-strength")
		self.assertEqual(strength["columns"][0]["label"], "LGA")
		self.assertEqual(len(strength["rows"]), len(BENUE_LGAS))
		self.assertIn("LGA", [column["label"] for column in get_hr_report("nominal-roll")["columns"]])

		frappe.set_user(self.hr_officer.name)
		self.assertNotIn("lga", [option["value"] for option in get_hr_report_options(self.makurdi)["group_by"]])

	def test_csv_export_is_rebuilt_on_the_server(self):
		self._make_employee(gender="Female", grade="GL 09")
		frappe.set_user(self.hr_officer.name)
		result = export_report(
			"hr.report.staff-strength", "Staff Strength Report", "Monthly management review",
			columns=["Forged"], rows=[["forged"]], company=self.makurdi,
			filters={"department": self.department, "group_by": "department"},
		)
		lines = result["content"].strip().splitlines()
		self.assertTrue(lines[0].startswith("Department,Active,% of active"))
		self.assertNotIn("forged", result["content"])
		self.assertTrue(lines[-1].startswith("Total,1,"))
		with self.assertRaises(frappe.PermissionError):
			export_report("hr.report.nominal-roll", "Nominal Roll", "Monthly management review", company=self.gboko, filters={})

	# ------------------------------------------------------------------ helpers

	def _names(self, result):
		return {row["name"] for row in result["rows"]}

	def _make_employee(
		self, company=None, department="default", gender="Male", grade=None, status="Active", date_of_birth="1985-01-01",
		date_of_joining="2015-01-01", date_of_retirement=None, relieving_date=None, verification=None, bvn=None,
	):
		company = company or self.makurdi
		doc = frappe.get_doc({
			"doctype": "Employee", "first_name": f"Report{uuid4().hex[:6]}", "company": company, "gender": gender,
			"date_of_birth": date_of_birth, "date_of_joining": date_of_joining, "status": status,
			"department": self.department if department == "default" and company == self.makurdi else None,
			"dtmgp_grade_level": grade, "date_of_retirement": date_of_retirement, "dtmgp_bvn": bvn,
			"relieving_date": relieving_date or ("2020-06-30" if status == "Left" else None),
		}).insert()
		if verification:
			frappe.db.set_value("Employee", doc.name, "dtmgp_verification_status", verification)
		return doc.name

	def _make_department(self, company):
		return frappe.get_doc({
			"doctype": "Department", "department_name": f"Reports {uuid4().hex[:6]}", "company": company,
			"parent_department": "All Departments",
		}).insert().name

	def _make_user(self, role, company):
		user = frappe.get_doc({
			"doctype": "User", "email": f"reports-{uuid4().hex}@example.com", "first_name": "Reports",
			"send_welcome_email": 0, "roles": [{"role": role}],
		}).insert()
		if company:
			frappe.get_doc({"doctype": "User Permission", "user": user.name, "allow": "Company", "for_value": company, "apply_to_all_doctypes": 1}).insert()
		return user

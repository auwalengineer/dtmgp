from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from dtmgp.api.v1.hr import (
	complete_separation_activity,
	decide_leave_application,
	get_attendance_summary,
	get_employee_separation,
	get_establishment_report,
	get_hr_reports,
	get_payroll_overview,
	get_retirement_forecast,
	get_staff_audit_exceptions,
	list_employee_promotions,
	list_employee_transfers,
	list_lga_companies,
	list_restricted_hr_records,
	list_staffing_plans,
	list_verification_records,
	review_verification_record,
	save_employee_promotion,
	save_employee_separation,
	save_employee_transfer,
	save_restricted_hr_record,
	save_staffing_plan,
	save_verification_exercise,
	save_verification_record,
	submit_employee_promotion,
	submit_employee_separation,
	submit_employee_transfer,
	submit_staffing_plan,
	transition_verification_exercise,
)
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import EMPLOYEE_GRADE_FIELD, EMPLOYEE_VERIFICATION_FIELD, seed_security_setup


class TestHRExtensions(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		seed_security_setup()
		self.makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		self.gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		# Kept minimal: User creation is rate-limited (throttle_user_creation), so tests
		# create extra role-specific users lazily, only where a given test needs them.
		self.hr_officer = self._make_user("HR Officer", self.makurdi)
		self.employee = self._make_employee(self.makurdi)

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	# ---------------------------------------------------------------- Establishment (Staffing Plan)

	def test_restricted_personnel_records_are_lga_scoped(self):
		frappe.set_user(self.hr_officer.name)
		created = save_restricted_hr_record("personnel_file", {
			"company": self.makurdi, "employee": self.employee, "file_status": "Active",
			"classification": "Restricted", "retention_category": "Personnel record",
		})
		self.assertEqual(list_restricted_hr_records("personnel_file", self.makurdi, self.employee)[0].name, created["name"])
		with self.assertRaises(frappe.PermissionError):
			list_restricted_hr_records("personnel_file", self.gboko)

	def test_next_of_kin_employee_must_belong_to_selected_lga(self):
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.ValidationError):
			save_restricted_hr_record("next_of_kin", {
				"company": self.gboko, "employee": self.employee, "full_name": "Test Contact",
				"relationship": "Sibling", "phone": "08000000000",
			})

	def test_staffing_plan_reports_computed_headcount_and_vacancies(self):
		# A dedicated, never-reused designation keeps this assertion exact regardless of
		# how many other employees (from other tests or concurrent site activity) happen
		# to share the shared "default" designation _make_employee otherwise picks.
		frappe.set_user("Administrator")
		designation = frappe.get_doc({"doctype": "Designation", "designation_name": f"Test Designation {uuid4().hex[:6]}"}).insert(ignore_permissions=True).name
		frappe.db.set_value("Employee", self.employee, "designation", designation)
		frappe.set_user(self.hr_officer.name)
		department = frappe.get_all("Department", filters={"company": self.makurdi}, pluck="name", limit=1)[0]

		created = save_staffing_plan({
			"company": self.makurdi, "department": department, "from_date": today(), "to_date": add_days(today(), 365),
			"staffing_details": [{"designation": designation, "vacancies": 2}],
		})
		submit_staffing_plan(created["name"])

		report = get_establishment_report(self.makurdi)
		position = next(p for p in report["positions"] if p["designation"] == designation)
		self.assertEqual(position["current_count"], 1)
		self.assertEqual(position["number_of_positions"], 3)
		self.assertEqual(position["position_status"], "Partially Filled")

	def test_staffing_plan_is_denied_across_lga(self):
		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			list_staffing_plans(self.gboko)

	# ---------------------------------------------------------------- Posting & transfer (Employee Transfer)

	def test_transfer_requires_a_different_submitter_and_moves_the_employee(self):
		gboko_hr_officer = self._make_user("HR Officer", self.gboko)
		frappe.set_user(self.hr_officer.name)
		created = save_employee_transfer({"employee": self.employee, "transfer_date": today(), "new_company": self.gboko})

		with self.assertRaises(frappe.PermissionError):
			submit_employee_transfer(created["name"])

		# Submission (assumption of duty) is recorded by the receiving LGA, which is
		# also the only side with write access to move the Employee's own company.
		frappe.set_user(gboko_hr_officer.name)
		result = submit_employee_transfer(created["name"])

		self.assertEqual(result["docstatus"], 1)
		self.assertEqual(frappe.db.get_value("Employee", self.employee, "company"), self.gboko)

	def test_posting_updates_the_employee_department_on_submission(self):
		lga_admin = self._make_user("LGA Administrator", self.makurdi)
		new_department = frappe.get_doc({"doctype": "Department", "department_name": f"Ops-{uuid4().hex[:5]}", "company": self.makurdi}).insert(ignore_permissions=True).name
		frappe.set_user(self.hr_officer.name)
		created = save_employee_transfer({"employee": self.employee, "transfer_date": today(), "to_department": new_department})

		frappe.set_user(lga_admin.name)
		submit_employee_transfer(created["name"])
		self.assertEqual(frappe.db.get_value("Employee", self.employee, "department"), new_department)

	def test_transfer_is_visible_to_both_source_and_destination_lga_but_not_a_third(self):
		gboko_hr_officer = self._make_user("HR Officer", self.gboko)
		frappe.set_user(self.hr_officer.name)
		created = save_employee_transfer({"employee": self.employee, "transfer_date": today(), "new_company": self.gboko})

		frappe.set_user(gboko_hr_officer.name)
		names = {item.name for item in list_employee_transfers(self.gboko)["items"]}
		self.assertIn(created["name"], names)

		frappe.set_user("Administrator")
		otukpo = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Otukpo")
		otukpo_officer = self._make_user("HR Officer", otukpo)
		frappe.set_user(otukpo_officer.name)
		with self.assertRaises(frappe.PermissionError):
			list_employee_transfers(self.makurdi)

	# ---------------------------------------------------------------- Promotions (Employee Promotion)

	def test_promotion_submission_updates_employee_grade_and_blocks_self_approval(self):
		lga_admin = self._make_user("LGA Administrator", self.makurdi)
		frappe.set_user(self.hr_officer.name)
		created = save_employee_promotion({"employee": self.employee, "promotion_date": today(), "proposed_grade_level": "GL 10"})

		with self.assertRaises(frappe.PermissionError):
			submit_employee_promotion(created["name"])

		frappe.set_user(lga_admin.name)
		result = submit_employee_promotion(created["name"])
		self.assertEqual(result["docstatus"], 1)
		self.assertEqual(frappe.db.get_value("Employee", self.employee, EMPLOYEE_GRADE_FIELD), "GL 10")

	def test_promotion_is_denied_across_lga(self):
		gboko_hr_officer = self._make_user("HR Officer", self.gboko)
		frappe.set_user(gboko_hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			list_employee_promotions(self.makurdi)

	# ---------------------------------------------------------------- Verification & biometrics

	def test_verification_review_requires_a_different_reviewer_and_updates_employee_status(self):
		lga_admin = self._make_user("LGA Administrator", self.makurdi)
		frappe.set_user(self.hr_officer.name)
		exercise = save_verification_exercise({"company": self.makurdi, "title": "2026 Cycle", "cycle_start_date": today(), "cycle_end_date": add_days(today(), 30)})
		transition_verification_exercise(exercise["name"], "In Progress")
		record = save_verification_record({"company": self.makurdi, "exercise": exercise["name"], "employee": self.employee})

		with self.assertRaises(frappe.ValidationError):
			review_verification_record(record["name"], "Verified")

		frappe.set_user(lga_admin.name)
		result = review_verification_record(record["name"], "Verified")
		self.assertEqual(result["review_status"], "Verified")
		self.assertEqual(frappe.db.get_value("Employee", self.employee, EMPLOYEE_VERIFICATION_FIELD), "Verified")

	def test_verification_exception_requires_a_reason(self):
		lga_admin = self._make_user("LGA Administrator", self.makurdi)
		frappe.set_user(self.hr_officer.name)
		exercise = save_verification_exercise({"company": self.makurdi, "title": "2026 Cycle", "cycle_start_date": today(), "cycle_end_date": add_days(today(), 30)})
		record = save_verification_record({"company": self.makurdi, "exercise": exercise["name"], "employee": self.employee})

		frappe.set_user(lga_admin.name)
		with self.assertRaises(frappe.ValidationError):
			review_verification_record(record["name"], "Exception")

	def test_verification_records_are_denied_across_lga(self):
		gboko_hr_officer = self._make_user("HR Officer", self.gboko)
		frappe.set_user(gboko_hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			list_verification_records(self.makurdi)

	# ---------------------------------------------------------------- Retirement & exit (Employee Separation)

	def test_exit_clearance_completes_all_activities_and_marks_employee_left(self):
		frappe.set_user(self.hr_officer.name)
		created = save_employee_separation({"employee": self.employee, "resignation_letter_date": today()})
		submit_employee_separation(created["name"])

		detail = get_employee_separation(created["name"])
		self.assertTrue(detail["activities"])
		for activity in detail["activities"][:-1]:
			complete_separation_activity(created["name"], activity["activity_name"])
			self.assertEqual(frappe.db.get_value("Employee", self.employee, "status"), "Active")

		complete_separation_activity(created["name"], detail["activities"][-1]["activity_name"])
		final = get_employee_separation(created["name"])
		self.assertEqual(final["boarding_status"], "Completed")
		self.assertEqual(frappe.db.get_value("Employee", self.employee, "status"), "Left")

	def test_exit_clearance_is_denied_across_lga(self):
		frappe.set_user(self.hr_officer.name)
		created = save_employee_separation({"employee": self.employee, "resignation_letter_date": today()})

		frappe.set_user("Administrator")
		gboko_hr_officer = self._make_user("HR Officer", self.gboko)
		frappe.set_user(gboko_hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			get_employee_separation(created["name"])

	def test_retirement_forecast_only_returns_employees_within_the_window(self):
		frappe.set_user("Administrator")
		retiring_soon = self._make_employee(self.makurdi, date_of_retirement=add_days(today(), 10))
		frappe.set_user(self.hr_officer.name)
		names = {item.name for item in get_retirement_forecast(self.makurdi, 1)}
		self.assertIn(retiring_soon, names)
		self.assertNotIn(self.employee, names)

	# ---------------------------------------------------------------- Attendance & leave

	def test_attendance_summary_is_scoped_to_the_requested_lga(self):
		frappe.set_user("Administrator")
		# Count deltas rather than an absolute total: this LGA may already carry
		# real, persistent attendance records (e.g. from dtmgp.setup.demo_data)
		# outside this test's own transaction.
		before = get_attendance_summary(self.makurdi)["present"]
		frappe.get_doc({"doctype": "Attendance", "employee": self.employee, "company": self.makurdi, "attendance_date": today(), "status": "Present"}).insert(ignore_permissions=True).submit()

		frappe.set_user(self.hr_officer.name)
		summary = get_attendance_summary(self.makurdi)
		self.assertEqual(summary["present"], before + 1)

	def test_shift_assignments_are_scoped_to_the_requested_lga(self):
		# Shift Assignment has no dedicated dtmgp API wrapper yet (the frontend surfaces
		# it via the desk-style Custom DocPerm + permission_query_conditions hooks
		# only), so this exercises dtmgp.permissions.hr.shift_assignment_query/
		# has_permission directly, the same way test_isolation.py covers other
		# hook-only doctypes.
		frappe.set_user("Administrator")
		shift_type = frappe.db.get_value("Shift Type", {}, "name") or frappe.get_doc(
			{"doctype": "Shift Type", "name": "Test Shift", "start_time": "09:00:00", "end_time": "17:00:00"}
		).insert(ignore_permissions=True).name
		makurdi_assignment = frappe.get_doc({
			"doctype": "Shift Assignment", "employee": self.employee, "company": self.makurdi,
			"shift_type": shift_type, "start_date": today(),
		}).insert(ignore_permissions=True)

		gboko_hr_officer = self._make_user("HR Officer", self.gboko)
		frappe.set_user(gboko_hr_officer.name)
		names = frappe.get_list("Shift Assignment", pluck="name")
		self.assertNotIn(makurdi_assignment.name, names)
		self.assertFalse(frappe.has_permission("Shift Assignment", "read", doc=makurdi_assignment.name, user=gboko_hr_officer.name))

		frappe.set_user(self.hr_officer.name)
		names = frappe.get_list("Shift Assignment", pluck="name")
		self.assertIn(makurdi_assignment.name, names)
		self.assertTrue(frappe.has_permission("Shift Assignment", "read", doc=makurdi_assignment.name, user=self.hr_officer.name))

	def test_employee_cannot_decide_their_own_leave_application(self):
		frappe.set_user("Administrator")
		user = frappe.get_doc({
			"doctype": "User", "email": f"leave-{uuid4().hex}@example.com", "first_name": "Leave",
			"enabled": 1, "send_welcome_email": 0, "dtmgp_lga": self.makurdi, "roles": [{"role": "HR Officer"}],
		}).insert()
		employee = self._make_employee(self.makurdi, user_id=user.name)
		leave_type = frappe.get_all("Leave Type", pluck="name", limit=1)[0]
		application = frappe.get_doc({
			"doctype": "Leave Application", "employee": employee, "company": self.makurdi, "leave_type": leave_type,
			"from_date": today(), "to_date": today(), "status": "Open",
		}).insert(ignore_permissions=True)

		frappe.set_user(user.name)
		with self.assertRaises(frappe.PermissionError):
			decide_leave_application(application.name, "Approved")

	# ---------------------------------------------------------------- Payroll, audit & reports

	def test_payroll_overview_is_denied_to_non_payroll_roles(self):
		treasurer = self._make_user("Treasurer", self.makurdi)
		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			get_payroll_overview(self.makurdi)

		frappe.set_user(treasurer.name)
		overview = get_payroll_overview(self.makurdi)
		self.assertIn("paid", overview)

	def test_staff_audit_exceptions_are_denied_to_non_audit_roles(self):
		internal_auditor = self._make_user("Internal Auditor", self.makurdi)
		frappe.set_user(self.hr_officer.name)
		with self.assertRaises(frappe.PermissionError):
			get_staff_audit_exceptions(self.makurdi)

		frappe.set_user(internal_auditor.name)
		result = get_staff_audit_exceptions(self.makurdi)
		self.assertIn(self.employee, [item.name for item in result["unverified"]])

	def test_lga_companies_list_is_the_full_23_lga_registry(self):
		frappe.set_user(self.hr_officer.name)
		names = list_lga_companies()
		self.assertEqual(len(names), 23)
		self.assertIn(self.gboko, names)

	def test_hr_reports_are_scoped_to_the_requested_lga(self):
		frappe.set_user(self.hr_officer.name)
		report = get_hr_reports(self.makurdi)
		self.assertGreaterEqual(sum(row["count"] for row in report["distribution_by_gender"]), 1)

	def _make_employee(self, company, user_id=None, date_of_retirement=None):
		gender = frappe.get_all("Gender", pluck="name", limit=1)[0]
		designation = frappe.get_all("Designation", pluck="name", limit=1)
		if not designation:
			designation = [frappe.get_doc({"doctype": "Designation", "designation_name": "Test Officer"}).insert(ignore_permissions=True).name]
		doc = frappe.get_doc({
			"doctype": "Employee", "first_name": f"Test-{uuid4().hex[:6]}", "company": company, "gender": gender,
			"date_of_birth": "1990-01-01", "date_of_joining": "2020-01-01", "status": "Active", "designation": designation[0],
			"date_of_retirement": date_of_retirement, "user_id": user_id,
		}).insert(ignore_permissions=True)
		return doc.name

	def _make_user(self, role, company):
		return frappe.get_doc({
			"doctype": "User", "email": f"hrext-{uuid4().hex}@example.com", "first_name": "HRExt",
			"enabled": 1, "send_welcome_email": 0, "dtmgp_lga": company, "roles": [{"role": role}],
		}).insert()

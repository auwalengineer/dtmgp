"""Local/dev demo data for the HR & Staff module. Not part of install/migrate —
run manually with `bench --site <site> execute dtmgp.setup.demo_data.seed_hr_demo_data`.
Safe to re-run: every record lookup is idempotent."""

import frappe
from frappe.utils import add_days, today

from dtmgp.api.v1.hr import (
	complete_separation_activity,
	review_verification_record,
	save_employee_promotion,
	save_employee_separation,
	save_employee_transfer,
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
from dtmgp.setup.security import EMPLOYEE_VERIFICATION_FIELD, seed_security_setup


def reset_hr_demo_data():
	"""Cancel and delete any partially-created demo records so seed_hr_demo_data
	starts clean. Safe to run even if nothing exists yet."""
	frappe.set_user("Administrator")
	for doctype in (
		"Attendance", "Leave Application", "Leave Allocation",
		"DTMGP Staff Verification Record", "DTMGP Staff Verification Exercise",
		"Employee Separation", "Employee Promotion", "Employee Transfer", "Staffing Plan",
	):
		for name in frappe.get_all(doctype, pluck="name"):
			doc = frappe.get_doc(doctype, name)
			if doc.docstatus == 1:
				doc.cancel()
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
	for name in frappe.get_all("Employee", filters={"company": ["like", "%Local Government Area"]}, pluck="name"):
		frappe.delete_doc("Employee", name, force=True, ignore_permissions=True)
	frappe.db.commit()


def seed_hr_demo_data():
	frappe.set_user("Administrator")
	seed_security_setup()

	makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
	gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")

	def make_user(email, first_name, role, company):
		if frappe.db.exists("User", email):
			return email
		return frappe.get_doc({
			"doctype": "User", "email": email, "first_name": first_name, "enabled": 1,
			"send_welcome_email": 0, "new_password": "Demo@12345", "dtmgp_lga": company,
			"roles": [{"role": role}],
		}).insert().name

	hr_officer = make_user("hr.officer@makurdi.gov.ng", "Grace", "HR Officer", makurdi)
	lga_admin = make_user("admin@makurdi.gov.ng", "Daniel", "LGA Administrator", makurdi)
	treasurer = make_user("treasurer@makurdi.gov.ng", "Comfort", "Treasurer", makurdi)
	auditor = make_user("auditor@makurdi.gov.ng", "Samuel", "Internal Auditor", makurdi)
	gboko_hr_officer = make_user("hr.officer@gboko.gov.ng", "Rose", "HR Officer", gboko)

	def make_employee(first_name, last_name, gender, dob, doj, department, designation, grade, date_of_retirement=None, verification="Pending"):
		existing = frappe.db.exists("Employee", {"first_name": first_name, "last_name": last_name, "company": makurdi})
		if existing:
			return existing
		return frappe.get_doc({
			"doctype": "Employee", "first_name": first_name, "last_name": last_name, "company": makurdi,
			"gender": gender, "date_of_birth": dob, "date_of_joining": doj, "status": "Active",
			"department": department, "designation": designation, "dtmgp_grade_level": grade,
			EMPLOYEE_VERIFICATION_FIELD: verification, "date_of_retirement": date_of_retirement,
		}).insert(ignore_permissions=True).name

	ada = make_employee("Ada", "Terna", "Female", "1990-01-01", "2019-01-15", "Accounts - MLGA", "Accountant", "GL 08")
	iorlumun = make_employee("Iorlumun", "Aondo", "Male", "1988-05-12", "2017-03-01", "Human Resources - MLGA", "Administrative Officer", "GL 10", verification="Verified")
	mimi = make_employee("Mimi", "Kwaghga", "Female", "1965-02-20", "2005-01-01", "Human Resources - MLGA", "Administrative Assistant", "GL 06", date_of_retirement=add_days(today(), 60))
	terzungwe = make_employee("Terzungwe", "Iyorja", "Male", "1992-07-30", "2021-09-01", "Legal - MLGA", "Business Analyst", "GL 09")
	doosuur = make_employee("Doosuur", "Age", "Female", "1980-11-11", "2015-06-01", "Management - MLGA", "Consultant", "GL 12")
	kwaghhemba = make_employee("Kwaghhemba", "Orya", "Male", "1993-03-03", "2022-01-10", "Sales - MLGA", "Associate", "GL 07")
	bem = make_employee("Bem", "Utoo", "Male", "1975-08-08", "2010-04-01", "Purchase - MLGA", "Analyst", "GL 08")

	created = {"employees": [ada, iorlumun, mimi, terzungwe, doosuur, kwaghhemba, bem]}
	frappe.db.commit()

	# ---- Establishment (Staffing Plan) ----
	if not frappe.db.exists("Staffing Plan", {"company": makurdi, "department": "Human Resources - MLGA"}):
		frappe.set_user(hr_officer)
		plan = save_staffing_plan({
			"company": makurdi, "department": "Human Resources - MLGA", "from_date": today(), "to_date": add_days(today(), 365),
			"staffing_details": [
				{"designation": "Administrative Officer", "vacancies": 2},
				{"designation": "Administrative Assistant", "vacancies": 1},
			],
		})
		submit_staffing_plan(plan["name"])
		created["staffing_plan"] = plan["name"]
	frappe.db.commit()

	# ---- Postings & Transfers ----
	if not frappe.db.exists("Employee Transfer", {"employee": terzungwe, "docstatus": 0}):
		frappe.set_user(hr_officer)
		posting = save_employee_transfer({"employee": terzungwe, "transfer_date": today(), "to_department": "Management - MLGA"})
		created["draft_posting"] = posting["name"]

	if not frappe.db.exists("Employee Transfer", {"employee": kwaghhemba}):
		frappe.set_user(hr_officer)
		transfer = save_employee_transfer({"employee": kwaghhemba, "transfer_date": today(), "new_company": gboko})
		frappe.set_user(gboko_hr_officer)
		submit_employee_transfer(transfer["name"])
		created["submitted_transfer"] = transfer["name"]
	frappe.db.commit()

	# ---- Promotions ----
	if not frappe.db.exists("Employee Promotion", {"employee": terzungwe}):
		frappe.set_user(hr_officer)
		promotion = save_employee_promotion({"employee": terzungwe, "promotion_date": today(), "proposed_grade_level": "GL 11"})
		frappe.set_user(lga_admin)
		submit_employee_promotion(promotion["name"])
		created["promotion"] = promotion["name"]
	frappe.db.commit()

	# ---- Verification ----
	if not frappe.db.exists("DTMGP Staff Verification Exercise", {"company": makurdi}):
		frappe.set_user(hr_officer)
		exercise = save_verification_exercise({"company": makurdi, "title": "2026 Annual Staff Verification", "cycle_start_date": today(), "cycle_end_date": add_days(today(), 30)})
		transition_verification_exercise(exercise["name"], "In Progress")

		record_verified = save_verification_record({"company": makurdi, "exercise": exercise["name"], "employee": ada, "biometric_captured": 1})
		record_exception = save_verification_record({"company": makurdi, "exercise": exercise["name"], "employee": iorlumun, "biometric_captured": 0})
		record_pending = save_verification_record({"company": makurdi, "exercise": exercise["name"], "employee": terzungwe, "biometric_captured": 0})

		frappe.set_user(lga_admin)
		review_verification_record(record_verified["name"], "Verified")
		review_verification_record(record_exception["name"], "Exception", exception_reason="Certificate awaiting confirmation from issuing institution.")
		created["verification_exercise"] = exercise["name"]
		created["verification_records"] = [record_verified["name"], record_exception["name"], record_pending["name"]]
	frappe.db.commit()

	# ---- Retirement & exit ----
	if not frappe.db.exists("Employee Separation", {"employee": doosuur}):
		frappe.set_user(hr_officer)
		separation_partial = save_employee_separation({"employee": doosuur, "resignation_letter_date": today(), "exit_interview": "Retiring to pursue private consultancy."})
		submit_employee_separation(separation_partial["name"])
		for activity_name in ("HR clearance", "Finance clearance", "Records and IT clearance"):
			complete_separation_activity(separation_partial["name"], activity_name)
		created["separation_partial"] = separation_partial["name"]
		frappe.db.commit()

	if not frappe.db.exists("Employee Separation", {"employee": bem}):
		frappe.set_user(hr_officer)
		separation_done = save_employee_separation({"employee": bem, "resignation_letter_date": today(), "exit_interview": "Voluntary resignation."})
		submit_employee_separation(separation_done["name"])
		for activity_name in ("HR clearance", "Finance clearance", "Records and IT clearance", "Head of Department clearance"):
			complete_separation_activity(separation_done["name"], activity_name)
		created["separation_done"] = separation_done["name"]
	frappe.db.commit()

	# ---- Attendance (today) ----
	frappe.set_user("Administrator")
	for emp, status, late in ((ada, "Present", 0), (iorlumun, "Present", 1), (terzungwe, "Present", 0), (mimi, "Absent", 0)):
		if not frappe.db.exists("Attendance", {"employee": emp, "attendance_date": today()}):
			frappe.get_doc({
				"doctype": "Attendance", "employee": emp, "company": makurdi, "attendance_date": today(),
				"status": status, "late_entry": late,
			}).insert(ignore_permissions=True).submit()

	# ---- Leave ----
	if not frappe.db.exists("Leave Allocation", {"employee": ada, "leave_type": "Privilege Leave"}):
		frappe.get_doc({
			"doctype": "Leave Allocation", "employee": ada, "leave_type": "Privilege Leave", "company": makurdi,
			"from_date": today(), "to_date": add_days(today(), 300), "new_leaves_allocated": 14, "total_leaves_allocated": 14, "carry_forward": 0,
		}).insert(ignore_permissions=True).submit()
	if not frappe.db.exists("Leave Allocation", {"employee": iorlumun, "leave_type": "Casual Leave"}):
		frappe.get_doc({
			"doctype": "Leave Allocation", "employee": iorlumun, "leave_type": "Casual Leave", "company": makurdi,
			"from_date": today(), "to_date": add_days(today(), 300), "new_leaves_allocated": 7, "total_leaves_allocated": 7, "carry_forward": 0,
		}).insert(ignore_permissions=True).submit()
	if not frappe.db.exists("Leave Application", {"employee": iorlumun, "leave_type": "Casual Leave", "status": "Open"}):
		frappe.get_doc({
			"doctype": "Leave Application", "employee": iorlumun, "company": makurdi, "leave_type": "Casual Leave",
			"from_date": add_days(today(), 3), "to_date": add_days(today(), 4), "status": "Open",
		}).insert(ignore_permissions=True)

	frappe.db.commit()
	created["users"] = [hr_officer, lga_admin, treasurer, auditor, gboko_hr_officer]
	return created

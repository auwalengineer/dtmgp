import frappe
from frappe.model.document import Document
from frappe.utils import add_years, getdate, now_datetime

from dtmgp.finance import require_roles, validate_lga
from dtmgp.permissions.scope import HR_MANAGE_ROLES
from dtmgp.setup.security import (
	EMPLOYEE_BVN_FIELD,
	EMPLOYEE_FIRST_APPOINTMENT_FIELD,
	EMPLOYEE_NIN_FIELD,
	EMPLOYEE_RETIRE_BY_AGE_FIELD,
	EMPLOYEE_RETIRE_BY_SERVICE_FIELD,
	RETIREMENT_AGE_YEARS,
	RETIREMENT_SERVICE_YEARS,
)

RESTRICTED_HR_ROLES = {"System Manager", "State Administrator", "LGA Administrator", "HR Officer"}


def validate_employee_record(doc, method=None):
	"""Employee doc_event (validate). Guards the identity numbers and derives the
	retirement dates so imported nominal-roll rows can't carry stale/hand-typed values."""
	for fieldname, label in ((EMPLOYEE_BVN_FIELD, "BVN"), (EMPLOYEE_NIN_FIELD, "NIN")):
		value = (doc.get(fieldname) or "").strip()
		# Both are 11-digit numbers; this also catches spreadsheet mangling such as "2.22E+10".
		if value and not (value.isdigit() and len(value) == 11):
			frappe.throw(f"{label} must be exactly 11 digits (got {value!r})")
		doc.set(fieldname, value or None)

	# Date of Present APPT is deliberately not checked against Date of 1st APPT: nominal-roll
	# data carries legitimate cases where it reads earlier (e.g. re-appointment, records corrected).
	first_appointment = doc.get(EMPLOYEE_FIRST_APPOINTMENT_FIELD) or doc.date_of_joining

	by_age = add_years(getdate(doc.date_of_birth), RETIREMENT_AGE_YEARS) if doc.date_of_birth else None
	by_service = add_years(getdate(first_appointment), RETIREMENT_SERVICE_YEARS) if first_appointment else None
	doc.set(EMPLOYEE_RETIRE_BY_AGE_FIELD, by_age)
	doc.set(EMPLOYEE_RETIRE_BY_SERVICE_FIELD, by_service)
	# Only fill an empty Date Of Retirement; an explicitly set one (e.g. an approved extension) wins.
	candidates = [d for d in (by_age, by_service) if d]
	if candidates and not doc.date_of_retirement:
		doc.date_of_retirement = min(candidates)


class RestrictedHRDocument(Document):
	def validate(self):
		validate_lga(self.company)
		require_roles(RESTRICTED_HR_ROLES, "You are not permitted to manage restricted personnel records")
		if frappe.db.get_value("Employee", self.employee, "company") != self.company:
			frappe.throw("Employee must belong to the selected LGA")
		self.validate_record()

	def validate_record(self):
		pass


class DTMGPPersonnelFile(RestrictedHRDocument):
	def validate_record(self):
		if self.retention_review_date and getdate(self.retention_review_date) < getdate():
			frappe.throw("Retention Review Date cannot be in the past")


class DTMGPNextofKin(RestrictedHRDocument):
	def validate_record(self):
		if self.is_primary:
			frappe.db.set_value("DTMGP Next of Kin", {"employee": self.employee, "is_primary": 1, "name": ["!=", self.name]}, "is_primary", 0)


class DTMGPStaffDocument(RestrictedHRDocument):
	def validate_record(self):
		if self.expiry_date and self.document_date and getdate(self.expiry_date) < getdate(self.document_date):
			frappe.throw("Expiry Date cannot be before Document Date")
		if self.file:
			file_doc = frappe.db.get_value("File", {"file_url": self.file}, ["name", "is_private"], as_dict=True)
			if not file_doc or not file_doc.is_private:
				frappe.throw("Staff documents must be uploaded as private files")
		if self.has_value_changed("verification_status") and self.verification_status in {"Verified", "Rejected"}:
			self.verified_by = frappe.session.user
			self.verified_on = now_datetime()


class ScopedHRDocument(Document):
	"""Base for dtmgp-owned, LGA-scoped HR DocTypes. Concepts already covered by an
	ERPNext/HRMS DocType (staffing plans, transfers, promotions, separations) are
	extended via Custom DocPerm and permission hooks instead of duplicated here —
	see dtmgp/setup/security.py and dtmgp/permissions/hr.py."""

	allowed_roles = HR_MANAGE_ROLES

	def validate(self):
		validate_lga(self.company)
		if self.is_new() or self.has_value_changed("company"):
			require_roles(self.allowed_roles, "You are not permitted to manage this record")
		self.validate_record()

	def validate_record(self):
		pass

	def _employee_company(self):
		return frappe.db.get_value("Employee", self.employee, "company")


class DTMGPStaffVerificationExercise(ScopedHRDocument):
	def validate_record(self):
		if self.cycle_end_date and self.cycle_start_date and getdate(self.cycle_end_date) < getdate(self.cycle_start_date):
			frappe.throw("Cycle End Date cannot be before Cycle Start Date")


class DTMGPStaffVerificationRecord(ScopedHRDocument):
	def validate_record(self):
		if self._employee_company() != self.company:
			frappe.throw("Employee must belong to the assigned LGA")
		if frappe.db.get_value("DTMGP Staff Verification Exercise", self.exercise, "company") != self.company:
			frappe.throw("Verification Exercise must belong to the same LGA")
		if self.is_new():
			self.prepared_by = frappe.session.user
			self.prepared_on = now_datetime()
		if self.review_status != "Pending":
			if not self.reviewed_by:
				frappe.throw("A reviewer is required to change the review status")
			if self.reviewed_by == self.prepared_by:
				frappe.throw("The preparer of a verification record cannot also review it")
			if self.review_status == "Exception" and not self.exception_reason:
				frappe.throw("An exception reason is required")

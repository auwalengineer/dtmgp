import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime

from dtmgp.finance import require_roles, validate_lga
from dtmgp.permissions.scope import HR_MANAGE_ROLES


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

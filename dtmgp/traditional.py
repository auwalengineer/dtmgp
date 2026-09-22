import frappe
from frappe.model.document import Document
from frappe.utils import getdate

from dtmgp.finance import require_roles, validate_lga
from dtmgp.governance import lga_dated_autoname
from dtmgp.permissions.scope import TRADITIONAL_MANAGE_ROLES

APPOINTMENT_GAZETTE_STATUSES = {"Gazetted", "Installed"}
PETITION_HEARING_STATUSES = {"Council Hearing", "Panel of Inquiry", "Exco Review", "Decided", "Appealed", "Closed"}


class ScopedTraditionalDocument(Document):
	allowed_roles = TRADITIONAL_MANAGE_ROLES

	def validate(self):
		validate_lga(self.company)
		if self.is_new() or self.has_value_changed("company"):
			require_roles(self.allowed_roles, "You are not permitted to manage this record")
		self.validate_record()

	def validate_record(self):
		pass


def _validate_company_link(doc, fieldname, doctype):
	value = doc.get(fieldname)
	if value and frappe.db.get_value(doctype, value, "company") != doc.company:
		frappe.throw(f"{doc.meta.get_label(fieldname)} must belong to the same LGA")


class DTMGPTraditionalInstitution(ScopedTraditionalDocument):
	def autoname(self):
		lga_dated_autoname(self, "INST", "creation")

	def validate_record(self):
		_validate_company_link(self, "parent_institution", "DTMGP Traditional Institution")
		if self.parent_institution and self.parent_institution == self.name:
			frappe.throw("An institution cannot be its own parent")


class DTMGPTraditionalRuler(ScopedTraditionalDocument):
	def autoname(self):
		lga_dated_autoname(self, "RUL", "appointment_date")

	def validate_record(self):
		_validate_company_link(self, "institution", "DTMGP Traditional Institution")
		_validate_company_link(self, "ruling_house", "DTMGP Ruling House")
		if self.status == "Reigning":
			duplicate = frappe.db.exists(
				"DTMGP Traditional Ruler",
				{"institution": self.institution, "status": "Reigning", "name": ["!=", self.name]},
			)
			if duplicate:
				frappe.throw("This institution already has a Reigning ruler")
		if self.status != "Reigning" and not self.reign_end_date:
			frappe.throw("Reign End Date is required once a ruler is no longer Reigning")


class DTMGPRulingHouse(ScopedTraditionalDocument):
	def autoname(self):
		lga_dated_autoname(self, "RH", "creation")

	def validate_record(self):
		_validate_company_link(self, "institution", "DTMGP Traditional Institution")


class DTMGPTraditionalAppointment(ScopedTraditionalDocument):
	def autoname(self):
		lga_dated_autoname(self, "APPT", "application_date")

	def validate_record(self):
		_validate_company_link(self, "institution", "DTMGP Traditional Institution")
		_validate_company_link(self, "ruling_house", "DTMGP Ruling House")
		if self.status in APPOINTMENT_GAZETTE_STATUSES and not self.gazette_reference:
			frappe.throw("Gazette Reference is required once an appointment is Gazetted")
		if self.status == "Installed" and not self.installation_date:
			frappe.throw("Installation Date is required once an appointment is Installed")
		if self.recognition_status == "Suspended" and not self.suspension_reason:
			frappe.throw("Suspension Reason is required when recognition is Suspended")
		if self.recognition_status == "Withdrawn" and not self.withdrawal_reason:
			frappe.throw("Withdrawal Reason is required when recognition is Withdrawn")


class DTMGPSuccessionCase(ScopedTraditionalDocument):
	def autoname(self):
		lga_dated_autoname(self, "SUCC", "vacancy_date")

	def validate_record(self):
		_validate_company_link(self, "institution", "DTMGP Traditional Institution")
		_validate_company_link(self, "eligible_ruling_house", "DTMGP Ruling House")
		_validate_company_link(self, "resulting_appointment", "DTMGP Traditional Appointment")
		if self.status == "Closed" and not self.resulting_appointment:
			frappe.throw("A resulting appointment is required to close a succession case")


class DTMGPChieftaincyPetition(ScopedTraditionalDocument):
	def autoname(self):
		lga_dated_autoname(self, "PET", "petition_date")

	def validate_record(self):
		_validate_company_link(self, "institution", "DTMGP Traditional Institution")
		_validate_company_link(self, "respondent_institution", "DTMGP Traditional Institution")
		if self.status in PETITION_HEARING_STATUSES and self.status != "Closed" and not self.hearing_date and self.status not in {"Decided", "Appealed"}:
			frappe.throw("Hearing Date is required once a petition reaches Council Hearing")
		if self.status in {"Decided", "Appealed", "Closed"} and not self.decision:
			frappe.throw("A decision is required once a petition is Decided")
		if self.status == "Appealed" and not self.appeal_date:
			frappe.throw("Appeal Date is required once a petition is Appealed")


class DTMGPTraditionalAllowance(ScopedTraditionalDocument):
	def autoname(self):
		lga_dated_autoname(self, "ALLOW", "period_start")

	def validate_record(self):
		_validate_company_link(self, "ruler", "DTMGP Traditional Ruler")
		if self.period_end and self.period_start and getdate(self.period_end) < getdate(self.period_start):
			frappe.throw("Period End cannot be before Period Start")
		if self.status == "Paid" and not self.payment_date:
			frappe.throw("Payment Date is required once an allowance is marked Paid")

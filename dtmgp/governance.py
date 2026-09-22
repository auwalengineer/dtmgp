import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import getdate

from dtmgp.finance import require_roles, validate_lga
from dtmgp.permissions.scope import GOVERNANCE_MANAGE_ROLES


def lga_dated_autoname(doc, type_code, date_field):
	"""Compose the {TYPE}-{LGA_CODE}-{YEAR}-{SEQUENCE} identifiers required by
	docs/naming-and-coding-conventions.md. Frappe's `format:` autoname strings can't
	dereference a linked doctype's field, so the LGA code is looked up explicitly and
	the counter is delegated to make_autoname's per-prefix series. `LGA Profile.name`
	(= `lga_code`) is the immutable code table in naming-and-coding-conventions.md;
	`Company.abbr` is not reliable, since seed_lga_companies only sets it at creation
	and never corrects it for a company that already existed under another abbr."""
	code = frappe.db.get_value("LGA Profile", {"company": doc.company}, "name") or frappe.db.get_value("Company", doc.company, "abbr")
	year = getdate(doc.get(date_field) or frappe.utils.nowdate()).year
	doc.name = make_autoname(f"{type_code}-{code}-{year}-.#####")


def validate_company_link(doc, fieldname, doctype):
	"""Cross-link guard mirroring dtmgp.finance._validate_company_link: a linked
	governance record (e.g. a Resolution's Meeting) must belong to the same LGA."""
	value = doc.get(fieldname)
	if value and frappe.db.get_value(doctype, value, "company") != doc.company:
		frappe.throw(f"{doc.meta.get_label(fieldname)} must belong to the same LGA")


class ScopedGovernanceDocument(Document):
	allowed_roles = GOVERNANCE_MANAGE_ROLES

	def validate(self):
		validate_lga(self.company)
		if self.is_new() or self.has_value_changed("company"):
			require_roles(self.allowed_roles, "You are not permitted to manage this record")
		self.validate_record()

	def validate_record(self):
		pass


class DTMGPCorrespondence(ScopedGovernanceDocument):
	def autoname(self):
		lga_dated_autoname(self, "COR", "correspondence_date")

	def validate_record(self):
		if self.correspondence_type in {"Incoming", "Outgoing"} and not self.correspondent:
			label = "Sender" if self.correspondence_type == "Incoming" else "Recipient"
			frappe.throw(f"{label} is required for {self.correspondence_type} correspondence")
		if self.department and frappe.db.get_value("Department", self.department, "company") != self.company:
			frappe.throw("Department must belong to the same LGA")
		if self.due_date and self.correspondence_date and getdate(self.due_date) < getdate(self.correspondence_date):
			frappe.throw("Due Date cannot be before the Correspondence Date")


class DTMGPMeeting(ScopedGovernanceDocument):
	def autoname(self):
		lga_dated_autoname(self, "CM", "meeting_date")

	def validate_record(self):
		if self.minutes_finalized and self.status != "Held":
			frappe.throw("Minutes can only be finalized for a meeting marked Held")


class DTMGPMeetingAgendaItem(Document):
	pass


class DTMGPMeetingAttendee(Document):
	pass


class DTMGPResolution(ScopedGovernanceDocument):
	def autoname(self):
		lga_dated_autoname(self, "RES", "creation")

	def validate_record(self):
		validate_company_link(self, "meeting", "DTMGP Meeting")
		if self.status == "Adopted" and not self.adopted_date:
			self.adopted_date = frappe.utils.nowdate()


class DTMGPResolutionAction(ScopedGovernanceDocument):
	def autoname(self):
		lga_dated_autoname(self, "RAC", "due_date")

	def validate_record(self):
		validate_company_link(self, "resolution", "DTMGP Resolution")
		if self.responsible_department and frappe.db.get_value("Department", self.responsible_department, "company") != self.company:
			frappe.throw("Responsible Department must belong to the same LGA")
		if self.status == "Completed" and not self.completed_date:
			self.completed_date = frappe.utils.nowdate()


class DTMGPStatutoryReturnType(Document):
	"""State-managed reference catalogue, not LGA-scoped: the same statutory return
	requirements apply to every LGA. Seeded with a starter set by
	dtmgp.setup.governance.seed_governance_catalogue; the authoritative catalogue is
	an external production condition, same as Finance's revenue-head catalogue."""

	pass


class DTMGPStatutoryReturn(ScopedGovernanceDocument):
	def autoname(self):
		lga_dated_autoname(self, "RET", "due_date")

	def validate_record(self):
		if self.return_type and frappe.db.get_value("DTMGP Statutory Return Type", self.return_type, "disabled"):
			frappe.throw("Return Type is disabled")
		if self.status == "Submitted" and not self.submitted_date:
			self.submitted_date = frappe.utils.nowdate()


class DTMGPComplianceRequirement(Document):
	"""State-managed reference catalogue, not LGA-scoped — see DTMGPStatutoryReturnType."""

	pass


class DTMGPComplianceSubmission(ScopedGovernanceDocument):
	def autoname(self):
		lga_dated_autoname(self, "CMP", "due_date")

	def validate_record(self):
		if self.requirement and frappe.db.get_value("DTMGP Compliance Requirement", self.requirement, "disabled"):
			frappe.throw("Compliance Requirement is disabled")
		if self.status == "Submitted" and not self.submitted_date:
			self.submitted_date = frappe.utils.nowdate()


class DTMGPApprovalDelegation(ScopedGovernanceDocument):
	def validate_record(self):
		if self.delegator == self.delegate:
			frappe.throw("A delegator cannot delegate to themselves")
		if self.end_date and self.start_date and getdate(self.end_date) < getdate(self.start_date):
			frappe.throw("End Date cannot be before Start Date")

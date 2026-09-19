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

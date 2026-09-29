import frappe
from frappe.model.document import Document

from dtmgp.finance import require_roles, validate_lga
from dtmgp.governance import lga_dated_autoname

# Only Project Officer/State Administrator may *create* a Projects-module record
# (docs/role-permission-matrix.md gives LGA Chairman/LGA Secretary "A" -- approve an
# existing record -- not "C"); PROJECTS_MANAGE_ROLES is the broader create-or-approve
# gate used by dtmgp/api/v1/projects.py's require_projects_access(write=True).
PROJECTS_CREATE_ROLES = {"State Administrator", "Project Officer"}


def _validate_company_link(doc, fieldname, doctype):
	value = doc.get(fieldname)
	if value and frappe.db.get_value(doctype, value, "company") != doc.company:
		frappe.throw(f"{doc.meta.get_label(fieldname)} must belong to the same LGA")


class ScopedProjectsDocument(Document):
	allowed_roles = PROJECTS_CREATE_ROLES

	def validate(self):
		validate_lga(self.company)
		if self.is_new() or self.has_value_changed("company"):
			require_roles(self.allowed_roles, "You are not permitted to manage this record")
		self.validate_record()

	def validate_record(self):
		pass


class DTMGPProjectInspection(ScopedProjectsDocument):
	def autoname(self):
		lga_dated_autoname(self, "INSP", "scheduled_date")

	def validate_record(self):
		_validate_company_link(self, "project", "Project")
		if self.status == "Exception" and not self.exception_reason:
			frappe.throw("Exception Reason is required when the inspection status is Exception")


class DTMGPAssetVerification(ScopedProjectsDocument):
	def autoname(self):
		lga_dated_autoname(self, "AVER", "verification_date")

	def validate_record(self):
		_validate_company_link(self, "asset", "Asset")


class DTMGPProjectProposal(ScopedProjectsDocument):
	def validate_record(self):
		if self.department and frappe.db.get_value("Department", self.department, "company") != self.company:
			frappe.throw("Department must belong to the selected LGA")
		if self.expected_end_date and self.expected_start_date and frappe.utils.getdate(self.expected_end_date) < frappe.utils.getdate(self.expected_start_date):
			frappe.throw("Expected End cannot be before Expected Start")
		if self.status in {"Approved", "Converted"} and not self.approval_reference:
			frappe.throw("Approval Reference is required for an approved proposal")


class DTMGPAssetDisposal(ScopedProjectsDocument):
	def validate_record(self):
		_validate_company_link(self, "asset", "Asset")
		if self.status == "Disposed" and (not self.approval_reference or not self.journal_entry or not self.disposal_date):
			frappe.throw("Approval Reference, Journal Entry and Disposal Date are required before disposal")


class DTMGPContractorDocument(ScopedProjectsDocument):
	def validate_record(self):
		if self.expiry_date and self.issue_date and frappe.utils.getdate(self.expiry_date) < frappe.utils.getdate(self.issue_date):
			frappe.throw("Expiry Date cannot be before Issue Date")
		file_doc = frappe.db.get_value("File", {"file_url": self.file}, "is_private") if self.file else None
		if not file_doc:
			frappe.throw("Contractor documents must be uploaded as private files")

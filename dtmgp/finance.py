import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate

from dtmgp.permissions.scope import get_allowed_companies
from dtmgp.setup.organization import PARENT_COMPANY


FINANCE_WRITE_ROLES = {"System Manager", "State Administrator", "LGA Administrator", "Treasurer"}
REVENUE_WRITE_ROLES = FINANCE_WRITE_ROLES | {"Revenue Officer"}
PROCUREMENT_WRITE_ROLES = FINANCE_WRITE_ROLES | {"Procurement Officer"}
AUDIT_ROLES = {"System Manager", "State Administrator", "State Auditor", "Internal Auditor"}


def validate_lga(company):
	if not company or frappe.db.get_value("Company", company, "parent_company") != PARENT_COMPANY:
		frappe.throw("A valid Benue LGA company is required")
	if company not in get_allowed_companies():
		frappe.throw("LGA is outside your permitted scope", frappe.PermissionError)


def require_roles(roles, message):
	if frappe.session.user != "Administrator" and not set(frappe.get_roles()).intersection(roles):
		frappe.throw(message, frappe.PermissionError)


class ScopedFinanceDocument(Document):
	allowed_roles = FINANCE_WRITE_ROLES

	def validate(self):
		validate_lga(self.company)
		if self.is_new() or self.has_value_changed("company"):
			require_roles(self.allowed_roles, "You are not permitted to manage this record")
		self.validate_record()

	def validate_record(self):
		pass


class DTMGPApprovalLimit(ScopedFinanceDocument):
	def validate_record(self):
		if flt(self.minimum_amount) < 0 or flt(self.maximum_amount) <= flt(self.minimum_amount):
			frappe.throw("Maximum amount must be greater than minimum amount")


class DTMGPRevenueHead(ScopedFinanceDocument):
	allowed_roles = REVENUE_WRITE_ROLES

	def validate_record(self):
		duplicate = frappe.db.exists("DTMGP Revenue Head", {"company": self.company, "revenue_code": self.revenue_code, "name": ["!=", self.name]})
		if duplicate:
			frappe.throw("Revenue Code must be unique within the LGA")
		if self.valid_from and self.valid_to and getdate(self.valid_to) < getdate(self.valid_from):
			frappe.throw("Valid To cannot be before Valid From")


class DTMGPRevenueAssessment(ScopedFinanceDocument):
	allowed_roles = REVENUE_WRITE_ROLES

	def validate_record(self):
		_validate_company_link(self, "revenue_head", "DTMGP Revenue Head")
		if flt(self.amount) <= 0:
			frappe.throw("Assessment amount must be greater than zero")
		if self.due_date and getdate(self.due_date) < getdate(self.assessment_date):
			frappe.throw("Due Date cannot be before Assessment Date")

	def on_submit(self):
		self.db_set("status", "Unpaid")


class DTMGPRevenueReceipt(ScopedFinanceDocument):
	allowed_roles = REVENUE_WRITE_ROLES

	def validate_record(self):
		_validate_company_link(self, "assessment", "DTMGP Revenue Assessment")
		if flt(self.amount) <= 0:
			frappe.throw("Receipt amount must be greater than zero")
		assessment = frappe.get_doc("DTMGP Revenue Assessment", self.assessment)
		if assessment.docstatus != 1:
			frappe.throw("Revenue Assessment must be submitted before receipting")
		paid = frappe.db.sql(
			"""select coalesce(sum(amount), 0) from `tabDTMGP Revenue Receipt`
			where assessment=%s and docstatus=1 and name != %s""",
			(self.assessment, self.name or ""),
		)[0][0]
		if flt(paid) + flt(self.amount) > flt(assessment.amount):
			frappe.throw("Receipt exceeds the outstanding assessment amount")

	def on_submit(self):
		self._update_assessment()

	def on_cancel(self):
		self._update_assessment()

	def _update_assessment(self):
		assessment = frappe.get_doc("DTMGP Revenue Assessment", self.assessment)
		paid = frappe.db.sql(
			"select coalesce(sum(amount), 0) from `tabDTMGP Revenue Receipt` where assessment=%s and docstatus=1",
			self.assessment,
		)[0][0]
		status = "Paid" if flt(paid) >= flt(assessment.amount) else ("Part Paid" if paid else "Unpaid")
		assessment.db_set({"amount_paid": paid, "status": status})


class DTMGPProcurementPlan(ScopedFinanceDocument):
	allowed_roles = PROCUREMENT_WRITE_ROLES

	def validate_record(self):
		if flt(self.estimated_amount) <= 0:
			frappe.throw("Estimated amount must be greater than zero")
		if self.planned_start_date and self.planned_end_date and getdate(self.planned_end_date) < getdate(self.planned_start_date):
			frappe.throw("Planned End Date cannot be before Planned Start Date")


class DTMGPProcurementCase(ScopedFinanceDocument):
	allowed_roles = PROCUREMENT_WRITE_ROLES

	def validate_record(self):
		_validate_company_link(self, "procurement_plan", "DTMGP Procurement Plan")
		if flt(self.estimated_amount) <= 0:
			frappe.throw("Estimated amount must be greater than zero")
		if self.status in {"Evaluated", "Approved", "Awarded", "Completed"} and not self.recommended_supplier:
			frappe.throw("A recommended supplier is required after bid evaluation")
		if self.status in {"Awarded", "Completed"} and not self.purchase_order:
			frappe.throw("An ERPNext Purchase Order is required for an awarded procurement")


class DTMGPPaymentRequest(ScopedFinanceDocument):
	def validate_record(self):
		if flt(self.amount) <= 0:
			frappe.throw("Payment amount must be greater than zero")
		if not self.procurement_case and not self.justification:
			frappe.throw("A procurement case or expenditure justification is required")
		_validate_company_link(self, "procurement_case", "DTMGP Procurement Case")


class DTMGPAuditQuery(ScopedFinanceDocument):
	allowed_roles = AUDIT_ROLES

	def validate_record(self):
		if self.response_due_date and getdate(self.response_due_date) < getdate(self.query_date):
			frappe.throw("Response Due Date cannot be before Query Date")


def _validate_company_link(doc, fieldname, doctype):
	value = doc.get(fieldname)
	if value and frappe.db.get_value(doctype, value, "company") != doc.company:
		frappe.throw(f"{doc.meta.get_label(fieldname)} must belong to the same LGA")

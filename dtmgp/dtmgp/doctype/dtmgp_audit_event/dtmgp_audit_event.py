import frappe
from frappe import _
from frappe.model.document import Document


class DTMGPAuditEvent(Document):
	def before_save(self):
		if not self.is_new():
			frappe.throw(_("Audit events are append-only"))

	def on_trash(self):
		frappe.throw(_("Audit events cannot be deleted"))

import frappe
from frappe import _
from frappe.model.document import Document

from dtmgp.setup.organization import BENUE_LGAS, PARENT_COMPANY


class LGAProfile(Document):
	def validate(self):
		approved = {lga.abbr: lga for lga in BENUE_LGAS}
		lga = approved.get(self.lga_code)
		if not lga or self.lga_name != lga.name or self.company != lga.company_name:
			frappe.throw(_("LGA name, code and Company must match the approved Benue registry"))
		if frappe.db.get_value("Company", self.company, "parent_company") != PARENT_COMPANY:
			frappe.throw(_("LGA Profile Company must be a child of the Benue State parent Company"))
		duplicate = frappe.db.exists("LGA Profile", {"company": self.company, "name": ["!=", self.name]})
		if duplicate:
			frappe.throw(_("Company is already linked to LGA Profile {0}").format(duplicate))

	def before_rename(self, old_name, new_name, merge=False):
		frappe.throw(_("LGA codes are immutable"))

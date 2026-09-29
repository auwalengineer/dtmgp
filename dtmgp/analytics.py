from urllib.parse import urlparse

import frappe
from frappe.model.document import Document
from frappe.utils import flt

from dtmgp.finance import require_roles


class DTMGPAnalyticsControl(Document):
	def validate(self):
		require_roles({"System Manager", "State Administrator"}, "Only state administration may manage analytics controls")
		if self.control_type == "KPI Configuration":
			if not self.kpi_key or flt(self.weight) <= 0:
				frappe.throw("KPI and a positive weight are required")
			if flt(self.critical_threshold) > flt(self.warning_threshold):
				frappe.throw("Critical Threshold cannot exceed Warning Threshold")
		elif self.control_type == "External Integration":
			parsed = urlparse(self.endpoint_url or "")
			if parsed.scheme != "https" or not parsed.netloc:
				frappe.throw("External integrations require an HTTPS endpoint")
			if self.status in {"Approved", "Active"} and not self.data_sharing_agreement:
				frappe.throw("An approved integration requires a data-sharing agreement")
		elif self.control_type == "Staging Acceptance":
			if self.status == "Approved" and not all((self.company, self.accepted_role, self.accepted_by, self.accepted_on, self.evidence)):
				frappe.throw("Approved staging acceptance requires LGA, role, representative, date and evidence")

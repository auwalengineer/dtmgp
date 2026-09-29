import json
from uuid import uuid4

import frappe
from frappe.client import get as client_get
from frappe.tests.utils import FrappeTestCase

from dtmgp.audit import record_event
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup


class TestAuditEvent(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_event_is_queryable_redacted_and_append_only(self):
		company = BENUE_LGAS[0].company_name
		record_event(
			"test_event",
			"Audit test",
			company=company,
			metadata={"operation": "test", "token": "must-not-be-stored", "nested": {"password": "secret"}},
		)
		name = frappe.get_all("DTMGP Audit Event", filters={"event_type": "test_event"}, pluck="name", limit=1)[0]
		doc = frappe.get_doc("DTMGP Audit Event", name)
		metadata = json.loads(doc.metadata_json)
		self.assertEqual(metadata["operation"], "test")
		self.assertEqual(metadata["token"], "[REDACTED]")
		self.assertEqual(metadata["nested"]["password"], "[REDACTED]")

		doc.summary = "Changed"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("DTMGP Audit Event", name, ignore_permissions=True)

	def test_event_read_is_scoped_to_the_actors_lga(self):
		"""Stage 2 direct-hook coverage for DTMGP Audit Event, complementing
		test_administration.py's role-gate test of the list_audit_events API wrapper --
		this proves dtmgp/permissions/audit_event.py's has_permission/
		get_permission_query_conditions hooks themselves deny cross-LGA reads, the same
		way test_isolation.py covers other hook-only doctypes."""
		seed_security_setup()
		makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
		gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")
		makurdi_auditor = self._make_user("Internal Auditor", makurdi)
		gboko_auditor = self._make_user("Internal Auditor", gboko)

		event_type = f"isolation_test_{uuid4().hex[:8]}"
		record_event(event_type, "Isolation test event", company=makurdi)
		name = frappe.get_all("DTMGP Audit Event", filters={"event_type": event_type}, pluck="name", limit=1)[0]

		frappe.set_user(gboko_auditor.name)
		with self.assertRaises(frappe.PermissionError):
			client_get("DTMGP Audit Event", name)
		self.assertNotIn(name, frappe.get_list("DTMGP Audit Event", pluck="name"))

		frappe.set_user(makurdi_auditor.name)
		result = client_get("DTMGP Audit Event", name)
		self.assertEqual(result["name"], name)

	def _make_user(self, role, company):
		return frappe.get_doc(
			{
				"doctype": "User",
				"email": f"audit-iso-{uuid4().hex}@example.com",
				"first_name": "Audit Isolation",
				"enabled": 1,
				"send_welcome_email": 0,
				"dtmgp_lga": company,
				"roles": [{"role": role}],
			}
		).insert()

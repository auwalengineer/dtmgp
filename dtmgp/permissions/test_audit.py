import json

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.audit import record_event
from dtmgp.setup.organization import BENUE_LGAS


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

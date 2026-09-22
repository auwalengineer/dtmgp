import frappe

# Starter catalogue only. The authoritative statutory-return and compliance
# catalogues (full list, legal citations, filing rates) are an external production
# condition — same status as Finance's approved revenue-head catalogue in
# docs/implementation-status.md — and must be confirmed by the relevant business
# owners before this list is treated as complete.
STATUTORY_RETURN_TYPES = (
	{"return_name": "Monthly Financial Return", "statutory_body": "Benue State Ministry of Local Government", "frequency": "Monthly"},
	{"return_name": "Quarterly Council Activity Return", "statutory_body": "Benue State Ministry of Local Government", "frequency": "Quarterly"},
	{"return_name": "Annual Statement of Accounts", "statutory_body": "Office of the State Auditor-General for Local Government", "frequency": "Annually"},
)
COMPLIANCE_REQUIREMENTS = (
	{"requirement_name": "Council Meeting Minutes Filing", "category": "Governance", "frequency": "Monthly"},
	{"requirement_name": "Staff Establishment Return", "category": "Human Resources", "frequency": "Quarterly"},
	{"requirement_name": "Procurement Plan Publication", "category": "Procurement", "frequency": "Annually"},
)


def seed_governance_catalogue():
	"""Idempotent starter catalogue for DTMGP Statutory Return Type / DTMGP
	Compliance Requirement, safe to rerun on install and migration."""
	created = {"return_types": [], "compliance_requirements": []}
	# ignore_permissions: install/migration-time seeding runs before any user session
	# exists, matching seed_lga_companies/seed_security_setup elsewhere in dtmgp/setup.
	for entry in STATUTORY_RETURN_TYPES:
		if frappe.db.exists("DTMGP Statutory Return Type", entry["return_name"]):
			continue
		frappe.get_doc({"doctype": "DTMGP Statutory Return Type", "description": "Starter catalogue entry, pending state confirmation.", **entry}).insert(ignore_permissions=True)
		created["return_types"].append(entry["return_name"])
	for entry in COMPLIANCE_REQUIREMENTS:
		if frappe.db.exists("DTMGP Compliance Requirement", entry["requirement_name"]):
			continue
		frappe.get_doc({"doctype": "DTMGP Compliance Requirement", "description": "Starter catalogue entry, pending state confirmation.", **entry}).insert(ignore_permissions=True)
		created["compliance_requirements"].append(entry["requirement_name"])
	return created

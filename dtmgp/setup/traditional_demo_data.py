"""Local/dev demo data for the Chieftaincy & Traditional Institutions module. Not part
of install/migrate -- run manually with
`bench --site <site> execute dtmgp.setup.traditional_demo_data.seed_traditional_demo_data`.
Safe to re-run: every record lookup is idempotent."""

import frappe

from dtmgp.api.v1.traditional import save_record, transition_record, update_recognition
from dtmgp.setup.organization import BENUE_LGAS
from dtmgp.setup.security import seed_security_setup

TRADITIONAL_DOCTYPES = (
	"DTMGP Traditional Allowance",
	"DTMGP Chieftaincy Petition",
	"DTMGP Succession Case",
	"DTMGP Traditional Appointment",
	"DTMGP Traditional Ruler",
	"DTMGP Ruling House",
	"DTMGP Traditional Institution",
)


def reset_traditional_demo_data():
	"""Delete any previously-seeded demo records so seed_traditional_demo_data starts
	clean. Safe to run even if nothing exists yet."""
	frappe.set_user("Administrator")
	for doctype in TRADITIONAL_DOCTYPES:
		for name in frappe.get_all(doctype, filters={"company": ["like", "%Local Government Area"]}, pluck="name"):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
	frappe.db.commit()


def seed_traditional_demo_data():
	frappe.set_user("Administrator")
	seed_security_setup()

	makurdi = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Makurdi")
	gboko = next(lga.company_name for lga in BENUE_LGAS if lga.name == "Gboko")

	def make_user(email, first_name, company):
		if frappe.db.exists("User", email):
			return email
		return frappe.get_doc({
			"doctype": "User", "email": email, "first_name": first_name, "enabled": 1,
			"send_welcome_email": 0, "new_password": "Demo@12345", "dtmgp_lga": company,
			"roles": [{"role": "Traditional Affairs Officer"}],
		}).insert().name

	officer_mkd = make_user("traditional.officer@makurdi.gov.ng", "Iveren", makurdi)
	officer_gbk = make_user("traditional.officer@gboko.gov.ng", "Orpin", gboko)

	def get_or_create(doctype, lookup, values, user):
		existing = frappe.db.exists(doctype, lookup)
		if existing:
			return existing
		frappe.set_user(user)
		return save_record(doctype, {**lookup, **values})["name"]

	# ---- Institutions ----
	council_mkd = get_or_create(
		"DTMGP Traditional Institution",
		{"company": makurdi, "institution_name": "Makurdi Traditional Council"},
		{"institution_type": "LGA Traditional Council", "status": "Active",
			"founding_basis": "Established under the Benue State Chieftaincy Law to coordinate recognised stools within Makurdi LGA."},
		officer_mkd,
	)
	agan = get_or_create(
		"DTMGP Traditional Institution",
		{"company": makurdi, "institution_name": "Agan Chiefdom"},
		{"institution_type": "First Class Stool", "rank_class": "First Class", "parent_institution": council_mkd,
			"seat_location": "Agan Palace, Makurdi", "status": "Active"},
		officer_mkd,
	)
	wadata = get_or_create(
		"DTMGP Traditional Institution",
		{"company": makurdi, "institution_name": "Wadata Ward"},
		{"institution_type": "Clan/Ward Headship", "parent_institution": agan,
			"seat_location": "Wadata, Makurdi", "status": "Active"},
		officer_mkd,
	)
	council_gbk = get_or_create(
		"DTMGP Traditional Institution",
		{"company": gboko, "institution_name": "Gboko Traditional Council"},
		{"institution_type": "LGA Traditional Council", "status": "Active",
			"founding_basis": "Established under the Benue State Chieftaincy Law to coordinate recognised stools within Gboko LGA."},
		officer_gbk,
	)
	yandev = get_or_create(
		"DTMGP Traditional Institution",
		{"company": gboko, "institution_name": "Yandev Chiefdom"},
		{"institution_type": "First Class Stool", "rank_class": "First Class", "parent_institution": council_gbk,
			"seat_location": "Yandev Palace, Gboko", "status": "Vacant"},
		officer_gbk,
	)

	# ---- Ruling houses ----
	utange = get_or_create(
		"DTMGP Ruling House", {"company": makurdi, "house_name": "Utange Ruling House", "institution": agan},
		{"rotation_order": 1, "is_eligible": 1, "last_occupied_from": "2016-04-15"}, officer_mkd,
	)
	get_or_create(
		"DTMGP Ruling House", {"company": makurdi, "house_name": "Ikpa Ruling House", "institution": agan},
		{"rotation_order": 2, "is_eligible": 1, "notes": "Next in rotation after the Utange Ruling House's current tenure."}, officer_mkd,
	)
	mbayion = get_or_create(
		"DTMGP Ruling House", {"company": makurdi, "house_name": "Mbayion Ruling House", "institution": wadata},
		{"rotation_order": 1, "is_eligible": 1}, officer_mkd,
	)
	anyiin = get_or_create(
		"DTMGP Ruling House", {"company": gboko, "house_name": "Anyiin Ruling House", "institution": yandev},
		{"rotation_order": 1, "is_eligible": 1}, officer_gbk,
	)

	# ---- Reigning ruler (Agan) ----
	get_or_create(
		"DTMGP Traditional Ruler",
		{"company": makurdi, "ruler_name": "Chief Terhemba Ikya", "institution": agan},
		{"ruling_house": utange, "gender": "Male", "date_of_birth": "1968-09-12", "appointment_date": "2016-03-10",
			"installation_date": "2016-04-15", "gazette_reference": "BNG/GAZ/2016/014", "status": "Reigning"},
		officer_mkd,
	)

	# ---- Deceased ruler leaving Wadata Ward vacant ----
	get_or_create(
		"DTMGP Traditional Ruler",
		{"company": makurdi, "ruler_name": "Chief Aondoana Utsu", "institution": wadata},
		{"ruling_house": mbayion, "gender": "Male", "date_of_birth": "1948-02-02", "appointment_date": "1998-06-01",
			"installation_date": "1998-07-20", "gazette_reference": "BNG/GAZ/1998/077", "status": "Deceased",
			"reign_end_date": "2026-06-15", "reign_end_reason": "Passed away after a brief illness; the stool was declared vacant pending succession."},
		officer_mkd,
	)

	# ---- Succession case for Wadata Ward (in progress) ----
	frappe.set_user(officer_mkd)
	succession = get_or_create(
		"DTMGP Succession Case",
		{"company": makurdi, "institution": wadata, "vacancy_date": "2026-06-15"},
		{"vacancy_reason": "Death", "eligible_ruling_house": mbayion, "candidates": "Iortyom Agera, Doose Chia"},
		officer_mkd,
	)
	if frappe.db.get_value("DTMGP Succession Case", succession, "status") == "Open":
		transition_record("DTMGP Succession Case", succession, "Candidates Nominated")
		transition_record("DTMGP Succession Case", succession, "Kingmakers Deliberation")

	# ---- Appointment: front-runner nominated for Wadata Ward, still pending ----
	get_or_create(
		"DTMGP Traditional Appointment",
		{"company": makurdi, "institution": wadata, "candidate_name": "Iortyom Agera"},
		{"ruling_house": mbayion, "application_date": "2026-07-10"},
		officer_mkd,
	)

	# ---- Petition contesting that nomination (open) ----
	frappe.set_user(officer_mkd)
	petition_open = get_or_create(
		"DTMGP Chieftaincy Petition",
		{"company": makurdi, "institution": wadata, "petitioner_name": "Doose Chia"},
		{"petition_type": "Eligibility Challenge", "petition_date": "2026-07-20",
			"description": "Doose Chia challenges the nomination of Iortyom Agera to the Wadata Ward stool, "
				"alleging he is not a recognised member of the Mbayion Ruling House."},
		officer_mkd,
	)
	if frappe.db.get_value("DTMGP Chieftaincy Petition", petition_open, "status") == "Filed":
		transition_record("DTMGP Chieftaincy Petition", petition_open, "Council Hearing")

	# ---- Petition, fully closed (historical) ----
	frappe.set_user(officer_mkd)
	petition_closed = get_or_create(
		"DTMGP Chieftaincy Petition",
		{"company": makurdi, "institution": agan, "petitioner_name": "Community Elders' Forum, Agan"},
		{"petition_type": "Rival Claim", "petition_date": "2015-11-05",
			"description": "Community elders petitioned against the Ikpa Ruling House's claim of precedence "
				"in the 2016 selection for the Agan stool."},
		officer_mkd,
	)
	if frappe.db.get_value("DTMGP Chieftaincy Petition", petition_closed, "status") == "Filed":
		transition_record("DTMGP Chieftaincy Petition", petition_closed, "Council Hearing")
		transition_record("DTMGP Chieftaincy Petition", petition_closed, "Panel of Inquiry")
		transition_record("DTMGP Chieftaincy Petition", petition_closed, "Exco Review")
		save_record("DTMGP Chieftaincy Petition", {
			"decision": "The Benue State Executive Council upheld the Utange Ruling House's rotational claim "
				"and confirmed the selection of Chief Terhemba Ikya.",
			"panel_reference": "PANEL/2016/003",
		}, name=petition_closed)
		transition_record("DTMGP Chieftaincy Petition", petition_closed, "Decided")
		save_record("DTMGP Chieftaincy Petition", {"appeal_outcome": "State Executive Council affirmed the original decision on review."}, name=petition_closed)
		transition_record("DTMGP Chieftaincy Petition", petition_closed, "Appealed")
		transition_record("DTMGP Chieftaincy Petition", petition_closed, "Closed")

	# ---- Appointment, fully installed (Yandev Chiefdom) ----
	frappe.set_user(officer_gbk)
	appointment_installed = get_or_create(
		"DTMGP Traditional Appointment",
		{"company": gboko, "institution": yandev, "candidate_name": "Terkimbi Ityoakaa"},
		{"ruling_house": anyiin, "application_date": "2026-02-01"},
		officer_gbk,
	)
	if frappe.db.get_value("DTMGP Traditional Appointment", appointment_installed, "status") == "Nominated":
		for target in ["Kingmakers Selection", "Council Endorsed", "Ministry Vetting", "Exco Approved", "Governor Approved"]:
			transition_record("DTMGP Traditional Appointment", appointment_installed, target)
		save_record("DTMGP Traditional Appointment", {"gazette_reference": "BNG/GAZ/2026/031", "gazette_date": "2026-08-05"}, name=appointment_installed)
		transition_record("DTMGP Traditional Appointment", appointment_installed, "Gazetted")
		transition_record("DTMGP Traditional Appointment", appointment_installed, "Installed")
		save_record("DTMGP Traditional Appointment", {"certificate_number": "CERT-2026-YND-01"}, name=appointment_installed)
		update_recognition(appointment_installed, "Approved")

	installed = frappe.get_doc("DTMGP Traditional Appointment", appointment_installed)
	yandev_ruler = get_or_create(
		"DTMGP Traditional Ruler",
		{"company": gboko, "ruler_name": "Terkimbi Ityoakaa", "institution": yandev},
		{"ruling_house": anyiin, "gender": "Male", "date_of_birth": "1975-05-19",
			"appointment_date": installed.application_date, "installation_date": installed.installation_date,
			"gazette_reference": installed.gazette_reference, "status": "Reigning"},
		officer_gbk,
	)
	if frappe.db.get_value("DTMGP Traditional Institution", yandev, "status") != "Active":
		save_record("DTMGP Traditional Institution", {"status": "Active"}, name=yandev)

	# ---- Allowances for the reigning Agan ruler ----
	ikya = frappe.db.get_value("DTMGP Traditional Ruler", {"company": makurdi, "ruler_name": "Chief Terhemba Ikya"})
	frappe.set_user(officer_mkd)
	allowance_paid = get_or_create(
		"DTMGP Traditional Allowance",
		{"company": makurdi, "ruler": ikya, "allowance_type": "Stipend", "period_start": "2026-01-01"},
		{"amount": 180000, "period_end": "2026-01-31"},
		officer_mkd,
	)
	if frappe.db.get_value("DTMGP Traditional Allowance", allowance_paid, "status") == "Draft":
		transition_record("DTMGP Traditional Allowance", allowance_paid, "Approved")
		save_record("DTMGP Traditional Allowance", {"payment_reference": "TRX-STP-2026-01"}, name=allowance_paid)
		transition_record("DTMGP Traditional Allowance", allowance_paid, "Paid")

	allowance_approved = get_or_create(
		"DTMGP Traditional Allowance",
		{"company": makurdi, "ruler": ikya, "allowance_type": "Vehicle", "period_start": "2026-01-01"},
		{"amount": 450000, "period_end": "2026-03-31"},
		officer_mkd,
	)
	if frappe.db.get_value("DTMGP Traditional Allowance", allowance_approved, "status") == "Draft":
		transition_record("DTMGP Traditional Allowance", allowance_approved, "Approved")

	allowance_draft = get_or_create(
		"DTMGP Traditional Allowance",
		{"company": makurdi, "ruler": ikya, "allowance_type": "Sitting Allowance", "period_start": "2026-08-01"},
		{"amount": 25000, "period_end": "2026-08-31"},
		officer_mkd,
	)

	frappe.db.commit()
	return {
		"users": [officer_mkd, officer_gbk],
		"institutions": [council_mkd, agan, wadata, council_gbk, yandev],
		"ruling_houses": [utange, mbayion, anyiin],
		"rulers": [ikya, yandev_ruler],
		"succession_case": succession,
		"appointments": [appointment_installed],
		"petitions": [petition_open, petition_closed],
		"allowances": [allowance_paid, allowance_approved, allowance_draft],
	}

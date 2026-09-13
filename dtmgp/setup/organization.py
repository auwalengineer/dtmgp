from dataclasses import dataclass

import frappe
from frappe.utils.nestedset import rebuild_tree

PARENT_COMPANY = "Benue State Local Government Administration"
DEFAULT_COUNTRY = "Nigeria"
DEFAULT_CURRENCY = "NGN"


@dataclass(frozen=True)
class LGA:
	name: str
	abbr: str

	@property
	def company_name(self):
		return f"{self.name} Local Government Area"


BENUE_LGAS = (
	LGA("Ado", "ADO"),
	LGA("Agatu", "AGT"),
	LGA("Apa", "APA"),
	LGA("Buruku", "BRK"),
	LGA("Gboko", "GBK"),
	LGA("Guma", "GMA"),
	LGA("Gwer East", "GWE"),
	LGA("Gwer West", "GWW"),
	LGA("Katsina-Ala", "KAL"),
	LGA("Konshisha", "KNS"),
	LGA("Kwande", "KWD"),
	LGA("Logo", "LOG"),
	LGA("Makurdi", "MKD"),
	LGA("Obi", "OBI"),
	LGA("Ogbadibo", "OGD"),
	LGA("Ohimini", "OHM"),
	LGA("Oju", "OJU"),
	LGA("Okpokwu", "OKP"),
	LGA("Otukpo", "OTK"),
	LGA("Tarka", "TRK"),
	LGA("Ukum", "UKM"),
	LGA("Ushongo", "USH"),
	LGA("Vandeikya", "VDK"),
)


def seed_lga_companies():
	"""Create the Benue parent Company and its 23 LGA child Companies."""
	parent = _ensure_parent_company()
	created = []
	updated = []

	for lga in BENUE_LGAS:
		company_name = _find_company_case_insensitively(lga.company_name)
		if company_name:
			company = frappe.get_doc("Company", company_name)
			if company.parent_company != parent.name or company.is_group:
				company.parent_company = parent.name
				company.is_group = 0
				company.save()
				updated.append(company.name)
			continue

		company = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": lga.company_name,
				"abbr": lga.abbr,
				"default_currency": DEFAULT_CURRENCY,
				"country": DEFAULT_COUNTRY,
				"parent_company": parent.name,
				"is_group": 0,
			}
		)
		company.insert()
		created.append(company.name)

	rebuild_tree("Company", "parent_company")
	return {"parent": parent.name, "created": created, "updated": updated}


def _ensure_parent_company():
	if frappe.db.exists("Company", PARENT_COMPANY):
		parent = frappe.get_doc("Company", PARENT_COMPANY)
		if not parent.is_group:
			parent.is_group = 1
			parent.save()
		return parent

	parent = frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": PARENT_COMPANY,
			"abbr": "BSLGA",
			"default_currency": DEFAULT_CURRENCY,
			"country": DEFAULT_COUNTRY,
			"is_group": 1,
		}
	)
	parent.insert()
	return parent


def _find_company_case_insensitively(company_name):
	for existing_name in frappe.get_all("Company", pluck="name"):
		if existing_name.casefold() == company_name.casefold():
			return existing_name
	return None

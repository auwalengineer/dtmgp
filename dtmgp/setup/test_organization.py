import unittest

import frappe
from frappe.tests.utils import FrappeTestCase

from dtmgp.setup.organization import BENUE_LGAS, PARENT_COMPANY, seed_lga_companies, seed_lga_profiles


class TestOrganizationSeedData(unittest.TestCase):
	def test_parent_company_name(self):
		self.assertEqual(PARENT_COMPANY, "Benue State Local Government Administration")

	def test_all_23_lgas_are_unique(self):
		self.assertEqual(len(BENUE_LGAS), 23)
		self.assertEqual(len({lga.name for lga in BENUE_LGAS}), 23)
		self.assertEqual(len({lga.abbr for lga in BENUE_LGAS}), 23)

	def test_company_names_are_explicit(self):
		for lga in BENUE_LGAS:
			self.assertTrue(lga.company_name.endswith(" Local Government Area"))


class TestOrganizationSeedIntegration(FrappeTestCase):
	def test_seeded_company_tree_is_complete_and_idempotent(self):
		result = seed_lga_companies()
		self.assertEqual(result["created"], [])
		self.assertEqual(result["updated"], [])
		self.assertEqual(frappe.db.get_value("Company", PARENT_COMPANY, "is_group"), 1)

		children = frappe.get_all(
			"Company",
			filters={"parent_company": PARENT_COMPANY, "is_group": 0},
			pluck="name",
		)
		expected = {lga.company_name.casefold() for lga in BENUE_LGAS}
		self.assertEqual(len(children), 23)
		self.assertEqual({name.casefold() for name in children}, expected)

	def test_lga_profiles_are_complete_and_idempotent(self):
		result = seed_lga_profiles()
		self.assertEqual(result["created"], [])
		profiles = frappe.get_all("LGA Profile", fields=["name", "lga_name", "lga_code", "company"])
		self.assertEqual(len(profiles), 23)
		self.assertEqual({profile.lga_code for profile in profiles}, {lga.abbr for lga in BENUE_LGAS})
		self.assertEqual({profile.company for profile in profiles}, {lga.company_name for lga in BENUE_LGAS})

	def test_lga_profile_registry_values_cannot_be_mixed(self):
		ado = next(lga for lga in BENUE_LGAS if lga.name == "Ado")
		agatu = next(lga for lga in BENUE_LGAS if lga.name == "Agatu")
		profile = frappe.get_doc(
			{
				"doctype": "LGA Profile",
				"lga_name": ado.name,
				"lga_code": agatu.abbr,
				"company": ado.company_name,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			profile.insert()

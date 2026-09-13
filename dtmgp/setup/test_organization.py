import unittest

from dtmgp.setup.organization import BENUE_LGAS, PARENT_COMPANY


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

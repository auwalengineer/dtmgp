from dtmgp.setup.organization import seed_lga_companies, seed_lga_profiles
from dtmgp.setup.security import seed_security_setup


def after_install():
	seed_lga_companies()
	seed_security_setup()
	seed_lga_profiles()

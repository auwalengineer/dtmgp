from dtmgp.setup.organization import seed_lga_companies


def after_install():
	seed_lga_companies()

### dtmgp

Local Government Digital Transformation, Management and Governance Platform

### Foundation status

The app is installed on a Frappe v15 bench with ERPNext and HRMS. Current verified versions are:

- Frappe 15.120.1
- ERPNext 15.121.2
- HRMS 15.64.0
- Node.js 18.20.8
- MariaDB 11.8.6

The current foundation includes Benue State branding for Desk, the website login, and the loading splash. It does not yet include Stage 1 frontend work or business DocTypes.

The Vue 3 application shell is maintained in `lg-dtmgp-web`. It includes responsive state navigation, an operational overview, module routes, and environment-specific development, staging, and production configuration.

Stage 0 governance documentation is indexed in [`docs/README.md`](docs/README.md), covering state offices and workflows, the role-permission matrix, data classification, naming and coding conventions, and operational safeguards.

On installation, `dtmgp.install.after_install` creates the group Company `Benue State Local Government Administration` and all 23 Benue LGA child Companies. The seed is idempotent and can be safely rerun with:

```bash
bench --site <site-name> execute dtmgp.setup.organization.seed_lga_companies
```

The following Stage 0 decisions remain project-owner gates before domain implementation:

- Validate the proposed state-office mapping, workflow approvers, role matrix, and data classifications with business owners.
- Approve the proposed operational targets, retention periods, alert thresholds, and release gates.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app dtmgp
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/dtmgp
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs ERPNext, HRMS, and this app on a clean version-15 site; verifies the 23-LGA seed; and runs backend tests.
- Vue CI: Runs type-checking, unit tests, the production build, hashed-asset integrity checks, and a production dependency audit.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit

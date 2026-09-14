# Naming and Coding Conventions

Status: Approved for implementation, 2026-09-14

## Product and repository names

| Item | Convention | Value or example |
| --- | --- | --- |
| Product display name | Uppercase acronym | `LG-DTMGP` |
| Frappe app and Python package | Lowercase snake case | `dtmgp` |
| Vue application directory and npm package | Lowercase kebab case | `lg-dtmgp-web` |
| State parent Company | Exact title | `Benue State Local Government Administration` |
| LGA Company | `{LGA Name} Local Government Area` | `Gboko Local Government Area` |
| Custom API namespace | Versioned kebab case | `/api/v1/lg-dtmgp/...` |
| Environment names | Lowercase fixed set | `development`, `staging`, `production` |

Do not rename ERPNext `Company` metadata or the `company` database field. The Vue application displays `LGA` as the user-facing label.

## Stable organization codes

Codes are immutable identifiers for integrations and naming series. They are not inferred from display names after creation.

| LGA | Code | LGA | Code |
| --- | --- | --- | --- |
| Ado | `ADO` | Agatu | `AGT` |
| Apa | `APA` | Buruku | `BRK` |
| Gboko | `GBK` | Guma | `GMA` |
| Gwer East | `GWE` | Gwer West | `GWW` |
| Katsina-Ala | `KAL` | Konshisha | `KNS` |
| Kwande | `KWD` | Logo | `LOG` |
| Makurdi | `MKD` | Obi | `OBI` |
| Ogbadibo | `OGD` | Ohimini | `OHM` |
| Oju | `OJU` | Okpokwu | `OKP` |
| Otukpo | `OTK` | Tarka | `TRK` |
| Ukum | `UKM` | Ushongo | `USH` |
| Vandeikya | `VDK` | | |

State code: `BNS`. Parent Company accounting abbreviation: `BSLGA`.

## Frappe model conventions

- Custom DocTypes use singular Title Case: `Council Resolution`, `Project Inspection`.
- Child DocTypes use the parent concept plus a singular child noun: `Council Resolution Action`.
- Field names use lowercase snake case: `reporting_period`, `company`, `due_date`.
- Link fields use the linked concept name without `_id`: `company`, `project`, `employee`.
- Boolean fields begin with `is_`, `has_`, or an imperative verb: `is_active`, `has_exception`, `requires_review`.
- Date fields end in `_date`; datetimes end in `_at`; counts end in `_count`; percentages end in `_percent`.
- Every LGA-scoped record has a mandatory `company` Link to `Company` and an index suitable for Company-filtered lists.
- Workflow state uses the standard `workflow_state` field. Domain status is added only when it expresses a separate lifecycle.
- Select values use stable English Title Case and are never repurposed after release.
- Custom fields on framework DocTypes use Frappe's `custom_` prefix.
- Attachments use meaningful field names such as `inspection_evidence`, not `file_1`.

## Document identifiers

User-facing identifiers follow `{TYPE}-{LGA_CODE}-{YEAR}-{SEQUENCE}`.

| Record | Type code | Example |
| --- | --- | --- |
| Council Meeting | `CM` | `CM-GBK-2026-00001` |
| Council Resolution | `RES` | `RES-GBK-2026-00001` |
| Statutory Return | `RET` | `RET-GBK-2026-00001` |
| Project | `PRJ` | `PRJ-GBK-2026-00001` |
| Project Inspection | `INS` | `INS-GBK-2026-00001` |
| Staff Verification | `SVR` | `SVR-GBK-2026-00001` |
| Petition or dispute | `PET` | `PET-GBK-2026-00001` |

- Sequences are five digits and unique within the complete series.
- Identifiers are immutable and not recycled after cancellation or deletion.
- Draft records receive their final identifier on first save unless security requires delayed numbering.
- External-system identifiers are stored in dedicated fields with source-system names; they never replace the platform identifier.

## Python conventions

- Follow Ruff formatting, imports, and lint rules configured in `pyproject.toml`.
- Use type hints for public service functions and non-obvious return values.
- Keep controllers focused on document lifecycle; place cross-document behavior in domain service modules.
- Use Frappe query and document APIs with parameterized filters. Do not construct SQL from user input.
- Do not use `ignore_permissions=True` in request code. Controlled installation, migration, and background processes must document why elevated access is necessary.
- Permission functions return explicit decisions and have denial-path tests.
- Use `frappe.throw` with translatable, non-sensitive messages for user-facing errors.
- Log identifiers and outcomes, not credentials or sensitive payloads.

## Vue and TypeScript conventions

- Use Vue 3 Composition API with `<script setup lang="ts">`.
- Components use PascalCase filenames; composables use `useName.ts`; Pinia stores use singular domain names.
- Routes and URL query keys use kebab case. TypeScript variables and functions use camel case.
- Domain API payloads are validated at boundaries with Zod and represented by explicit TypeScript types.
- TanStack Query owns server state; Pinia owns session and durable client state; local component state remains local.
- Route guards improve navigation but never substitute for backend permission checks.
- Shared controls expose labels, keyboard behavior, loading, empty, error, disabled, and validation states.
- Do not store API secrets or long-lived credentials in browser storage or `VITE_` variables.

## API conventions

- Public application endpoints begin with `/api/v1/lg-dtmgp/`.
- Resource paths use plural kebab-case nouns: `/council-resolutions`.
- Commands use explicit action subpaths when they are not CRUD: `/council-resolutions/{id}/approve`.
- JSON fields use snake case to match Frappe fields.
- Dates use `YYYY-MM-DD`; datetimes use ISO 8601 with timezone; money uses decimal strings plus currency.
- Lists use `page`, `page_size`, allowlisted `sort`, and allowlisted filters. Maximum page size is enforced server-side.
- Errors use stable machine codes and safe user messages; validation errors identify fields without leaking restricted values.
- Breaking contracts require a new API version. Additive fields remain backward compatible.

## Git, commits, and releases

- Permanent branches are `main` for production and `develop` for integrated development.
- Working branches use `feature/<ticket>-<summary>`, `fix/<ticket>-<summary>`, or `chore/<ticket>-<summary>`.
- Commits use Conventional Commit prefixes: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.
- Releases use semantic versioning: `MAJOR.MINOR.PATCH`.
- Database migrations and fixtures ship with the release that consumes them and must support clean installation plus upgrade.
- Secrets, production personal data, build output, local environment overrides, and editor files are not committed.

## Review checklist

- Names use approved domain language and do not duplicate ERPNext or HRMS concepts.
- Every LGA-scoped model, query, report, API, and test uses Company scope.
- Stable codes and identifiers are not based on mutable labels.
- New states and roles are reflected in workflow and permission documentation.
- Public APIs, migrations, fixtures, tests, and documentation change together.

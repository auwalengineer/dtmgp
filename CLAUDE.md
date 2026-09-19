# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

LG-DTMGP: Local Government Digital Transformation, Management and Governance Platform for Benue State. A Frappe v15 app (`dtmgp`) installed alongside ERPNext and HRMS on a single site, paired with a separate Vue 3 frontend (`lg-dtmgp-web`). Governance baseline docs live in `docs/` (start at `docs/README.md`); five accepted ADRs live in `docs/architecture/`.

This repo is two projects in one working tree:
- `dtmgp/` — the Frappe app (Python backend, DocTypes, fixtures, patches).
- `lg-dtmgp-web/` — the Vue 3 + TypeScript frontend (independent npm project, own CI job).

## Commands

### Backend (`dtmgp/`, run from a bench, e.g. `~/frappe-bench`)

```bash
bench --site <site-name> install-app dtmgp
bench --site <site-name> migrate                       # must be repeatable/idempotent
bench --site <site-name> set-config allow_tests true
bench --site <site-name> run-tests --app dtmgp
bench --site <site-name> run-tests --app dtmgp --module dtmgp.permissions.test_finance_scope
bench --site <site-name> execute dtmgp.setup.organization.seed_lga_companies   # idempotent, safe to rerun
```

Backend tests live next to the code they cover as `test_*.py` (e.g. `dtmgp/permissions/test_finance_scope.py`, `dtmgp/setup/test_organization.py`) — there is no separate `tests/` tree.

Lint/format (also run by pre-commit and CI):

```bash
pre-commit install        # once, from apps/dtmgp
pre-commit run --all-files
ruff check .
ruff format .
```

### Frontend (`lg-dtmgp-web/`)

```bash
cd lg-dtmgp-web
npm ci
npm run dev              # vite dev server
npm run typecheck        # vue-tsc -b --noEmit
npm test                 # vitest run
npm test -- session.test.ts   # single test file
npm run build             # generates version metadata, typechecks, vite build
npm run check:assets      # verifies every asset index.html references exists and is hashed
npx playwright install --with-deps chromium
npm run test:e2e          # Playwright browser + accessibility (axe) tests
```

## Architecture

### Single-site, Company-based LGA isolation (ADR-001)

There is one Frappe site. `Benue State Local Government Administration` is a group Company; each of the 23 LGAs (`dtmgp/setup/organization.py`, `BENUE_LGAS`) is a child Company, seeded idempotently by `dtmgp.install.after_install` → `seed_lga_companies`/`seed_lga_profiles`/`seed_security_setup`. Every LGA-scoped custom DocType carries a mandatory `company` link (surfaced as "LGA" in the Vue UI — never rename the underlying field). Isolation is enforced in layers, not by the database:

- `permission_query_conditions` / `has_permission` hooks in `hooks.py`, implemented in `dtmgp/permissions/*.py` (`user.py`, `audit_event.py`, `finance.py`).
- `dtmgp/permissions/scope.py` is the source of truth for role sets (`STATE_ROLES`, `FINANCE_VIEW_ROLES`, etc.) and scope helpers: `get_allowed_companies()`, `get_requested_companies(company)` (intersects a requested LGA against what the caller is actually allowed — always use this rather than trusting a client-supplied company), `is_state_user()`, `require_finance_access()/require_hr_access()/require_user_admin()`.
- State-level roles get statewide access; everyone else is scoped via `User Permission` on `Company`.
- Because Company permissions are an organizational boundary rather than hard multi-tenancy, every new list view, direct read/write, report, export, and file path needs an explicit cross-LGA denial test (see `dtmgp/permissions/test_*.py` for the pattern).

### Server-authoritative authorization (ADR-003)

The Vue app never decides access — it only reflects what the server returns. Frontend route guards and the dynamic menu (`dtmgp/navigation.py::get_navigation`) are usability affordances, not security boundaries. Every whitelisted API re-derives the caller's roles and allowed Companies server-side. Same-origin Frappe session cookies are used for auth; no API secrets or long-lived credentials belong in browser storage or `VITE_` env vars.

### Domain document pattern (finance/revenue/procurement)

`dtmgp/finance.py` defines `ScopedFinanceDocument`, the base controller class for LGA-scoped DocTypes (`DTMGP Revenue Head`, `DTMGP Revenue Assessment`, `DTMGP Revenue Receipt`, `DTMGP Procurement Plan`, `DTMGP Procurement Case`, `DTMGP Payment Request`, `DTMGP Approval Limit`, `DTMGP Audit Query`). `validate()` always calls `validate_lga(self.company)` then enforces `allowed_roles` on new/reassigned records; subclasses override `validate_record()` for field-level rules. Follow this pattern for any new scoped DocType rather than duplicating the company/role checks inline.

Whitelisted API modules under `dtmgp/api/v1/` (`finance.py`, `people.py`, `administration.py`, `users.py`, `navigation.py`, `overview.py`, `context.py`) follow a consistent shape: call a `require_*_access()` guard first, resolve companies via `get_requested_companies`, use explicit field allowlists (e.g. `RECORD_FIELDS`/`EDITABLE_FIELDS` in `finance.py`) rather than exposing full DocTypes, and drive status changes through an explicit `TRANSITIONS` map keyed by `(from_status, to_status) -> required_roles` (an amount-based `DTMGP Approval Limit` check applies when `required_roles` is `None`).

### Append-only audit trail

`dtmgp/audit.py` provides `record_event`/`record_denial`, wired into `doc_events` in `hooks.py` for user/permission changes and finance document lifecycle events. `record_denial` commits after rollback via `frappe.db.after_rollback.add(...)` so a denied/failed action is still recorded even though the triggering transaction rolls back. Sensitive keys (`SENSITIVE_KEYS` in `audit.py`) are redacted from metadata before storage — extend that set rather than logging raw payloads when adding new event metadata.

### Role-driven navigation

`dtmgp/navigation.py` defines the entire app's menu tree as a static tuple (`NAVIGATION`) of modules → sections → items, each gated by a role set. `get_navigation(user)` filters this tree by the caller's roles and returns only the module/section shell (routes), not data. Many listed routes are placeholders for domains not yet built (see `docs/implementation-status.md` for what's actually implemented vs. pending) — don't assume a nav entry implies a working feature.

### Frontend structure (`lg-dtmgp-web/`)

Vue 3 + `<script setup lang="ts">`, Vue Router, Pinia (session/durable client state), TanStack Query (server state), Zod (boundary validation of API responses and runtime config). `src/config/environment.ts` loads build-time `VITE_*` env vars and optionally overlays a runtime `runtime-config.json` fetched at startup (ADR-004: immutable, content-hashed build promoted across dev/staging/prod without rebuilding; runtime config carries only non-secret, deploy-time values). `src/services/api.ts` is the shared API client; `src/stores/session.ts` owns auth/session state. Route guards in `src/router/` are UX only, per ADR-003.

### Naming and API conventions

Full detail in `docs/naming-and-coding-conventions.md`; key points:
- Public API namespace: `/api/v1/lg-dtmgp/...`, plural kebab-case resources, action subpaths for non-CRUD commands.
- Custom DocTypes: singular Title Case; fields: snake_case; booleans: `is_`/`has_`/imperative prefix; dates end `_date`, datetimes end `_at`.
- Document identifiers follow `{TYPE}-{LGA_CODE}-{YEAR}-{SEQUENCE}` (5-digit sequence, immutable, never recycled).
- Never use `ignore_permissions=True` in request-path code; if elevated access is unavoidable (install/migration/background), document why at the call site.
- Branches: `main` (production), `develop` (integration), `feature/<ticket>-<summary>`, `fix/...`, `chore/...`. Conventional Commit prefixes (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`).

## CI

- `.github/workflows/ci.yml`: secret scan (gitleaks); backend job installs ERPNext+HRMS+dtmgp on a fresh site, runs `bench run-tests --app dtmgp`, and verifies `bench migrate` is repeatable; frontend job runs typecheck, vitest, Playwright (browser + accessibility), production build, `check:assets`, and `npm audit --omit=dev`.
- `.github/workflows/linter.yml`: pre-commit (ruff, ruff-format, prettier, eslint) plus Frappe Semgrep rules and `pip-audit` on every PR.

When adding a new scoped DocType or API, expect to touch: the controller in `dtmgp/finance.py`-style module (or new equivalent), `hooks.py` (`permission_query_conditions`/`has_permission`/`doc_events`), `dtmgp/permissions/scope.py` role sets, an `api/v1/*.py` module, `dtmgp/navigation.py` if it needs a menu entry, and a cross-LGA denial test.

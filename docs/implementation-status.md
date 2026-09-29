# Implementation Status and Pending Work

Last reconciled: 2026-09-21
Branch: `develop`  
Latest reviewed milestone: `f7b1489` plus HR extensions, the full Administration & Governance module (see GOV-001), the Traditional Affairs / Chieftaincy domain (see TRAD-001), the Projects, Assets & Field Monitoring domain (see PRJ-001), the Budget/Allocations/Accounting/Contracts completion of Finance, Revenue & Procurement (see FIN-002), and the System Administration module (see SYS-001)

## Status definitions

- **Complete**: implemented, tested, committed, and reproducible in the development environment.
- **Partial**: useful behavior exists, but the approved acceptance criteria are not fully satisfied.
- **Pending**: implementation has not started or remains a presentation-only workspace.
- **External**: requires named business, legal, security, or operations evidence and cannot be completed by code alone.

## Completed engineering milestones

| Area | Status | Evidence |
| --- | --- | --- |
| Vue 3 application shell and environments | Complete | Responsive shell, development/staging/production configuration, Vite build and asset checks |
| Organizational model | Complete | Parent Company plus 23 LGA child Companies, idempotent install seed and integration tests |
| Architecture and governance baseline | Complete | Five ADRs, role matrix, classification matrix, naming conventions, operations policy and Stage 0 approval record |
| Authentication | Complete | Same-origin Frappe login/logout, session restore, CSRF handling and authenticated route guards |
| Scoped user administration | Complete | Vue and Frappe user management, seeded roles, LGA field, Company User Permission synchronization and cross-LGA denial tests |
| Permission-driven navigation | Complete | Backend-filtered domain/submenu tree, role and LGA-assignment checks, direct-route guards and global user menu |
| Administration dashboard | Complete | Scoped account totals, role distribution, recent users and user create/edit/enable/disable APIs |
| Overview foundation | Complete | Server-derived account and workforce metrics filtered by active authorized LGA |
| HR staff directory foundation | Complete | ERPNext Employee reuse, search, pagination, filters, create/edit, verification status, leave list and department headcounts |
| HR metadata deployment | Complete | Idempotent custom fields/permissions for clean install and existing-site migration |
| LGA registry | Complete | One-to-one LGA Profile records, immutable official codes, Company validation, clean-site seed and duplicate-link tests |
| Security audit foundation | Complete | Append-only audit events for user/permission changes and authorization denials with sensitive-value redaction |
| Runtime release detection | Complete | Build metadata publication, periodic version polling and non-blocking refresh notification |
| CI baseline | Complete | Clean-site install, repeatable migration, backend/unit/browser/accessibility checks, secret scan, Vue build, asset verification and production dependency audit |
| Finance, revenue and procurement foundation | Complete | Eight LGA-scoped governance DocTypes, ERPNext accounting/purchasing integration, controlled transitions, amount-based approvals, audit events, APIs and Vue cockpit |
| Executive analytics foundation | Complete | Permission-filtered KPI registry, reporting periods, freshness/completeness metadata, LGA dashboard, guarded 23-LGA scorecards, trends, maps, alerts, audited exports and responsive Vue workspace |
| FIN-002 Budget, Allocations, Accounting & Contracts | Complete | Completes the four Finance tabs that were previously placeholder-only. Budget reuses ERPNext's native submittable `Budget`/`Budget Account` doctypes (preparation, submission, and cancel-then-amend revisions via `amended_from`) rather than a new dtmgp doctype; Budget Performance/Variance Analysis compare submitted budget lines against `GL Entry` actuals. Allocations (statutory federal/state transfers, a genuine gap with no ERPNext equivalent) is a new LGA-scoped `DTMGP Allocation` + child table `DTMGP Allocation Distribution`. Accounting exposes read views over ERPNext's `Account`/`Journal Entry`/`GL Entry` (chart of accounts, journal entries, general ledger, trial balance); Accounts Receivable/Payable and Bank Reconciliation remain honest placeholders — see the FIN-001 row below. Contracts (post-award contract register, a genuine gap distinct from Procurement Case) is a new `DTMGP Contract` + child table `DTMGP Contract Milestone`, plus `DTMGP Contract Variation` wired through the existing amount-based `_validate_approval_limit` gate using the `DTMGP Approval Limit.transaction_type` "Contract Variation" option that was already in the schema but unused. Procurement's "Goods Received" now reads ERPNext's native `Purchase Receipt`. Financial Reports' Budget Performance and Cash Flow reports are now real (Cash Flow derives from submitted Revenue Receipts vs. Paid Payment Requests). All behind the existing `require_finance_access()` guard and `FINANCE_VIEW_ROLES`/`FINANCE_MANAGE_ROLES`, scoped API additions in `dtmgp/api/v1/finance.py`, audit-event wiring, cross-LGA denial and role-gated-transition tests added to `dtmgp/permissions/test_finance_scope.py`, and new Custom DocPerm grants (including a read-only grant on `GL Entry`) seeded via `dtmgp.patches.v1_0.add_finance_module_extensions`. |
| GOV-001 Administration & Governance | Complete | `DTMGP Correspondence` (Incoming/Outgoing/Internal Memo, Draft→Registered→Dispatched→Closed), `DTMGP Meeting` (+ agenda/attendance child tables, minutes), `DTMGP Resolution` and `DTMGP Resolution Action` (assigned-action tracking), `DTMGP Statutory Return` and `DTMGP Compliance Submission` (both backed by a state-managed, not-LGA-scoped reference catalogue — `DTMGP Statutory Return Type` / `DTMGP Compliance Requirement` — seeded with a starter set pending full business confirmation), and a cross-cutting Approvals inbox (`get_approvals_inbox`) with `DTMGP Approval Delegation` letting a delegate act for a role within a date range. Departments & Units reuses ERPNext `Department` rather than a new DocType. Scoped API (`dtmgp/api/v1/governance.py`), audit-event wiring, cross-LGA denial tests (`dtmgp/permissions/test_governance_scope.py`, `dtmgp/permissions/test_governance_isolation.py`) and a Vue workspace at `/governance` covering all eight nav sections |
| FND-003 Roles and Role Profiles | Complete | All approved roles are seeded; a one-role Role Profile per platform role is seeded idempotently and reproducible-assignment is tested (`dtmgp/setup/test_security.py`) |
| HR-002 Staff verification | Complete | `DTMGP Staff Verification Exercise`/`Record` model with reviewer-cannot-equal-preparer enforcement, exception reasons, an evidence attachment field and audit-event wiring (`dtmgp/hr.py`, `dtmgp/api/v1/hr.py`, `dtmgp/permissions/test_hr_extensions.py`); biometric capture is a manual confirmation flag pending device-integration scope |
| HR-003 Establishment control | Complete | ERPNext `Staffing Plan`/`Staffing Plan Detail` (not a new dtmgp DocType) extended with platform-role Custom DocPerm; live filled/vacant/overstaffed computed from `Staffing Plan Detail`'s own `current_count`/`number_of_positions`, scoped CRUD, tests |
| HR-004 Postings, transfers and promotions | Complete | HRMS `Employee Transfer` (posting and cross-LGA transfer in one submittable doctype; `company`/`new_company` both exempted from Frappe's automatic per-field Company filtering via Property Setters so the destination LGA can act on an inbound transfer) and `Employee Promotion`, both extended with Custom DocPerm and a no-self-submit guard in the API layer; submission updates the Employee record via each doctype's native controller |
| HR-005 Retirement and exit | Complete | HRMS `Employee Separation` (its native Project/Task-based boarding-activity checklist, extended with Task/Project Custom DocPerm and Task scoped through its Project's company) gates completion; marks the Employee `Left` with a relieving date once every activity task is completed; plus a retirement forecast report over Employee's existing `date_of_retirement` field |
| HR-006 Attendance and leave decisions | Complete | Scoped attendance summary/list over ERPNext `Attendance`; leave balance, calendar and approve/reject actions over `Leave Application` with a no-self-approval guard |
| HR-007 Payroll and staff-audit visibility | Complete | Count-only Payroll overview (Treasurer/state roles) and a Staff Audit exceptions report (unverified/duplicate/missing-grade, Internal Auditor/state roles); payroll amounts, bank and tax detail remain deferred as Restricted data pending sign-off |
| TRAD-001 Traditional Affairs / Chieftaincy | Complete | Seven new LGA-scoped DocTypes (`DTMGP Traditional Institution`, `Traditional Ruler`, `Ruling House`, `Traditional Appointment`, `Succession Case`, `Chieftaincy Petition`, `Traditional Allowance`) modeling institution/ruler/ruling-house as distinct entities, a Nominated→...→Installed appointment/recognition chain, a Filed→...→Closed petition/dispute chain, and Draft→Approved→Paid allowances, all behind `require_traditional_access()`, scoped API (`dtmgp/api/v1/traditional.py`), audit-event wiring and cross-LGA denial tests (`dtmgp/permissions/test_traditional_scope.py`, `test_traditional_isolation.py`); a full Vue workspace at `/traditional-affairs` replaces the prior all-placeholder frontend. **This domain was previously listed as deferred pending the external sign-off conditions below (see "External production conditions"); the project owner explicitly directed engineering to proceed ahead of that sign-off. No business/legal/records sign-off for chieftaincy data has actually been obtained — this is a build-ahead-of-process decision, not a completed governance gate.** |
| PRJ-001 Projects, Assets & Field Monitoring | Complete | Built on native ERPNext/HRMS doctypes rather than a parallel data model: `Project`/`Task` (already scoped via the existing HR-005 `dtmgp/permissions/hr.py` hooks) plus two new Custom Fields (`dtmgp_location`, `dtmgp_funding_source`) for the register/planning/progress views; `Asset`/`Asset Category`/`Location`/`Asset Movement`/`Asset Maintenance` for the asset register/locations/assignments/transfers/maintenance views; `Vehicle`/`Vehicle Log` (extended with a new `company` Custom Field) for fleet management; `Supplier` (shared statewide, same treatment PRC-001 already gives it) for the contractor register/blacklist, with contractor performance derived read-only from `DTMGP Procurement Case`. Two new LGA-scoped DocTypes fill the only genuine gaps: `DTMGP Project Inspection` (field monitoring, GPS coordinates and photo evidence) and `DTMGP Asset Verification`. All behind `require_projects_access()`, scoped API (`dtmgp/api/v1/projects.py`), audit-event wiring and cross-LGA denial tests (`dtmgp/permissions/test_projects_scope.py`, `test_projects_isolation.py`); a full Vue workspace at `/projects` replaces the prior all-placeholder frontend. A handful of items remain honest placeholders where no underlying capability exists yet — see the PRJ-001 row in "Partially complete backlog". |
| Cross-domain completion controls | Complete | Restricted HR personnel files/next-of-kin/private documents and migration templates; Finance control policies, bank signatories, native bank reconciliation data, voucher formats and operational AR/AP views; approved revenue heads, gateway/reconciliation/enforcement metadata; procurement threshold/committee/evidence/public-notice and milestone certification/payment links; approval-gated governance catalogues; project proposals, project financials/variations, asset disposals, private contractor documents and embedded maps; configurable analytics KPI weights/thresholds, staging acceptance evidence and secured external-integration registration. Authority-owned values remain Draft until evidence is supplied. |
| SYS-001 System Administration | Complete | Of the nav's 8 System Administration sections, User Management (Users, plus new Roles/Role Profiles/LGA Access/User Sessions reads), Organization Setup (LGAs via `LGA Profile`, Departments & Units reusing GOV-001's `list_departments`/`save_department`, Designations, Fiscal Years — the last write-restricted to state admins since it's global and drives every LGA's ledger) and most of Reference Data (Document Numbering, a live read of each DTMGP doctype's actual `autoname`, and Locations) and Security & Audit (Audit Logs over the already-scoped `DTMGP Audit Event`; Login History over native `Activity Log`; Permission Changes/Security Events as preset filters over the same two) are real, mostly by exposing existing-but-unreachable data (`DTMGP Approval Limit`, consumed by finance transitions since FIN-002 but never given a CRUD surface until now, added to `finance.py`'s `RECORD_FIELDS`; `DTMGP Approval Delegation` reused directly from GOV-001) or native doctypes (`Designation`, `Fiscal Year`, `Location`, raw `tabSessions`, `Activity Log`) behind new Custom DocPerm grants and `dtmgp.permissions.scope.require_state_admin()`/`require_system_manager()` guards. A full Vue workspace at `/workspace/system/...` (`dtmgp/permissions/test_administration.py` covers the new cross-LGA and role-gate denials) replaces the prior all-placeholder frontend. System Operations links out to native Frappe Desk screens (Background Jobs, Scheduled Tasks, Error Log, Application Settings) rather than rebuilding them, plus one live scheduler-status check. Workflows/Workflow States/Escalation Rules, all of Communication Setup, Data Export History and the remaining Reference Data items stay honest, documented placeholders — see the SYS-001 row in "Partially complete backlog". |

## Partially complete backlog

| Backlog | Current state | Remaining acceptance work |
| --- | --- | --- |
| FND-005 Isolation test harness | User, navigation, Employee and the extended native HR doctypes (Staffing Plan, Employee Transfer/Promotion/Separation, Project, Task) have multi-LGA denial tests; direct document read/write, submit/cancel, raw report/list query, export-permission, private-attachment and dual-LGA-visibility (Employee Transfer's `company`/`new_company`) denial are proven against the `has_permission`/`permission_query_conditions` hooks directly (`dtmgp/permissions/test_isolation.py`, `dtmgp/permissions/test_hr_extensions.py`) | Extend the same direct-hook coverage to procurement and audit-query record types as their dedicated UI is built |
| FND-006 Audit event foundation | User/permission changes and authorization denials are recorded append-only | Add workflow-transition and export events as those capabilities are implemented |
| FND-008 Session lifecycle | Login, logout, CSRF and unauthorized guest behavior work | Add automated expired-session, disabled-user and concurrent-session journeys |
| FND-010 Delivery gates | Browser, critical axe, secret-scan and repeatable-migration gates are configured in CI | Add immutable artifact publishing and required-branch protection evidence |
| UI-001 Responsive shell | Desktop/mobile shell and principal pages are responsive | Perform browser viewport and keyboard acceptance checks for state, LGA and self-service users |
| UI-003 Data tables and filters | Employee list has server pagination/search/filtering | Build shared component, allowlisted sorting and URL-preserved filter state |
| UI-005 Accessibility baseline | Critical axe checks run on desktop/mobile authorization journeys | Complete keyboard journeys and broaden WCAG checks across principal workflows |
| UI-006 Low-bandwidth behavior | Hashed build is small and lists paginate | Define budget, add measurements, upload progress/retry and non-blocking skeleton patterns |
| HR-001 Scoped staff directory | Core approved Employee fields and LGA scope are live | Approve production field allowlist, add restricted-field denial tests and staging acceptance |
| DSH-001 LGA operational dashboard | Complete: authorized cross-domain metrics include source, period, freshness, completeness and scoped drill-down | Complete controlled staging acceptance with representative LGA roles |
| DSH-002 Statewide dashboard | Approved state roles can compare all 23 LGAs; incomplete/stale LGAs are explicitly unranked | Approve KPI weights and thresholds; complete state-executive staging acceptance |
| FIN-001 Finance and treasury | Payment requests, budget preparation/submission/revision and performance, chart of accounts/journal entries/general ledger/trial balance read views, scoped dashboard and ERPNext ledger permissions are live (see FIN-002 above) | Configure chart-of-accounts policy, bank signatories and Bank Account setup for reconciliation, voucher print formats and staging acceptance; a dedicated Accounts Receivable/Payable ledger remains a placeholder since DTMGP doesn't use Sales/Purchase Invoice party ledgers |
| REV-001 Revenue administration | Revenue heads, assessments, submitted receipts, reconciliation totals and Revenue Officer role are live | Approve lawful revenue-head catalogue, rates, payment gateway and enforcement process |
| PRC-001 Procurement | Plans and cases link ERPNext material requests, RFQs, suppliers, purchase orders and receipts; Goods Received reads ERPNext Purchase Receipt; a post-award Contract register with milestones and variations is live (see FIN-002 above) | Configure BSPPC thresholds, committees, bid evidence and public notices; contract milestone certification/payment-linking and variation intake are recorded directly in Frappe Desk pending a dedicated UI action |
| PRJ-001 Projects, Assets & Field Monitoring | Project/task register, proposals, planning, finance/variation links, inspections, IndexedDB offline inspection/photo queue with reconnect synchronization, physical progress, disposal requests with mandatory Journal Entry linkage, private contractor documents, embedded maps, asset register/locations/assignments/transfers/maintenance/verification, native Vehicle Log service-detail entry and fleet management are live | Production disposal-account mappings and contractor-document retention periods still require authority approval |
| SYS-001 System Administration | User Management, Organization Setup, Document Numbering/Locations, and Audit Logs/Login History/Permission Changes/Security Events are live (see SYS-001 above) | Workflow Setup's Workflows/Workflow States/Escalation Rules don't apply — this platform uses explicit per-domain `TRANSITIONS` maps, not Frappe's generic Workflow engine; Communication Setup (Notifications, Email Templates, SMS Templates, Notification Preferences) is blocked on the same pending Notifications pipeline as the P1 backlog item below; Security & Audit's Data Export History is blocked on the same pending "Authorized exports" P1 item below; Reference Data's Status Definitions, Categories and Other Reference Data have no concrete backing entity yet |

## Pending engineering work

### P0 foundation

1. **FND-005 Expanded isolation harness**: extend the proven direct document/submit-cancel/report/export/attachment denial coverage to HR, procurement and audit-query record types as each capability becomes available.
2. **API contract foundation**: standardize envelopes and errors, document `/api/v1` methods, and add an OpenAPI reference plus Bruno/Postman collection.
3. **FND-008 Session lifecycle tests**: cover expired sessions, disabled users and concurrent-session behavior.

### P1 shared frontend

1. **UI-002 Shared form controls**: accessible text, select, date, number, checkbox, file, validation, disabled, loading and error components.
2. **UI-004 Workflow components**: timeline, approval panel, rejection reason, confirmation and pending-action components.
3. **UI-005 Accessibility completion**: broaden automated WCAG checks and complete keyboard journeys.
4. Expand Playwright coverage from authorization denial to login/logout, LGA switching, user administration and HR workflows.
5. Implement global search, notifications, calendar, tasks, approvals, recently viewed, saved items, help and profile workflows; these are currently registered navigation workspaces only.

### P1 first-release domains

1. ~~**Governance**~~ — complete, see GOV-001 above. The statutory-return and compliance-requirement catalogues ship with a starter set only; the authoritative catalogues are an external production condition (same status as Finance's revenue-head catalogue).
2. **HR restricted-data records**: digital personnel files, next-of-kin and staff-document storage remain pending a named HR/records-legal field-classification and retention sign-off (external production condition 6) — the operational HR workflows (verification, establishment, postings/transfers, promotions, attendance, leave decisions, exit/retirement, reports) are complete.
3. **Dashboards**: engineering foundation is complete; approve KPI weights/thresholds and complete representative LGA/state staging acceptance.
4. **Notifications**: deduplicated reminders and escalations for overdue returns, actions and inspections.
5. **Authorized exports**: purpose capture, scoped fields, classification markings and export audit records.

Projects and assets (project register, milestones, inspections, evidence, exception review and scoped reports) is no longer pending — see PRJ-001 above.

### Deferred domains

Full payroll processing (bank, tax and deduction detail), external integrations and offline/PWA remain deferred until their approved entry conditions are met; a count-only Payroll overview is live (see HR-007). Finance/revenue and procurement now have operational foundations; functions beyond the records and controls listed above remain pending until their business configuration is approved. Chieftaincy/Traditional Affairs is no longer deferred — see TRAD-001; that decision was made without the sign-off this section otherwise requires (see the note on TRAD-001).

## External production conditions

1. Name and obtain sign-off from local-government and HR business owners.
2. Confirm workflow approvers, alternates, deadlines and delegation duration.
3. Obtain records/legal approval for retention, legal hold, archival and disposal.
4. Obtain information-security approval for classification, emergency access, audit and incident handling.
5. Demonstrate backup isolation, key recovery, restoration timing, monitoring routes and runbooks.
6. Approve production HR field classification and migration templates.
7. Complete controlled staging acceptance with representative LGA and state users.

## Recommended next milestone

Complete the remaining foundation in this order:

1. Standardized API contracts and reference documentation.
2. Isolation test harness coverage for the remaining domains (HR, procurement, audit query).
3. Session lifecycle browser tests.
4. Immutable artifact publishing and branch-protection evidence.

Governance, Traditional Affairs/Chieftaincy, Projects/Assets and the analytics foundation are now implemented (see GOV-001, TRAD-001, PRJ-001, DSH-001 and DSH-002) — remaining first-release scope is HR restricted-data records, notifications, cross-domain authorized exports, and controlled staging acceptance (see "Pending engineering work" below).

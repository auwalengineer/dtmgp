# Implementation Status and Pending Work

Last reconciled: 2026-09-16  
Branch: `develop`  
Latest reviewed milestone: `9c4755f`

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
| CI baseline | Complete | Clean-site install, backend tests, Vue type-check/tests/build, asset verification and production dependency audit |

## Partially complete backlog

| Backlog | Current state | Remaining acceptance work |
| --- | --- | --- |
| FND-003 Roles and Role Profiles | All approved roles are seeded | Create approved Role Profiles and test reproducible profile assignment |
| FND-005 Isolation test harness | User, navigation and Employee APIs have multi-LGA denial tests | Add direct document, submit/cancel, report, export, attachment and private-file denial coverage |
| FND-008 Session lifecycle | Login, logout, CSRF and unauthorized guest behavior work | Add automated expired-session, disabled-user and concurrent-session journeys |
| FND-010 Delivery gates | Clean install and core backend/frontend checks run in CI | Add browser tests, secret scanning, migration test, immutable artifact and required-branch protection evidence |
| UI-001 Responsive shell | Desktop/mobile shell and principal pages are responsive | Perform browser viewport and keyboard acceptance checks for state, LGA and self-service users |
| UI-003 Data tables and filters | Employee list has server pagination/search/filtering | Build shared component, allowlisted sorting and URL-preserved filter state |
| UI-006 Low-bandwidth behavior | Hashed build is small and lists paginate | Define budget, add measurements, upload progress/retry and non-blocking skeleton patterns |
| HR-001 Scoped staff directory | Core approved Employee fields and LGA scope are live | Approve production field allowlist, add restricted-field denial tests and staging acceptance |
| HR-002 Staff verification | Verification status and authorized verify action exist | Implement exercise/record model, reviewer separation, evidence, exceptions, reasons, audit trail and Restricted-file controls |
| DSH-001 LGA operational dashboard | Scoped workforce/account metrics exist | Add metric source, reporting period, freshness, drill-down and approved governance/project indicators |

## Pending engineering work

### P0 foundation

1. **FND-002 LGA Profile and stable code**: create the one-to-one LGA Profile model, immutable code validation and duplicate-link tests.
2. **FND-006 Audit event foundation**: record privileged access, permission changes, workflow transitions, exports and authorization denials without sensitive payloads.
3. **FND-009 Runtime version detection**: publish version/commit/build time and show a non-blocking refresh notification when a newer deployment is available.
4. **API contract foundation**: standardize envelopes and errors, document `/api/v1` methods, and add an OpenAPI reference plus Bruno/Postman collection.

### P1 shared frontend

1. **UI-002 Shared form controls**: accessible text, select, date, number, checkbox, file, validation, disabled, loading and error components.
2. **UI-004 Workflow components**: timeline, approval panel, rejection reason, confirmation and pending-action components.
3. **UI-005 Accessibility baseline**: automated WCAG checks and complete keyboard journeys.
4. Add Playwright coverage for login/logout, LGA switching, user administration, navigation denial and HR workflows.
5. Implement global search, notifications, calendar, tasks, approvals, recently viewed, saved items, help and profile workflows; these are currently registered navigation workspaces only.

### P1 first-release domains

1. **Governance**: Government Correspondence, meetings/agendas/attendance/minutes, resolutions/actions, statutory returns, compliance and approval workflows.
2. **Projects and assets**: project register, milestones, inspections, evidence, exception review and scoped reports.
3. **HR completion**: verification exercises, personnel files, establishment positions, posting/transfers, promotions, attendance, retirement/exit and approved reports.
4. **Dashboards**: complete LGA dashboard and build the approved statewide comparison dashboard without ranking stale/incomplete periods.
5. **Notifications**: deduplicated reminders and escalations for overdue returns, actions and inspections.
6. **Authorized exports**: purpose capture, scoped fields, classification markings and export audit records.

### Deferred domains

Finance/revenue, procurement, payroll, chieftaincy, external integrations and offline/PWA remain deferred until their approved entry conditions are met. Their navigation entries are registered placeholders, not completed business modules.

## External production conditions

1. Name and obtain sign-off from local-government and HR business owners.
2. Confirm workflow approvers, alternates, deadlines and delegation duration.
3. Obtain records/legal approval for retention, legal hold, archival and disposal.
4. Obtain information-security approval for classification, emergency access, audit and incident handling.
5. Demonstrate backup isolation, key recovery, restoration timing, monitoring routes and runbooks.
6. Approve production HR field classification and migration templates.
7. Complete controlled staging acceptance with representative LGA and state users.

## Recommended next milestone

Complete the remaining P0 foundation in this order:

1. LGA Profile and immutable codes.
2. Audit event foundation.
3. Expanded isolation test harness.
4. Runtime version detection.
5. Browser and security delivery gates.

After that gate passes, implement the governance domain beginning with correspondence, council meetings, resolutions/actions and statutory returns.

# Implementation Status and Pending Work

Last reconciled: 2026-09-16  
Branch: `develop`  
Latest reviewed milestone: `406c34c`

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

## Partially complete backlog

| Backlog | Current state | Remaining acceptance work |
| --- | --- | --- |
| FND-003 Roles and Role Profiles | All approved roles are seeded | Create approved Role Profiles and test reproducible profile assignment |
| FND-005 Isolation test harness | User, navigation and Employee APIs have multi-LGA denial tests | Add direct document, submit/cancel, report, export, attachment and private-file denial coverage |
| FND-006 Audit event foundation | User/permission changes and authorization denials are recorded append-only | Add workflow-transition and export events as those capabilities are implemented |
| FND-008 Session lifecycle | Login, logout, CSRF and unauthorized guest behavior work | Add automated expired-session, disabled-user and concurrent-session journeys |
| FND-010 Delivery gates | Browser, critical axe, secret-scan and repeatable-migration gates are configured in CI | Add immutable artifact publishing and required-branch protection evidence |
| UI-001 Responsive shell | Desktop/mobile shell and principal pages are responsive | Perform browser viewport and keyboard acceptance checks for state, LGA and self-service users |
| UI-003 Data tables and filters | Employee list has server pagination/search/filtering | Build shared component, allowlisted sorting and URL-preserved filter state |
| UI-005 Accessibility baseline | Critical axe checks run on desktop/mobile authorization journeys | Complete keyboard journeys and broaden WCAG checks across principal workflows |
| UI-006 Low-bandwidth behavior | Hashed build is small and lists paginate | Define budget, add measurements, upload progress/retry and non-blocking skeleton patterns |
| HR-001 Scoped staff directory | Core approved Employee fields and LGA scope are live | Approve production field allowlist, add restricted-field denial tests and staging acceptance |
| HR-002 Staff verification | Verification status and authorized verify action exist | Implement exercise/record model, reviewer separation, evidence, exceptions, reasons, audit trail and Restricted-file controls |
| DSH-001 LGA operational dashboard | Scoped workforce/account metrics exist | Add metric source, reporting period, freshness, drill-down and approved governance/project indicators |
| FIN-001 Finance and treasury | Payment requests, budget/account/cost-center links, scoped dashboard and ERPNext ledger permissions are live | Configure chart-of-accounts policy, bank signatories, voucher print formats and staging acceptance |
| REV-001 Revenue administration | Revenue heads, assessments, submitted receipts, reconciliation totals and Revenue Officer role are live | Approve lawful revenue-head catalogue, rates, payment gateway and enforcement process |
| PRC-001 Procurement | Plans and cases link ERPNext material requests, RFQs, suppliers, purchase orders and receipts | Configure BSPPC thresholds, committees, bid evidence, public notices and contract-variation acceptance |

## Pending engineering work

### P0 foundation

1. **FND-005 Expanded isolation harness**: add direct document, submit/cancel, report, export, attachment and private-file cross-LGA denial coverage as each capability becomes available.
2. **API contract foundation**: standardize envelopes and errors, document `/api/v1` methods, and add an OpenAPI reference plus Bruno/Postman collection.
3. **FND-003 Role Profiles**: create approved Role Profiles and test reproducible assignment.
4. **FND-008 Session lifecycle tests**: cover expired sessions, disabled users and concurrent-session behavior.

### P1 shared frontend

1. **UI-002 Shared form controls**: accessible text, select, date, number, checkbox, file, validation, disabled, loading and error components.
2. **UI-004 Workflow components**: timeline, approval panel, rejection reason, confirmation and pending-action components.
3. **UI-005 Accessibility completion**: broaden automated WCAG checks and complete keyboard journeys.
4. Expand Playwright coverage from authorization denial to login/logout, LGA switching, user administration and HR workflows.
5. Implement global search, notifications, calendar, tasks, approvals, recently viewed, saved items, help and profile workflows; these are currently registered navigation workspaces only.

### P1 first-release domains

1. **Governance**: Government Correspondence, meetings/agendas/attendance/minutes, resolutions/actions, statutory returns, compliance and approval workflows.
2. **Projects and assets**: project register, milestones, inspections, evidence, exception review and scoped reports.
3. **HR completion**: verification exercises, personnel files, establishment positions, posting/transfers, promotions, attendance, retirement/exit and approved reports.
4. **Dashboards**: complete LGA dashboard and build the approved statewide comparison dashboard without ranking stale/incomplete periods.
5. **Notifications**: deduplicated reminders and escalations for overdue returns, actions and inspections.
6. **Authorized exports**: purpose capture, scoped fields, classification markings and export audit records.

### Deferred domains

Payroll, chieftaincy, external integrations and offline/PWA remain deferred until their approved entry conditions are met. Finance/revenue and procurement now have operational foundations; functions beyond the records and controls listed above remain pending until their business configuration is approved.

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
2. Expanded isolation test harness.
3. Role Profiles and assignment tests.
4. Session lifecycle browser tests.
5. Immutable artifact publishing and branch-protection evidence.

After that gate passes, implement the governance domain beginning with correspondence, council meetings, resolutions/actions and statutory returns.

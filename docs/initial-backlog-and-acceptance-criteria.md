# Initial Backlog and Acceptance Criteria

Status: Approved for implementation, 2026-09-14
Release target: Foundation and minimum useful first release

Current implementation progress and the prioritized remaining work are tracked in
[`implementation-status.md`](implementation-status.md). This backlog remains the approved
acceptance baseline; a feature is not considered complete merely because its navigation entry exists.

## Priority definitions

| Priority | Meaning |
| --- | --- |
| P0 | Required to prove isolation, identity, installation, and safe delivery |
| P1 | Required for the minimum useful pilot release |
| P2 | Valuable after the pilot foundation is stable |

## Foundation backlog

| ID | Priority | Backlog item | Acceptance criteria |
| --- | --- | --- | --- |
| FND-001 | P0 | Reproducible app installation | A clean version-15 site installs ERPNext, HRMS, and `dtmgp`; the parent and exactly 23 LGA Companies exist; a second seed run makes no changes |
| FND-002 | P0 | LGA profile and stable code | Every child Company has one LGA Profile with an immutable approved code matching the 23-code registry; duplicate Company/profile links are rejected |
| FND-003 | P0 | Roles and Role Profiles | Approved state and LGA roles install reproducibly; privileged roles are not granted by default; role fixtures contain no users |
| FND-004 | P0 | Company access utility | Server utility returns only Companies permitted to the current user; state scope is explicit; supplied request filters cannot broaden the result |
| FND-005 | P0 | Isolation test harness | Tests prove cross-LGA denial for list, direct read, create, update, submit, report, export, and private file access using at least two LGAs |
| FND-006 | P0 | Audit event foundation | Privileged access, Company-permission changes, workflow transitions, exports, and authorization denials create redacted, queryable audit events |
| FND-007 | P0 | Frontend user context | Vue loads current user, roles, allowed LGAs, active LGA, and permission-driven menu from the server; hardcoded identity data is removed |
| FND-008 | P0 | Session lifecycle | Login, logout, CSRF handling, expired session, disabled user, and unauthorized response paths work without storing secrets in browser storage |
| FND-009 | P0 | Runtime version detection | Build publishes version, commit, and build time; the client detects a newer release and offers a non-blocking refresh action |
| FND-010 | P0 | Delivery gates | CI runs clean install, backend tests, Vue type-check/tests/build, dependency audits, asset checks, and secret scanning; required checks block merge |

## Shared frontend backlog

| ID | Priority | Backlog item | Acceptance criteria |
| --- | --- | --- | --- |
| UI-001 | P1 | Responsive application shell | State, single-LGA, and self-service layouts work at agreed desktop and mobile widths without overlap, clipping, or layout shifts |
| UI-002 | P1 | Shared form controls | Text, select, date, number, checkbox, file, validation, disabled, loading, and error states are accessible and covered by component tests |
| UI-003 | P1 | Data table and filters | Authorized lists support allowlisted sort/filter, pagination, empty/error/loading states, and URL-preserved query state |
| UI-004 | P1 | Workflow components | Status, timeline, approval panel, rejection reason, confirmation, and pending-action states support keyboard and screen-reader use |
| UI-005 | P1 | Accessibility baseline | Critical pages meet WCAG 2.1 AA automated checks and complete keyboard journeys; exceptions are documented and owned |
| UI-006 | P1 | Low-bandwidth behavior | Initial authenticated shell remains within the approved asset budget; lists paginate; uploads show progress/retry; skeletons do not block navigation |

## First-release domain backlog

| ID | Priority | Backlog item | Acceptance criteria |
| --- | --- | --- | --- |
| GOV-001 | P1 | Council meeting register | Authorized LGA users create agendas and meetings within their Company; another LGA cannot discover or access them |
| GOV-002 | P1 | Resolution and action workflow | Secretary submits, Chairman approves/returns, owners update actions, and closure is audited; prohibited self-approval fails server-side |
| GOV-003 | P1 | Statutory returns | LGA/period uniqueness is enforced; local endorsement and state acceptance/correction follow the approved workflow; lateness is reported independently |
| HR-001 | P1 | Scoped staff directory | Reuse HRMS Employee data; expose only approved directory fields; LGA and state scope plus restricted-field denials are tested |
| HR-002 | P1 | Staff verification | Routine and exception workflows preserve reviewer separation, reasons, evidence access, and Restricted classification controls |
| PRJ-001 | P1 | Project register and milestones | Projects and milestones are Company-scoped, indexed, filterable, and visible statewide only to approved roles |
| PRJ-002 | P1 | Project inspection | Inspection scheduling, evidence, review, material-exception escalation, provenance, and private-file permissions pass workflow and denial tests |
| DSH-001 | P1 | LGA operational dashboard | Metrics show source, reporting period, and freshness; drill-down respects Company and field permissions |
| DSH-002 | P1 | Statewide dashboard | Approved state users compare all 23 LGAs; incomplete/stale periods are identified and not silently ranked with complete data |
| NTF-001 | P1 | Notifications and alerts | Overdue returns, actions, and inspections generate deduplicated reminders and escalations without exposing Confidential data in message subjects |
| EXP-001 | P1 | Authorized exports | Export requires explicit permission and purpose, applies server scope, marks classification, limits fields, and records actor, filters, row count, and time |

## Deferred backlog

| ID | Priority | Backlog item | Entry condition |
| --- | --- | --- | --- |
| FIN-001 | P2 | Finance and revenue extensions | Finance owner approves processes, chart structure, thresholds, and segregation |
| PRC-001 | P2 | Procurement integration | Procurement owner approves planning, evaluation, award, receipt, and payment boundaries |
| PAY-001 | P2 | Payroll integration | HR/finance owners approve Restricted fields, payroll controls, and reconciliation |
| TRA-001 | P2 | Chieftaincy workflows | Traditional Affairs owner approves institution, appointment, succession, petition, and dispute lifecycles |
| INT-001 | P2 | External integrations | Data-sharing agreement, security review, sandbox, idempotency, webhook, monitoring, and rollback are approved per integration |
| PWA-001 | P2 | Offline/PWA capability | Offline scope, protected-data storage, conflict resolution, cache invalidation, and update strategy are approved |

## Definition of ready

A backlog item may enter implementation when:

- Business owner, users, data fields, classification, Company scope, and workflow are identified.
- Acceptance criteria include successful and denied paths.
- Dependencies, integrations, migration needs, and operational impact are known.
- UI/API contracts or approved mockups exist where required.
- Security, privacy, retention, audit, and accessibility implications are recorded.

## Definition of done

- Acceptance criteria and authorization-denial tests pass.
- Code is reviewed, documented, and committed using the project conventions.
- Clean installation or migration and relevant backend/frontend CI checks pass.
- No secrets or production personal data are committed or used in tests.
- Audit, observability, backup, and support impacts are implemented or explicitly not applicable.
- Known limitations and deferred work are recorded.
- Business owner accepts the item in staging before pilot or production release.

## Stage sequence

1. Complete `FND-001` through `FND-010` and the Stage 0 external sign-off register.
2. Complete shared UI foundations `UI-001` through `UI-006`.
3. Implement governance, returns, HR visibility, projects, dashboards, notifications, and exports domain by domain.
4. Pilot with representative LGAs and close critical findings.
5. Begin deferred domains only after their entry conditions are approved.

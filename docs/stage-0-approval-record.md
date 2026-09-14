# Stage 0 Approval Record

Decision date: 2026-09-14
Approval authority: Project owner, recorded from explicit implementation instruction
Scope: architecture and delivery baseline, not production go-live

## Decision status

| Item | Stage 0 status | Approved baseline | Production condition |
| --- | --- | --- | --- |
| State-office mapping | Approved with condition | Functional offices in `state-offices-and-workflows.md` are the authorization model | Name the current statutory body and accountable office holder for each function before onboarding production users |
| Workflow approvers | Approved with condition | Council, return, inspection, and staff-verification transitions and role separation | Process owners confirm named approvers, alternates, deadlines, and any statutory review steps |
| Approval thresholds | Approved with condition | No monetary threshold is introduced in the initial four workflows; material project exceptions require state review | Finance/procurement thresholds require a separate signed schedule before those workflows are enabled |
| Delegation | Approved with condition | Delegation is time-bound, scoped, independently approved, and audited; no self-approval | Business owners define maximum duration and emergency approvers before production |
| Role-permission matrix | Approved | Roles, Company scope, export constraints, and segregation rules in `role-permission-matrix.md` | Negative authorization tests must pass before sensitive modules are released |
| Data-classification matrix | Approved | Public, Internal, Confidential, and Restricted levels and domain defaults | Dataset owners classify every production field and attachment collection before migration |
| Retention and disposal | Approved with condition | Proposed periods and hold/disposal controls in `operations-and-delivery-policy.md` | Records/legal owner signs the schedule and identifies disposal authority before automated deletion |
| Backup and recovery | Approved with condition | Tier 1 RPO 15 minutes, RTO 4 hours; backup and exercise schedule as documented | Hosting operator demonstrates isolation, key recovery, and measured restoration |
| Monitoring and alerts | Approved with condition | Signals, initial thresholds, ownership, and runbook requirement as documented | Operations names contacts, routes alerts, and tunes thresholds during pilot |
| CI and release controls | Approved | Clean installation, tests, frontend build, dependency audit, immutable artifacts, and rollback requirements | Remaining browser and migration checks are implemented before their related release gate |

## Confirmed workflow authority

| Workflow | Preparer | Local approval/review | State approval/review | Self-approval |
| --- | --- | --- | --- | --- |
| Council resolution | LGA Secretary | LGA Chairman | State oversight is read-only unless an intervention is separately authorized | Prohibited |
| Statutory return | Designated LGA reporting officer | LGA Secretary endorses | State Administrator accepts or requests correction | Prohibited |
| Project inspection | LGA Project Officer | LGA Secretary or approved works reviewer | State Project Officer resolves material exceptions | Prohibited |
| Staff verification | Employee or HR-assisted process | HR Officer verifies routine cases | State HR Officer or approved panel resolves exceptions | Prohibited |

Rejection, return, override, emergency access, and delegation require a reason. Delegates cannot receive powers beyond the delegator's role or Company scope.

## Required sign-off register

The following evidence remains mandatory for production. Blank names are deliberate; no signature is inferred from this document.

| Sign-off | Required evidence | Named approver | Status |
| --- | --- | --- | --- |
| Local-government business ownership | Statutory-office mapping and workflow schedule | To be appointed | Pending external sign-off |
| Human-resources ownership | Staff-verification process, field set, and retention | To be appointed | Pending external sign-off |
| Finance/procurement ownership | Monetary thresholds and segregation schedule | To be appointed | Deferred until finance/procurement scope |
| Records/legal ownership | Retention, legal hold, archival, and disposal schedule | To be appointed | Pending external sign-off |
| Information security | Classification controls, emergency access, logging, and incident handling | To be appointed | Pending external sign-off |
| Hosting/operations | Backup isolation, recovery exercise, monitoring routes, and runbooks | To be appointed | Pending operational evidence |
| Pilot business acceptance | Controlled sample workflows across representative LGAs | To be appointed | Deferred until pilot |

## Change control

- The project owner may revise Stage 0 design decisions through an ADR or a superseding approval record.
- Production conditions cannot be waived silently. An exception records owner, reason, risk, compensating control, expiry, and approval.
- Role, workflow, classification, retention, RPO/RTO, and threshold changes require documentation and corresponding test updates.
- This approval does not authorize production personal data, financial processing, payroll, external integrations, or statewide rollout.

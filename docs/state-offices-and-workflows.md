# State Offices and Initial Workflows

Status: Stage 0 baseline  
Scope: Benue State and all 23 Local Government Areas  
Organizational model: one Frappe site with each LGA represented by a child Company

## State-level offices

The platform uses functional offices so permissions remain stable if the legal name of a ministry, department, or agency changes. The project owner must map each function to the current statutory office before production onboarding.

| Functional office | Platform responsibility | Typical platform roles |
| --- | --- | --- |
| State Platform Governance Council | Policy, scope, risk acceptance, stage gates, and cross-office dispute resolution | State Executive Viewer, State Administrator |
| Local Government Administration Office | Business ownership, LGA onboarding, statutory-return coordination, and statewide supervision | State Administrator, State Executive Viewer |
| State Executive Oversight | Statewide scorecards, exceptions, and executive decisions without routine record editing | State Executive Viewer |
| State Finance and Treasury Oversight | Consolidated finance visibility, budget controls, revenue oversight, and treasury policy | State Auditor, finance roles introduced with the finance module |
| State HR Oversight | Establishment controls, staff verification oversight, postings, transfers, and HRMS governance | State Administrator, HR Officer with statewide scope |
| State Procurement Oversight | Procurement policy, exception monitoring, and high-value approval controls | State Auditor, Procurement Officer with statewide scope |
| State Project Monitoring Office | Project portfolio supervision, inspection review, and delayed-project escalation | Project Officer with statewide scope, State Executive Viewer |
| State Traditional Affairs Office | Traditional institution records, appointments, succession matters, petitions, and disputes | Traditional Affairs Officer with statewide scope |
| State Internal Audit | Independent read, export, audit-trail review, and control testing across all LGAs | State Auditor |
| State ICT and Platform Operations | Identity, availability, deployment, backup, integrations, and technical support | System Manager |

State Platform Governance Council membership does not grant operational permissions by itself. Every user receives explicit roles and Company permissions.

## LGA operating offices

| Functional office | Primary responsibility | Typical role |
| --- | --- | --- |
| Chairman's Office | Executive approval and performance oversight | LGA Chairman |
| Secretary to the LGA | Council agenda, minutes, resolutions, correspondence, and coordination | LGA Secretary |
| LGA Administration | User onboarding, local master data, and operational coordination | LGA Administrator |
| Treasury | LGA finance, revenue, budget, and payment controls | Treasurer |
| Human Resources | Staff records, verification, establishment, leave, and HR requests | HR Officer |
| Procurement | Procurement planning and transaction processing | Procurement Officer |
| Works and Project Monitoring | Project records, milestones, inspections, evidence, and assets | Project Officer |
| Traditional Affairs Desk | Local traditional institution records, petitions, and case processing | Traditional Affairs Officer |
| Internal Audit | Independent LGA control review and exception reporting | Internal Auditor |
| General Oversight | Authorized read-only operational access | Read-only Officer |

## Workflow rules

- The server derives the user's permitted Companies; client-selected LGA context never grants access.
- A submitter cannot approve or verify the same record unless an emergency exception is documented and audited.
- Rejection and return transitions require a reason.
- Submitted and approved records are not silently edited; corrections use amendment or controlled reopen actions.
- Every transition records actor, timestamp, previous state, new state, and comment.
- State officers supervise and escalate but do not replace required LGA approvals unless a workflow explicitly provides a state intervention transition.
- Notifications are reminders, not authorization. Permissions and workflow state remain authoritative.

## Council resolution workflow

Owner: LGA Secretary  
Approver: LGA Chairman or authorized council approval role  
State visibility: State Administrator, State Executive Viewer, State Auditor

| State | Allowed action | Next state | Actor |
| --- | --- | --- | --- |
| Draft | Prepare resolution and action owners | Submitted for Approval | LGA Secretary |
| Submitted for Approval | Approve | Approved | LGA Chairman |
| Submitted for Approval | Return with reason | Draft | LGA Chairman |
| Approved | Record implementation actions | In Implementation | LGA Secretary |
| In Implementation | Update assigned action | In Implementation | Assigned officer |
| In Implementation | Confirm all actions complete | Completed | LGA Secretary |
| Completed | Verify closure | Closed | LGA Chairman |

Overdue action dates create alerts but do not change the resolution state automatically.

## Statutory return workflow

Owner: designated LGA reporting officer  
Local reviewer: LGA Secretary  
State reviewer: Local Government Administration Office

| State | Allowed action | Next state | Actor |
| --- | --- | --- | --- |
| Draft | Enter reporting-period data and evidence | Submitted for LGA Review | Reporting officer |
| Submitted for LGA Review | Return with reason | Draft | LGA Secretary |
| Submitted for LGA Review | Endorse | Submitted to State | LGA Secretary |
| Submitted to State | Accept | Accepted | State Administrator |
| Submitted to State | Request correction | Correction Required | State Administrator |
| Correction Required | Amend and resubmit | Submitted for LGA Review | Reporting officer |

The reporting period and LGA combination must be unique. Late submission is stored separately from workflow status.

## Project inspection workflow

Owner: LGA Project Officer  
Local reviewer: LGA Secretary or delegated works supervisor  
State escalation: State Project Monitoring Office

| State | Allowed action | Next state | Actor |
| --- | --- | --- | --- |
| Planned | Schedule inspection | Scheduled | Project Officer |
| Scheduled | Capture findings and evidence | Submitted for Review | Project Officer |
| Submitted for Review | Return with reason | Scheduled | Local reviewer |
| Submitted for Review | Accept findings | Reviewed | Local reviewer |
| Reviewed | Raise material exception | State Review Required | Local reviewer or Internal Auditor |
| State Review Required | Resolve or issue directive | Closed | State Project Officer |
| Reviewed | Close without escalation | Closed | Local reviewer |

Inspection evidence retains uploader, capture time, file checksum, and available location metadata. Original evidence is not replaced after submission.

## Staff-directory and verification workflow

The first release provides authorized HR visibility and a controlled verification process; payroll changes remain outside this workflow.

| State | Allowed action | Next state | Actor |
| --- | --- | --- | --- |
| Not Started | Open verification record | Pending Staff Confirmation | HR Officer |
| Pending Staff Confirmation | Confirm details or report discrepancy | HR Review | Employee or HR Officer-assisted process |
| HR Review | Verify | Verified | HR Officer |
| HR Review | Escalate exception | Exception Review | HR Officer |
| Exception Review | Resolve | Verified | State HR Officer or authorized review panel |
| Exception Review | Reject with reason | Rejected | State HR Officer or authorized review panel |

Bank, identity, health, disciplinary, and payroll details are excluded from general staff-directory views.

## Required business validation

- Map functional state offices to current statutory bodies and named process owners.
- Confirm approval thresholds and delegation rules.
- Confirm statutory-return types, due dates, and correction rules.
- Confirm who may close project exceptions and staff-verification disputes.
- Approve emergency-access and temporary-delegation procedures.

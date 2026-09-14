# Role and Permission Matrix

Status: Approved for implementation, 2026-09-14

## Scope notation

| Scope | Meaning |
| --- | --- |
| System | Technical configuration across the site |
| Statewide | All 23 LGA Companies and approved state-level records |
| Assigned LGA | Only Companies explicitly assigned through Frappe User Permissions |
| Own | Records created by or assigned to the current user, within an assigned LGA |

All LGA operational roles require exactly one assigned Company by default. Statewide access requires an explicit state role and all approved Company permissions. `System Manager` is reserved for technical administration and is not a substitute for a business role.

## Role matrix

Legend: `M` manage configuration, `C` create, `R` read, `U` update drafts, `S` submit, `A` approve or transition, `X` export, `-` no access. Workflow and document-state rules may further reduce these permissions.

| Role | Scope | Users and setup | Governance | HR | Projects/assets | Traditional affairs | Finance/procurement | Audit/export |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| System Manager | System | M | - | - | - | - | - | Technical logs only |
| State Administrator | Statewide | M | CRUSA | R | RA | RA | R | RX |
| State Executive Viewer | Statewide | - | R | R | R | R | R | RX, approved summaries only |
| State Auditor | Statewide | - | RX | RX | RX | RX | RX | RX |
| LGA Administrator | Assigned LGA | M, no role escalation | CRU | R | R | R | R | R, limited export |
| LGA Chairman | Assigned LGA | - | RA | R | RA | R | R | R, approved summaries only |
| LGA Secretary | Assigned LGA | - | CRUSA | R | RA | CRU | R | R, limited export |
| Treasurer | Assigned LGA | - | R | - | R | - | CRUSA | R, finance export |
| HR Officer | Assigned LGA or approved statewide | - | R | CRUSA | - | - | payroll access only when separately granted | R, HR export |
| Procurement Officer | Assigned LGA or approved statewide | - | R | - | R | - | CRUS | R, procurement export |
| Project Officer | Assigned LGA or approved statewide | - | R | - | CRUSA | - | R | R, project export |
| Traditional Affairs Officer | Assigned LGA or approved statewide | - | R | - | - | CRUSA | - | R, case export when authorized |
| Internal Auditor | Assigned LGA | - | RX | RX | RX | RX | RX | RX |
| Read-only Officer | Assigned LGA | - | R | R, directory fields only | R | R, non-restricted | R, non-sensitive summaries | No bulk export |

## Permission constraints

- Every scoped custom DocType has a mandatory `company` field. The Vue label is `LGA`; the database field remains `company`.
- Frappe User Permissions provide the allowed Company set. A default Company improves usability but does not grant access.
- Permission query conditions restrict lists, reports, search, export, and link-field results.
- Document permission hooks restrict direct reads, writes, submits, cancels, amendments, and guessed document names.
- API services intersect every requested filter with the caller's allowed Companies.
- Child-table access inherits from its parent document and is never granted independently.
- File access follows the attached document's permission and classification.
- Read permission does not imply print, download, report, or export permission.
- Statewide HR, procurement, project, or traditional-affairs officers receive the same functional role plus statewide Company permissions; no duplicate role is required.
- A System Manager who needs temporary business-data access receives a separate, time-bound role through the approved emergency-access process.

## Segregation of duties

| Control | Required separation |
| --- | --- |
| User and role administration | Requester cannot approve their own privileged access |
| Council resolutions | LGA Secretary submits; LGA Chairman approves |
| Statutory returns | Reporting officer prepares; LGA Secretary endorses; state office accepts |
| Project inspections | Inspector submits; reviewer accepts or escalates |
| Procurement | Request, evaluation, approval, receipt, and payment roles are separated when implemented |
| Finance | Journal/payment preparation, approval, and reconciliation are separated when implemented |
| Staff verification | Subject or assisting officer confirms; authorized HR reviewer verifies |
| Audit | Auditors cannot alter the operational records they review |

## Access administration

- Access is requested with role, Company scope, reason, start date, and optional expiry date.
- LGA Administrator may onboard standard users only within the assigned LGA and cannot grant state, audit, System Manager, or additional-Company access.
- State Administrator manages approved business access. System Manager manages technical access.
- Privileged and cross-LGA access requires independent approval and is reviewed quarterly.
- Transfers, suspension, termination, and expired delegation trigger prompt access removal.
- Role, User Permission, export, failed authorization, and emergency-access events are audited.

## Mandatory authorization tests

- An LGA user cannot list, search, open, print, export, report on, update, submit, cancel, or attach files to another LGA's records.
- Changing `company` in a request body or URL does not broaden access.
- A read-only role cannot invoke workflow transitions or bulk exports.
- A preparer cannot perform a prohibited self-approval.
- A state viewer cannot modify operational data.
- An auditor can inspect approved audit data but cannot alter source records.
- Revoked and expired access takes effect for existing and new sessions.

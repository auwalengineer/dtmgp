# Data-Classification Matrix

Status: Stage 0 baseline

## Classification levels

Classification is assigned to the dataset and inherited by exports, attachments, backups, logs, and derived reports. When fields of different levels appear together, the record uses the highest applicable level.

| Level | Definition | Examples | Default access | Minimum controls |
| --- | --- | --- | --- | --- |
| Public | Approved for publication | Published resolutions, approved public project summaries, public office contacts, public notices | Anonymous or authenticated, as approved | Publication approval, integrity checks, version history |
| Internal | Routine government information not approved for public release | Draft agendas, internal correspondence, operational dashboards, non-sensitive asset registers | Authorized staff in assigned scope | Authentication, Company scoping, audit logging |
| Confidential | Disclosure could harm operations, privacy, procurement, or public trust | Personnel files, evaluation records, bid details before award, internal audit working papers, non-public financial details | Named functional roles and assigned scope | Least privilege, export control, private files, access review, encrypted transport and backups |
| Restricted | Highly sensitive data whose misuse could cause serious harm or enable fraud | Password or token material, bank details, identity numbers, payroll details, health or disciplinary records, protected petitions, security findings | Explicitly approved named roles; no general dashboard exposure | Field minimization, masking, strong authentication, detailed access logs, download restrictions, short-lived integrations, incident alerting |

Secrets, passwords, API keys, session tokens, and encryption keys must not be stored in ordinary DocType fields, fixtures, logs, source control, or frontend configuration.

## Domain matrix

| Domain or dataset | Default class | LGA access | State access | Export rule | Notes |
| --- | --- | --- | --- | --- | --- |
| LGA profile and public contacts | Internal until published | Assigned LGA roles | Approved statewide roles | Authorized | Approved subset may become Public |
| User account and role assignment | Confidential | LGA Administrator, limited scope | State Administrator, System Manager | Restricted | Passwords and session material remain Restricted and non-exportable |
| Council meeting draft and agenda | Internal | Governance roles | State oversight roles | Limited | Becomes Public only through explicit publication |
| Approved resolution | Internal | Assigned LGA roles | Statewide oversight | Authorized | Approved public version may be Public |
| Government correspondence | Confidential | Named participants and authorized governance roles | Authorized oversight | Case-by-case | Classification may be Restricted based on content |
| Statutory return | Confidential | Reporting and review roles | State reviewers and auditors | Authorized | Published aggregate is a separate Public artifact |
| Staff directory fields | Internal | Authorized assigned-LGA users | Authorized state users | Limited | Name, title, department, and work contact only |
| Personnel, verification, or disciplinary file | Restricted | HR and specifically authorized reviewers | Authorized state HR and auditors | Normally prohibited | Excluded from general search and dashboards |
| Payroll, bank, tax, identity, health data | Restricted | Explicit HR/payroll roles | Explicit state HR/payroll roles | Prohibited unless legally approved | Mask fields and avoid logging values |
| Project register and approved progress summary | Internal | Assigned LGA roles | Statewide oversight | Authorized | Approved publication subset may be Public |
| Inspection evidence and location | Confidential | Project reviewers and auditors | State project oversight | Controlled | Preserve provenance and file checksum |
| Procurement plan | Internal | Procurement and oversight roles | State oversight | Authorized | Publication follows procurement policy |
| Bid or evaluation before award | Restricted | Named procurement participants | Authorized oversight and audit | Prohibited before authorized disclosure | Enforce time-bound access |
| Contract and award record | Confidential | Authorized LGA roles | State oversight and audit | Controlled | Approved publication subset may be Public |
| Financial transaction and revenue record | Confidential | Finance and audit roles | State finance oversight and audit | Controlled | Payment credentials are Restricted |
| Traditional institution public register | Internal until published | Traditional affairs roles | State oversight | Authorized | Approved fields may become Public |
| Petition, dispute, or succession evidence | Restricted | Named case officers | Authorized state reviewers and auditors | Normally prohibited | Protect parties, witnesses, and allegations |
| Audit log and security event | Restricted | Internal Auditor for approved events | State Auditor and System Manager by duty | Prohibited by default | Append-only behavior and tamper evidence required |
| Aggregated executive KPI | Internal | LGA summary for assigned LGA | Statewide executive roles | Approved summaries | Show source and freshness; suppress sensitive small groups |
| Backup and disaster-recovery copy | Highest class present | No routine user access | Named platform operators | Prohibited | Encrypt, inventory, test restoration, and log access |

## Handling rules

- Collect only fields required for an approved purpose and document the lawful or administrative basis before production migration.
- Use private Frappe files for Confidential and Restricted attachments.
- Do not include Confidential or Restricted values in URLs, analytics events, notification subjects, client logs, or server error messages.
- Apply field masking to identity, bank, payroll, health, and protected case information.
- Bulk export is a separate privilege, includes classification markings, and is audited with actor, purpose, filters, row count, and timestamp.
- Non-production environments use synthetic data. Production personal data is not copied into development.
- Integrations receive the smallest approved field set and classification; credentials remain server-side.
- Retention schedules are defined by record class and legal owner before go-live. Expiry triggers review, defensible deletion, archival, or legal hold.
- Classification changes require the dataset owner's approval and an audit entry.
- Suspected exposure of Confidential or Restricted data follows the incident-response process.

## Ownership and review

| Responsibility | Owner |
| --- | --- |
| Assign initial classification | Business process owner |
| Approve access roles | Data owner and State Administrator |
| Implement controls | State ICT and Platform Operations |
| Review compliance | State Internal Audit |
| Approve publication or declassification | Authorized business or communications owner |
| Approve retention and legal hold | Records/legal owner |

The matrix is reviewed before each domain enters production and at least annually thereafter.

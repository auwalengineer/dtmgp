# Operations and Delivery Policy

Status: Approved for implementation with production evidence conditions, 2026-09-14
Applies to: development, staging, production, backups, exports, integrations, and support operations

The targets below are the minimum technical baseline. The project owner, records owner, security owner, and hosting operator must approve them before production go-live. A legal hold or applicable records rule overrides normal deletion.

## Ownership

| Area | Accountable owner | Operational owner | Independent review |
| --- | --- | --- | --- |
| Audit and security events | State Platform Governance Council | State ICT and Platform Operations | State Internal Audit |
| Business-record retention | Relevant business or records owner | Application administrators | State Internal Audit or legal/records function |
| Backup and recovery | State ICT and Platform Operations | Hosting/database operator | State Internal Audit |
| Monitoring and incidents | State ICT and Platform Operations | Platform support team | Platform Governance Council |
| Release approval | Product/business owner | Release manager | Security and operations reviewers |

## Audit requirements

### Events that must be recorded

- Successful and failed authentication, logout, password reset, session revocation, and account lockout.
- User creation, disablement, role changes, Role Profile changes, Company User Permission changes, delegation, and emergency access.
- Read access to Restricted records where technically feasible.
- Create, update, submit, approve, reject, return, cancel, amend, delete, print, download, and bulk export of governed records.
- Workflow transitions, including previous state, next state, actor, reason, and timestamp.
- Changes to classification, retention class, configuration, fixtures, integrations, and scheduled jobs.
- API authentication failures, authorization denials, rate-limit events, webhook validation failures, and idempotency conflicts.
- Backup, restore, release, migration, rollback, maintenance-mode, and administrative console operations.

### Required audit fields

| Field | Requirement |
| --- | --- |
| Event identifier | Globally unique and immutable |
| Occurred at | UTC timestamp; display may use Africa/Lagos |
| Actor | User or service identity; never only a display name |
| Session/request | Correlation identifier without session secret |
| Source | Application, API, worker, integration, or administrator |
| Action and outcome | Stable event code plus success, denial, or failure |
| Object | DocType/resource and record identifier when allowed |
| LGA scope | Company identifier for scoped events |
| Change summary | Changed field names and safe before/after values; Restricted values are redacted |
| Reason | Mandatory for rejection, return, override, export, and emergency access |
| Network context | Security-approved source address/device metadata where lawful and available |

Audit events are append-only to application users. Business-record deletion must not delete the corresponding audit event. Clock synchronization is monitored. Audit access and exports are themselves audited.

Do not log passwords, session cookies, tokens, encryption keys, complete bank details, complete identity numbers, health details, protected petition text, or uploaded file contents.

## Retention baseline

| Record category | Proposed minimum | Disposal action |
| --- | --- | --- |
| Council resolutions and official minutes | Permanent | Transfer to approved archive; retain searchable integrity record |
| Statutory returns and acceptance history | 7 years after reporting period | Review, then archive or defensibly delete |
| Project, contract, inspection, and asset evidence | 10 years after closure/disposal | Review for disputes, audit, and archival value |
| Procurement and financial records | 7 years after financial-year close | Review legal/audit holds, then defensibly delete |
| Personnel and verification records | Employment/service end plus 7 years | Delete or archive approved subset; preserve legal holds |
| Petitions, disputes, and succession cases | 10 years after final closure | Case-owner review before disposal |
| Workflow and business-change audit | 7 years | Defensibly delete after owner approval |
| Privileged access and security audit | 7 years | Defensibly delete after security and audit approval |
| Authentication and ordinary access logs | 2 years | Aggregate where useful, then delete raw events |
| Application and infrastructure diagnostics | 90 days searchable, 1 year archived | Delete after incident and legal-hold checks |
| Failed integration payload metadata | 1 year | Delete payload details earlier when no longer needed |
| Backups | Per backup schedule below | Cryptographic or provider-verifiable deletion |

Retention begins from the latest relevant event, such as case closure, contract completion, employee separation, or financial-year close. Records under investigation, litigation, audit, information request, or legal hold are suspended from disposal. Production retention jobs require dry-run reports, owner approval, deletion counts, and audit evidence.

## Backup policy

### Production schedule

| Backup | Frequency | Retention | Storage requirement |
| --- | --- | --- | --- |
| Database transaction/binlog protection | Continuous or at most 15-minute loss window | 7 days | Encrypted and isolated from the application host |
| Full database backup | Daily | 35 days | Encrypted, checksummed, separate failure domain |
| Private and public files | Daily incremental; weekly full | 35 days daily, 12 weeks weekly | Encrypted; permissions preserved |
| Monthly recovery point | Monthly | 12 months | Immutable or write-protected copy |
| Configuration, deployment manifests, and site settings | Every approved release and after material change | Current plus 12 months | Secrets stored separately in approved secret storage |

- At least one recoverable copy is isolated from production credentials and routine administrator deletion.
- Backups are encrypted in transit and at rest, inventoried, monitored, and access logged.
- Encryption keys are backed up separately with documented recovery custodians.
- Backup jobs fail visibly; missed or unverified backups alert the platform support team.
- Development does not receive production backups. Staging restores use anonymized or synthetic data unless an approved exercise requires otherwise.

## Recovery objectives

| Service tier | Scope | RPO | RTO |
| --- | --- | --- | --- |
| Tier 1 | Production database, private files, authentication, core workflows | 15 minutes | 4 hours |
| Tier 2 | Background jobs, reporting, exports, and notifications | 4 hours | 8 hours |
| Tier 3 | Staging and development | 24 hours | 2 business days |

RPO is the maximum acceptable data-loss window. RTO is the target time to restore agreed service after incident declaration; it is not a guarantee until measured by recovery exercises.

## Disaster-recovery procedure

1. The incident commander declares the recovery level and freezes conflicting changes.
2. Operations records the incident timeline, affected site, last known good release, and candidate recovery point.
3. Credentials and infrastructure are contained or replaced when compromise is suspected.
4. The database, files, configuration, encryption access, queues, and scheduled jobs are restored into an isolated environment.
5. Automated integrity checks verify schema/migrations, Company tree, file references, user access, queues, and critical workflows.
6. Business owners validate controlled samples across multiple LGAs, including permission denials.
7. The incident commander authorizes traffic restoration and communicates recovery status.
8. Operations monitor errors, queues, reconciliation reports, and data freshness during the stabilization window.
9. A post-incident review records root cause, data loss, target performance, control improvements, and owners.

Database-only restoration is not considered complete until matching files and configuration are reconciled. Integration replay uses idempotency controls and an approved recovery window.

## Recovery testing

- Verify backup completion and checksums daily through automation.
- Perform a sampled file and database restore monthly.
- Perform a complete isolated-site restore quarterly.
- Conduct an annual disaster-recovery exercise involving technical and business owners.
- Test restoration before major infrastructure, database, Frappe, ERPNext, or HRMS upgrades.
- Record actual RPO, RTO, missing artifacts, reconciliation results, and corrective actions.

## Observability requirements

### Signals

| Area | Minimum signals |
| --- | --- |
| User experience | Availability, response time, error rate, failed navigation/API requests, frontend version |
| Web/API | Request rate, latency percentiles, status codes, authentication failures, authorization denials, rate limits |
| Workers and scheduler | Queue depth, oldest-job age, failures, retries, scheduler heartbeat, long-running jobs |
| Database | Availability, connections, slow queries, lock waits, replication/binlog health, storage growth |
| Redis/cache | Availability, memory, evictions, connection failures, queue health |
| Files | Storage capacity, upload/download failures, missing references, malware-scan status when introduced |
| Integrations | Success/failure rate, latency, retry count, dead letters, last successful exchange |
| Business freshness | Last accepted return, LGA reporting completeness, overdue workflows, stale KPI snapshots |
| Infrastructure | CPU, memory, disk, inode use, certificate expiry, time synchronization, backup completion |

Logs use structured fields, UTC timestamps, correlation IDs, environment, service, release, user/service identity, LGA code where safe, event code, and classification. Restricted values are redacted before they reach the logging platform.

### Initial alert thresholds

| Alert | Threshold | Priority |
| --- | --- | --- |
| Production unavailable | Two consecutive checks or 2 minutes | Critical |
| Error rate | More than 5% for 5 minutes | High |
| API latency | p95 above 2 seconds for 10 minutes | High |
| Queue delay | Oldest normal job above 10 minutes | High |
| Scheduler missing | No heartbeat for 10 minutes | High |
| Backup failure | Any scheduled production backup fails or is unverified | Critical |
| Disk usage | Above 80% warning; above 90% critical | High/Critical |
| Certificate expiry | 30 days warning; 7 days critical | Medium/Critical |
| Repeated cross-LGA denials | Security-defined burst threshold | Security review |
| Reporting freshness | Required source exceeds approved reporting interval | Business alert |

Alert routes, duty hours, escalation contacts, and paging tools are environment-specific configuration and are not stored in source control. Every production alert has an owner and runbook.

## Environment controls

| Control | Development | Staging | Production |
| --- | --- | --- | --- |
| Data | Synthetic | Synthetic/anonymized | Approved live data |
| Access | Delivery team | Delivery and acceptance team | Named operational users |
| Debug mode | Allowed locally | Disabled by default | Disabled |
| Secrets | Local approved mechanism | Secret store | Secret store with rotation |
| Backups | Best effort | Daily during active testing | Production schedule |
| Monitoring | Basic | Production-like | Full signals and alerting |
| Deployment | Developer initiated | Automated from approved commit | Approved immutable release |

Environment credentials, databases, file stores, domains, queues, and integration accounts are separate. Production changes do not originate from developer workstations.

## CI quality gates

Every pull request must eventually enforce:

- Python formatting, linting, import checks, secret scanning, and Frappe security rules.
- Vue formatting/linting, TypeScript type-check, unit tests, and production build.
- Python dependency and production npm dependency vulnerability checks.
- Clean Frappe-site creation, app installation, migration, and idempotent seed verification with exactly 23 LGA children.
- Backend tests, including cross-LGA denial cases when permission code is introduced.
- API contract tests and critical Playwright journeys when those layers are introduced.
- A build-integrity check proving every asset referenced by `index.html` exists.
- Review of migrations, fixtures, permission changes, retention changes, and new external data flows.

Current gap: CI covers backend installation/tests, Python lint/security checks, Vue type-check/tests/build, explicit 23-LGA seed assertions, and frontend asset integrity. Browser tests will be added when critical integrated journeys are available.

## Release policy

1. Create a release candidate from a reviewed commit on `develop`.
2. Build immutable backend and frontend artifacts in CI; do not rebuild differently for production.
3. Record semantic version, commit, build time, migrations, dependencies, checksums, and known limitations.
4. Deploy to staging, run migrations, smoke tests, authorization denials, backup/restore readiness checks, and user acceptance.
5. Obtain business, security, and operations approval for production.
6. Take and verify a pre-deployment recovery point.
7. Deploy to a versioned directory and atomically switch the active frontend release.
8. Run database migrations once under controlled maintenance and capture output.
9. Verify login, current-user context, LGA scope, critical workflows, queues, scheduler, assets, and version metadata.
10. Monitor through the stabilization window and either close the release or invoke the tested rollback procedure.

`index.html`, `runtime-config.json`, `version.json`, service-worker metadata, and deployment metadata use `no-cache` or revalidation. Content-hashed assets use `public, max-age=31536000, immutable`. A service worker is not introduced until offline behavior and update handling are approved.

## Rollback requirements

- Every release has a named decision owner, previous known-good application artifact, migration assessment, and rollback runbook.
- Application rollback uses the previous immutable artifact. Do not merge old and new `dist` directories.
- Database rollback prefers a forward corrective patch. Restore from backup only when the data-loss and reconciliation impact is approved.
- Breaking or destructive migrations require a maintenance window, tested restoration point, and explicit rollback limitations.
- External writes are reconciled before replay or rollback to prevent duplicate government or financial actions.

## Approval checklist

- Records/legal owner approves retention periods and disposal authority.
- Security owner approves audit fields, redaction, alert thresholds, and emergency access.
- Hosting operator demonstrates backup isolation and encryption-key recovery.
- Quarterly restore proves the Tier 1 RPO/RTO or records an approved remediation plan.
- Business owners identify critical journeys and recovery-validation samples.
- Delivery owner implements all CI gaps before the Stage 0 gate is declared complete.

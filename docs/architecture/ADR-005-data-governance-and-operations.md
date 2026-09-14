# ADR-005: Classification-Driven Governance and Recovery Targets

Status: Accepted with production conditions
Date: 2026-09-14

## Context

The platform will handle public records, internal operations, personal data, financial information, protected cases, audit history, and backups. Controls must follow data sensitivity and measured service needs.

## Decision

Use four classifications: Public, Internal, Confidential, and Restricted. Records inherit the highest applicable field or attachment classification. Apply least privilege, private-file controls, export auditing, redaction, synthetic non-production data, legal holds, and approved retention schedules.

Set initial Tier 1 recovery targets to a 15-minute RPO and 4-hour RTO. Use isolated encrypted backups, monthly sampled restores, quarterly complete restores, and annual disaster-recovery exercises. Monitor application, worker, database, cache, file, integration, security, backup, and business-freshness signals.

## Consequences

- Dataset owners must classify fields before production migration.
- Records/legal owners must sign retention and disposal schedules.
- Hosting operators must demonstrate that recovery targets are achievable.
- Restricted values are excluded from ordinary logs, URLs, notifications, analytics, and frontend configuration.
- Automated deletion cannot begin until legal holds, dry runs, approvals, and disposal evidence are implemented.

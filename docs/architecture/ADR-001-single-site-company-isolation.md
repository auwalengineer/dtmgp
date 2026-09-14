# ADR-001: Single-Site Company-Based LGA Isolation

Status: Accepted
Date: 2026-09-14

## Context

The platform must isolate operations for 23 LGAs while allowing authorized state officers to supervise and report across them. Separate sites would provide stronger database boundaries but multiply deployment, upgrades, identity, integrations, and statewide aggregation work.

## Decision

Use one Frappe site. Represent `Benue State Local Government Administration` as a group Company and each LGA as a child Company. Every scoped custom record has a mandatory `company` link displayed as `LGA` in Vue.

Enforce isolation through Company User Permissions, query conditions, document permission hooks, report/export checks, private-file access, and server-derived API scope. State roles receive explicitly approved multi-Company access.

## Consequences

- Statewide reporting and shared ERPNext/HRMS configuration are practical.
- One deployment and migration path serves all LGAs.
- Company permissions are an organizational boundary, not hard database multitenancy.
- Every list, direct read, write, workflow, report, export, and file path needs denial tests.
- A future legal requirement for hard isolation would require a multi-site architecture and aggregation service.

## Rejected alternatives

- One site per LGA: deferred because current requirements do not mandate database separation and operating complexity is substantially higher.
- Custom tenant master replacing Company: rejected because it duplicates ERPNext's enterprise boundary and weakens standard integration.

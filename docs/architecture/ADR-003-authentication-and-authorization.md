# ADR-003: Same-Origin Sessions and Server Authorization

Status: Accepted
Date: 2026-09-14

## Context

The Vue client needs Frappe authentication without exposing API credentials or trusting browser-selected LGA context.

## Decision

Use secure same-origin Frappe session cookies where practical. Do not store API secrets, passwords, or long-lived bearer credentials in local storage. The server derives the caller, roles, permitted Companies, and active-LGA eligibility for every request.

Frontend route guards and menus are usability controls only. Backend permission checks remain authoritative for resources, service methods, workflows, reports, exports, and files.

## Consequences

- Production frontend and APIs should share an origin or a tightly controlled reverse proxy.
- CSRF, cookie security, session expiry, logout, and unauthorized responses need integrated tests.
- Requested Company filters are intersected with server-authorized Companies.
- Privileged, failed, and cross-LGA access events are audited.

## Rejected alternatives

- Browser-stored API keys: rejected due to theft and lifecycle risk.
- Client-only role checks: rejected because requests can bypass the interface.

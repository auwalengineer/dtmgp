# ADR-002: Separate Vue 3 Frontend

Status: Accepted
Date: 2026-09-14

## Context

Operational users need a focused, responsive interface for dashboards, forms, approvals, and role-specific navigation. Frappe Desk remains useful for restricted technical administration but is not the primary user experience.

## Decision

Use Vue 3 with TypeScript and Vite in `lg-dtmgp-web`. Use Vue Router for navigation, Pinia for durable client/session state, TanStack Query for server state, Zod for boundary validation, and an accessible shared component layer.

## Consequences

- The frontend can evolve independently while using stable versioned Frappe APIs.
- Authentication and authorization contracts must be explicit.
- Domain DTOs and runtime validation reduce accidental exposure of unrestricted DocType fields.
- CI must type-check, test, build, and verify hashed assets.
- Frappe Desk remains available only to approved administrative roles.

## Rejected alternatives

- Frappe Desk as the primary UI: rejected because it does not provide the intended task-focused cross-domain experience.
- React: rejected because the delivery team already has Vue experience and no project requirement justifies switching.

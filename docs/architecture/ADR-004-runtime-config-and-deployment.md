# ADR-004: Runtime Configuration and Immutable Frontend Deployment

Status: Accepted
Date: 2026-09-14

## Context

The frontend must move through development, staging, and production without stale application shells or environment-specific rebuilds.

## Decision

Build content-hashed assets with Vite. Use environment files for build mode and a non-secret `runtime-config.json` for deploy-time endpoints and environment labels. Deploy each build to a versioned directory and atomically switch the active release.

Serve HTML, runtime configuration, version metadata, manifests, and future service-worker metadata with revalidation or `no-cache`. Serve content-hashed assets with a one-year immutable cache policy. Do not introduce a service worker until offline behavior and updates are approved.

## Consequences

- The same immutable artifact can be promoted after staging validation.
- Runtime configuration must never contain secrets.
- CI verifies every asset referenced by `index.html` exists and is hashed.
- Deployments publish build version, commit, and build time and preserve the previous release for rollback.

# ADR-001 — Review UI: HTMX over React

- **Status:** Accepted
- **Date:** 2026-06-25

## Context

The spec leaves the HITL review UI framework to us ("React or HTMX — your call, justify it").
The UI is a table of issues with diff view and approve/reject/bulk actions — server-driven CRUD.

## Decision

Use **HTMX + Jinja2** served by the same FastAPI process.

## Rationale

- No Node toolchain, no separate build/deploy — `docker compose up` serves everything from one
  Python service, keeping the "demo in one command" promise small and reproducible.
- The interactions (table, filters, approve/reject, bulk-by-confidence) are classic
  server-rendered fragments; HTMX handles them without client state management.
- Smaller deliverable surface and fewer dependencies to keep at 100% discipline.

## Consequences

- Rich client-only interactions (drag-drop, offline) would be harder — not needed for v1.
- Frontend is excluded from the 100% unit-coverage gate (it is integration/e2e tested instead).

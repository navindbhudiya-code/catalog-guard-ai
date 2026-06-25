# ADR-000 — Context and engineering standards

- **Status:** Accepted
- **Date:** 2026-06-25

## Context

CatalogGuard AI is a public OSS portfolio piece: a LangGraph multi-agent auditor for Magento 2
catalogs. Because it will be promoted in agency communities and reviewed by hiring managers, the
build process itself is part of the product. The owner asked for four guarantees on top of the
functional spec: traceability, build verification, maintained logs, and 100% tested core.

## Decision

We adopt the following standards from commit zero:

1. **TDD** for all core logic (`superpowers:test-driven-development`).
2. A single **`make verify`** gate — ruff → mypy --strict → byte-compile → import-linter → pytest
   (`fail_under = 100` on core) → traceability check — required green before every commit and in CI.
3. **Requirement traceability**: a stable set of requirement IDs maps to component → test → eval in
   `docs/TRACEABILITY.md`; `make trace` fails the build if a requirement has no passing test.
4. **Structured logging** (`structlog`) to `logs/run-<id>.jsonl` plus a token-cost ledger, and a
   human-readable `docs/build-log.md` appended each phase.
5. **One ADR per architectural decision.**

## Consequences

- Slower first commit, much cheaper change later: refactors are safe behind the gate.
- The repo is auditable end-to-end — a reviewer can trace any requirement to the test that proves it.
- Coverage at 100% on core forces small, testable units and dependency injection.

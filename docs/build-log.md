# Build Log

Human-readable trail of the build itself — appended at the end of every phase. Records what was
built, the commands run, test/coverage numbers, eval scorecard deltas, and open follow-ups.

---

## Phase 0 — Project governance — 2026-06-25

**Built**
- `git init` at `app/code/NavinDBhudiya/CatalogGuard/`; Python 3.11 venv.
- Project scaffold: `src/catalogguard/{models,magento_client,providers,agents,graph,rules,logging,storage}`, `api/`, `ui/`, `evals/`, `tests/`, `docs/`, `docker/`, `.github/workflows/`.
- Quality gates: `pyproject.toml` (ruff, mypy --strict, pytest, coverage `fail_under=100` scoped to core, import-linter layered contract).
- `Makefile` with the single `make verify` gate (lint → type → compile → imports → test → trace).
- Governance docs: `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, `LICENSE` (MIT), `.env.example`.
- Traceability: `docs/TRACEABILITY.md` (15 requirement IDs) + machine-checker `catalogguard.tools.trace_check` (`make trace`).
- ADRs: ADR-000 (standards), ADR-001 (HTMX review UI).

**Commands / results**
- `make verify` → **green**: ruff ✓, mypy --strict ✓ (11 files), compileall ✓, import-linter ✓ (1 contract kept), pytest **21 passed**, coverage **100.00%** (fail_under=100), trace ✓.
- CI workflow (`.github/workflows/ci.yml`) runs `make verify` on push/PR. Pre-commit hooks wired.

**Follow-ups**
- Phase 1 (next): Magento REST client (auth/pagination/backoff/retry) + ExtractorAgent → SQLite, `catalogguard extract`, structlog wiring. Flip R-EXTRACT to `done` when its tests land.

---

## Phase 1a — Shared typed models (R-STATE) — 2026-06-25

**Built (TDD, test-first throughout)**
- `src/catalogguard/models/`: `Product` (+ `from_magento` mapper, `is_enabled`, non-negative price validator), `Issue`, `FixProposal` (confidence∈[0,1], `is_approved`), `AuditReport` (count aggregations), `AuditConfig` (`should_run`), `GraphState` (`record_tokens`, idempotent `mark_agent_done`), enums (`Dimension`, `Severity`, `DetectedBy`, `ProposalStatus`).
- `tests/unit/test_models.py` — 13 tests covering validators, mappers, aggregations.

**Commands / results**
- `make verify` → **green**, **21 passed**, **100.00%** coverage.
- Traceability: R-STATE flipped to `done`; `make trace` → 2 done requirements, all test-backed.

**Gate:** STOP for review — model definitions + GraphState schema presented for sign-off before the Magento client lands (per spec "show me the models, wait for approval"). **Approved.**

---

## Phase 1b — Foundation: client, cache, logging, extractor (R-EXTRACT) — 2026-06-25

**Built (TDD, test-first throughout)**
- `config.py` — `Settings` + `load_settings(env)` (env-driven; fails loud on missing base URL).
- `storage/cache.py` — `ProductCache` (SQLite): upsert/get/all/count + resumable `get_cursor`/`set_cursor` checkpoint table.
- `logging/` — `configure_logging(run_id, dir)` → structlog JSON lines to `logs/run-<id>.jsonl`, every record stamped with `run_id`.
- `magento_client/` — `MagentoClient`: bearer-token auth, `searchCriteria` pagination, tenacity retry/backoff on 429+5xx, fail-fast on non-retryable errors; HTTP layer injectable for hermetic tests.
- `agents/extractor.py` — `ExtractorAgent`: page-checkpointed, resumable extraction; idempotent upserts; `max_products` cap; structured logs per page.
- `cli.py` + `__main__.py` — `python -m catalogguard extract` (typer), `.env` loader, wires settings→client→cache→extractor.

**Commands / results**
- `make verify` → **green**: ruff ✓, mypy --strict ✓, compileall ✓, import-linter ✓, pytest **41 passed**, coverage **100.00%**, trace ✓ (3 done reqs).
- End-to-end smoke (mocked Magento, no live store): `extract` → 1 product mapped + cached + JSON log line written with `run_id`. CLI `--help` lists the `extract` subcommand.

**Notes**
- Live extraction against `https://app.demo.test` needs a Magento integration access token in `.env` (`MAGENTO_ACCESS_TOKEN`); unit tests never require it (recorded fixtures / mock transport).

**Gate:** STOP for review — Phase 1 foundation complete. Next: Phase 2 (rules + Sanity/Attribute/Duplicate agents + LangGraph Supervisor + SQLite checkpointer).

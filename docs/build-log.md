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

---

## Phase 2 — Rule agents + Supervisor + checkpointing — 2026-06-25

**Built (TDD, 100% core)**
- `rules/` — sanity (zero price/categories, special>regular, enabled+zero-stock) and attribute (missing required, placeholders, missing images/weight) rule sets + `base.issue` helper.
- `agents/` — `SanityAgent`, `AttributeAgent` (rules-first via `RuleAgent`), `DuplicateAgent` (exact text + near via `SimilarityIndex`), `registry.build_agents`.
- `providers/similarity.py` — `InMemorySimilarityIndex` (token-cosine, zero-dep default) + protocol for a ChromaDB drop-in.
- `graph/supervisor.py` — native `Supervisor` runs requested checks, accumulates issues, checkpoints; skips completed agents on resume.
- `storage/checkpoint.py` — `AuditCheckpoint` (SQLite) GraphState persistence.
- `reporting.py` — `build_report` + `render_markdown`. CLI `audit` command → `report.json` + `report.md`.
- ADR-002 (native orchestrator + pluggable similarity).

**Results**
- `make verify` → **green**, **78 passed**, **100.00%** coverage, trace ✓ (8 done requirements).
- End-to-end: seeded 2-product cache → `catalogguard audit --checks sanity,attributes,duplicates` → 6 issues, JSON+md reports written.
- Crash-resume proven by `test_checkpoint_resume.py` (agent crashes mid-audit; resume skips completed agent, no duplicate issues).

---

## Phase 3 — LLM agents + provider abstraction + evals — 2026-06-25

**Built (TDD, 100% core)**
- `providers/base.py` (LLMProvider protocol) + `providers/stub.py` (offline deterministic provider). Real `claude.py`/`bedrock.py`/`factory.py` (structured tool-use) added as `[llm]`-extra glue (coverage-omitted).
- `agents/content.py` — `ContentAgent` (LLM scoring, structured output, rules-before-LLM skip on empty description, records tokens).
- `rules/seo.py` + `agents/seo.py` — SEO rules (missing/long meta, url key, thin content) + cross-product duplicate-meta detection.
- `agents/fix_proposal.py` — `FixProposalAgent` consolidates fixable issues into FixProposals with confidence via the provider.
- `logging/cost.py` — `CostLedger` (per-agent tokens + $ estimate).
- `evals/` core — `synthetic.generate_catalog` (ground truth) + `scoring` (precision/recall/F1 + markdown scorecard). Runner `evals/score.py` (--write/--check-baseline). `graph/langgraph_adapter.py` optional StateGraph wrapper.
- ADR-002 covers orchestration/similarity. Registry extended with `seo` + provider-gated `content`.

**Results**
- `make verify` → **green**, **104 passed**, **100.00%** coverage, trace ✓ (13 done requirements).
- Eval scorecard on synthetic catalog: **1.00 precision/recall/F1** for sanity, attribute, duplicate, seo. Baseline committed; CI runs `evals/score.py --check-baseline` as an F1 gate.

---

## Phase 4 — HITL review + Apply + rollback — 2026-06-25

**Built (TDD, 100% core)**
- `storage/approval.py` — `ApprovalStore` (SQLite): save/query by status, set_status, edit-then-approve, bulk-approve-by-confidence, persistence.
- `storage/rollback.py` — `RollbackJournal` (SQLite): records previous value per change; `entries`/`mark_reverted`.
- `agents/apply.py` — `ApplyAgent`: applies only APPROVED proposals, journals before writing, `revert(batch)` restores prior values via a `CatalogWriter` protocol.
- `magento_client` — `update_field` (PUT) maps native fields vs custom_attributes; tested with mock transport.
- `api/app.py` — FastAPI + HTMX review UI (table, approve/reject/edit, bulk-approve). SRI on CDN script. `[api]` extra glue; opt-in integration test.
- CLI: `propose`, `serve`, `apply`, `rollback` close the loop.

**Results**
- `make verify` → **green**, **115 passed, 1 skipped** (integration), **100.00%** coverage, trace ✓ — **all 15 requirements done**.
- End-to-end offline loop verified: audit → 2 proposals → approve → apply (writes generated meta title) → rollback (restores prior value).

---

## Phase 5 — Magento admin module (NavinDBhudiya\CatalogGuard) — 2026-06-25

**Built**
- Module skeleton at the repo root: `registration.php`, `composer.json` (navindbhudiya/module-catalogguard), `etc/module.xml`, `etc/acl.xml`, `etc/adminhtml/{routes.xml,menu.xml,system.xml}`, `etc/config.xml`.
- `Model/PythonService.php` — Curl client to the Python service (`/audit`, `/report/latest`); base URL from store config.
- `Controller/Adminhtml/Audit/Index.php` (admin page) + `Run.php` (proxies Run Audit).
- `Block/Adminhtml/Audit/Report.php` + `view/adminhtml/templates/audit/report.phtml` — issues grid + "Run Audit" button (escaped output).
- Python API extended with `/audit` and `/report/latest` so the module integrates against a real service.

**Results**
- `php -l` clean on all PHP files; all module XML well-formed (`xmllint`).
- `make verify` → **green**, 115 passed + 1 integration skipped, **100.00%** core coverage, trace ✓ (15/15 requirements).

---

## Phase 6 — Docs + deliverable + release — 2026-06-25

**Built**
- `docker/docker-compose.yml` + `Dockerfile` (Python service + ChromaDB; `default_app` factory).
- `docs/USER_GUIDE.md` (full workflow), polished `README.md` (commands, scorecard, roadmap), `docs/good-first-issues.md` (5 starter tasks), `docs/DELIVERABLE.md` (final report).

**Final state**
- `make verify` → **green**: 115 passed + 1 integration skipped, **100.00%** core coverage, **15/15** requirements traced.
- Eval scorecard: 1.00 P/R/F1 (sanity/attribute/duplicate/seo). Tagged **v0.1.0**.

---

## Live run fix — Product.from_magento extension_attributes/media — 2026-06-26

**Found by a real audit against app.demo.test (2,040 Luma products).** The Magento product
endpoint nests categories under `extension_attributes.category_links`, stock under
`extension_attributes.stock_item`, and images under `media_gallery_entries` — the v0.1 mapper
only read flat `categories`/`images`, inflating `zero_categories`/`missing_images` to 100%.

**Fix (TDD):** `Product.from_magento` now maps category_links → categories, stock_item.qty →
stock_qty, media_gallery_entries → images. 117 tests, 100% coverage. Re-audit dropped sanity
issues 2,189 → 149 (false `zero_categories` eliminated).

---

## Configurable-product rule refinements (from live audit) — 2026-06-26

**Driven by the app.demo.test audit.** Variant/parent structure produced expected-but-noisy findings.
Refinements (TDD):
- `Product`: added `id` + `variant_child_ids` (from `extension_attributes.configurable_product_links`).
- `zero_price`, `missing_images`, `missing_weight`: exempt composite parent types (configurable/grouped/bundle) — price/images/weight live on child variants.
- `DuplicateAgent`: family-aware — skips exact/near duplicate pairs within the same variant family (parent↔child and sibling↔sibling).

**Live re-audit impact (2,040 products):** total issues **13,948 → 5,998**; duplicates **5,447 → 27**
(now genuine cross-product copy duplication); sanity false positives eliminated; missing_weight 192 → 44.
123 tests, 100% core coverage, 15/15 requirements.

---

## v0.1.1 — Embedded "Review Fixes" admin grid — 2026-06-26

**Built** an in-admin review queue so merchants manage fixes without leaving Magento:
- Python: `GET /proposals` (paged items+totalRecords) + `POST /api/proposals/{id}/approve|reject` + `/api/proposals/bulk-approve` JSON endpoints.
- Magento UI-component grid `catalogguard_review_listing` backed by a service-fed `ReviewDataProvider` (no DB table); columns SKU/Field/Proposed Value/Confidence/Status; mass-action Approve/Reject proxying server-side to the service; "Review Fixes" menu + ACL `NavinDBhudiya_CatalogGuard::review`.
- Approve-in-queue-only: write-back stays the explicit, journaled `apply` step.

**Verified live (app.demo.test):** grid renders 4,080 proposals (204 pages) with real generated meta values; **Actions → Approve** on 2 rows → "2 fix proposal(s) approved", count 4,080 → 4,078. `make verify` green (125 tests, 100% core). Screenshots 11–12 in `.claude/CatalogGuard-demo/`.

---

## v0.1.2 — Wire Run Audit ↔ Review Fixes — 2026-06-27

**Built** a one-click audit→fixes→review flow inside the admin:
- Core: `HeuristicProvider` (offline, deterministic meta/description generation — tested) + factory support; `ApprovalStore.clear()`.
- Python: `POST /propose` (clear → audit → FixProposalAgent → save) using the heuristic provider by default.
- Magento: `PythonService.generateProposals`; `Review/Generate` controller (JSON + redirect); a **"Generate Fixes"** button and **"Open Review Queue"** link on the audit page; clicking Generate runs `/propose` then redirects to the Review grid.

**Verified live:** audit page → Generate Fixes → 4,080 proposals generated → auto-redirect to the populated Review queue. `make verify` green (131 tests, 100% core). Screenshot 13 added.

---

## v0.1.3 — Apply Approved + Rollback admin actions — 2026-06-27

**Built** the write-back step as admin actions (paired so it stays reversible):
- Core: `RollbackJournal.latest_batch()` (TDD).
- Python: `POST /apply` (apply APPROVED via the configured `CatalogWriter` + journal, mark APPLIED) and `POST /rollback` (revert latest batch). `create_app` gains `writer` + `journal_db`; `serve_demo` wires a real `MagentoClient` from `.env`.
- Magento: `PythonService.applyApproved/rollbackLast`; `Review/Apply` + `Review/Rollback` controllers (JSON); an **Apply Approved** / **Rollback Last Batch** action bar above the Review grid.

**Tested:** `/apply`→`/rollback` round-trip proven offline via integration tests (fake writer: applies the value, journals the previous, rollback restores). `make verify` green (133 tests + integration, 100% core).

**Note:** the live admin browser test + screenshot is pending — `app.demo.test`'s HTTPS frontend went unreachable (Warden containers up, traefik/varnish not responding); environment issue, not code. The `.env` Magento token was blanked during a failed re-mint while the store was down and must be re-minted once it recovers.

# CLAUDE.md — CatalogGuard AI

Guidance for Claude Code when working in `app/code/NavinDBhudiya/CatalogGuard/`. These
instructions are scoped to **this module/repo only** and OVERRIDE broader defaults here.

## What this is

CatalogGuard AI is a **LangGraph multi-agent system (Python 3.11+)** that audits a live
Magento 2 / Adobe Commerce catalog across 5 dimensions, proposes fixes, and applies
**only human-approved** fixes with a rollback journal. It is a public OSS portfolio piece —
engineering discipline (traceability, build verification, logging, tests) is a first-class
requirement, not an afterthought.

Full spec: `../../../.claude/docs/magento-ai-catalog-toolkit-build-prompt.md`.

## Locked decisions

| Topic | Decision |
|------|----------|
| Repo location | This dir, its own `git` repo (sibling to `AiProductContent`). |
| Cadence | Build phase-by-phase; STOP for review at each phase gate. |
| Coverage | **100% line+branch on core** (`src/catalogguard` models/rules/client/providers/agents/graph/storage). Glue (`cli.py`, `api/`, `ui/`) omitted via coverage config. |
| Test store | Existing `https://app.demo.test` (Warden). Live tests are `@pytest.mark.integration`, opt-in via env. |
| LLM provider | Claude API default (latest Claude model) behind a provider abstraction; AWS Bedrock is a config flag. |
| Review UI | HTMX (no Node build step) — see `docs/decisions/`. |

## Non-negotiable rules (the user's explicit asks)

1. **TDD always.** No production code without a failing test first. `superpowers:test-driven-development`.
2. **`make verify` must pass before every commit.** It runs: ruff → mypy --strict → compileall → import-linter → pytest(100% core) → traceability check. This is the "compilated"/build-verified gate.
3. **100% core coverage.** The coverage gate is `fail_under = 100`; do not lower it. If glue genuinely can't be unit-tested, add it to `[tool.coverage.run] omit`, not to the threshold.
4. **Everything is traceable.** Every requirement ID (`R-DUP`, `R-ATTR`, `R-CONTENT`, `R-SEO`, `R-SANITY`, `R-STATE`, `R-SUPERVISOR`, `R-CHECKPOINT`, `R-PROVIDER`, `R-ROLLBACK`, `R-HITL`, `R-EVAL`, `R-COST`) appears in `docs/TRACEABILITY.md` mapped to component → test → eval → ADR. `make trace` fails the build if a requirement has no passing test.
5. **Maintain logs.** Runtime: `structlog` JSON to `logs/run-<id>.jsonl` (stamp `run_id`, `agent`, `sku`, `phase`) + a token-cost ledger. Build: append to `docs/build-log.md` at the end of every phase (what was built, commands, test/coverage numbers, scorecard delta, follow-ups).
6. **Conventional commits with requirement IDs**, e.g. `feat(seo): meta-length audit [R-SEO]`.
7. **LLM calls use structured outputs only** (tool use / JSON schema). Never free-text parse.
8. **Rules before LLM.** A regex/threshold check must run before spending any token; log estimated token cost per audit.
9. **No store writes without approval.** `ApplyAgent` only ever consumes items in `APPROVED` state, and always writes a rollback journal entry first.
10. **One ADR per key architectural decision** in `docs/decisions/`.

## Environment & secrets

- Python 3.11 venv at `.venv` (`make install`). Activate via the `make` targets (they call `.venv/bin/python`).
- Secrets live in `.env` (gitignored); template in `.env.example`. Needed: `MAGENTO_BASE_URL`, `MAGENTO_ACCESS_TOKEN` (admin integration token), `ANTHROPIC_API_KEY`, optional `LANGSMITH_API_KEY`, Bedrock vars.
- Never commit `.env` or real tokens. The Magento base URL for dev is `https://app.demo.test`.

## Common commands

```bash
make install     # set up venv + dev deps
make verify      # full gate — run before committing
make test        # tests + 100% core coverage
make audit ARGS="--checks sanity,attributes,duplicates"
```

## Phase gates (stop after each)

- **P0 governance:** scaffold + gates green on empty project.
- **P1 foundation:** pydantic models (approval-gated) + Magento client + ExtractorAgent → `catalogguard extract`.
- **P2 rule agents + graph:** Sanity/Attribute/Duplicate + LangGraph Supervisor + SQLite checkpointer (resumable).
- **P3 LLM agents + evals:** Content/SEO/FixProposal + provider abstraction + synthetic generator + scorecard + CI F1 gate.
- **P4 HITL + Apply:** FastAPI + HTMX review UI + ApplyAgent + rollback + end-to-end demo.
- **P5 PHP module:** Magento admin grid + Run-Audit button; `setup:di:compile` clean; tag `v0.1.0`.

## When exploring the parent Magento repo

The parent project has a `code-review-graph` MCP graph — prefer it over Grep/Glob for the
Magento store code. For *this* Python module, normal file tools are fine.

# Requirement Traceability Matrix

Every requirement maps to the component that implements it, the test(s) that prove it, the
eval/benchmark that measures it, and the ADR that justifies design choices.

**Machine-checked:** `make trace` parses this table. For every row whose **Status** is `done`,
the **Tests** cell must reference at least one test file that exists on disk. A `done` requirement
with no resolvable test fails the build. `planned` rows are listed but not yet gated.

Requirement IDs are stable; see `.claude/docs/magento-ai-catalog-toolkit-build-prompt.md` for the
source spec.

| Req ID | Description | Component | Tests | Eval | ADR | Status |
|--------|-------------|-----------|-------|------|-----|--------|
| R-STATE | Typed shared state: Product, Issue, FixProposal, AuditReport, GraphState | `src/catalogguard/models/` | `tests/unit/test_models.py` | — | ADR-000 | done |
| R-EXTRACT | Magento REST client (auth, pagination, rate-limit backoff, retry) + ExtractorAgent → SQLite cache | `src/catalogguard/magento_client/`, `src/catalogguard/agents/extractor.py` | `tests/unit/test_magento_client.py`, `tests/unit/test_extractor.py` | cost/latency | ADR-000 | done |
| R-SANITY | Category/price/stock rule checks (pure rules, no LLM) | `src/catalogguard/rules/`, `src/catalogguard/agents/sanity.py` | `tests/unit/test_rules_sanity.py` | precision/recall | — | planned |
| R-ATTR | Missing/malformed attribute validation (rules + LLM) | `src/catalogguard/agents/attribute.py` | `tests/unit/test_attribute.py` | precision/recall | — | planned |
| R-DUP | Duplicate / near-duplicate detection via ChromaDB embeddings | `src/catalogguard/agents/duplicate.py` | `tests/unit/test_duplicate.py` | precision/recall | — | planned |
| R-SUPERVISOR | LangGraph StateGraph + Supervisor selects agents from audit config | `src/catalogguard/graph/` | `tests/unit/test_graph.py` | — | — | planned |
| R-CHECKPOINT | Resumable audit via LangGraph checkpointer + SQLite | `src/catalogguard/graph/`, `src/catalogguard/storage/` | `tests/unit/test_checkpoint_resume.py` | — | — | planned |
| R-CONTENT | LLM-scored description quality + proposed rewrites (structured output) | `src/catalogguard/agents/content.py` | `tests/unit/test_content.py` | Ragas faithfulness | — | planned |
| R-SEO | Meta/url/alt-text audit + generated fixes (structured output) | `src/catalogguard/agents/seo.py` | `tests/unit/test_seo.py` | precision/recall | — | planned |
| R-PROVIDER | LLM provider abstraction Claude ↔ Bedrock (config flag) + LangSmith tracing | `src/catalogguard/providers/` | `tests/unit/test_providers.py` | — | — | planned |
| R-ROLLBACK | ApplyAgent writes only APPROVED fixes + rollback journal (one-command revert) | `src/catalogguard/agents/apply.py`, `src/catalogguard/storage/rollback.py` | `tests/unit/test_rollback.py` | — | — | planned |
| R-HITL | FastAPI review API + HTMX UI, approval state in SQLite | `api/`, `ui/`, `src/catalogguard/storage/` | `tests/integration/test_review_api.py` | — | ADR-001 | planned |
| R-EVAL | Synthetic broken-catalog generator + precision/recall/F1 scorecard + CI gate | `evals/` | `tests/unit/test_evals.py` | scorecard | — | planned |
| R-COST | Per-agent token + wall-clock cost tracking, logged | `src/catalogguard/logging/` | `tests/unit/test_cost_ledger.py` | cost/latency | — | planned |
| R-TRACE | Traceability matrix is machine-checked in the build gate | `src/catalogguard/tools/trace_check.py` | `tests/unit/test_trace_check.py` | — | ADR-000 | done |

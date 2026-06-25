# ADR-002 — Native orchestrator + pluggable similarity index

- **Status:** Accepted
- **Date:** 2026-06-25

## Context

The spec fixes LangGraph for orchestration and ChromaDB for duplicate-detection
embeddings. Both are heavy dependencies. Our standards (ADR-000) require the core
test suite to be hermetic and 100%-covered, and the project to be demoable in one
command without paid embedding APIs.

## Decision

1. **Orchestration:** a native `Supervisor` is the tested engine. It runs the agents
   named in `config.checks`, accumulates issues into `GraphState`, and checkpoints to
   SQLite (`AuditCheckpoint`) after each agent — giving real, unit-tested crash-resume
   (`completed_agents` is the resume key). A LangGraph `StateGraph` adapter that wraps
   these same agent callables for tracing is added in Phase 3, when the `[llm]` extra
   (and thus langgraph) is installed and can be integration-tested properly.

2. **Similarity:** `DuplicateAgent` depends on a `SimilarityIndex` protocol. The default
   `InMemorySimilarityIndex` (token-cosine, zero deps) makes duplicate detection work out
   of the box and in CI. A ChromaDB embedding index is a drop-in implementation provided
   under the `[llm]` extra for higher-recall near-duplicate detection.

## Consequences

- The resumability requirement (R-CHECKPOINT) is satisfied and tested today, without
  depending on LangGraph's checkpointer API surface.
- Heavy deps (langgraph, chromadb) stay optional; `make verify` runs fast and offline.
- We honor the fixed stack by adding LangGraph/ChromaDB as adapters over the same
  interfaces, rather than substituting them away.

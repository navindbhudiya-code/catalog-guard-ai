# Contributing to CatalogGuard AI

Thanks for your interest! This project holds itself to production standards.

## Ground rules

1. **TDD.** Write a failing test first, watch it fail, then write minimal code. No production code without a test.
2. **`make verify` must be green** before you push or open a PR. It runs ruff, mypy --strict, byte-compile, the import-layering contract, the test suite at **100% core coverage**, and the traceability check.
3. **Conventional commits** with a requirement ID where applicable, e.g. `feat(seo): add meta-length audit [R-SEO]`.
4. **Trace your work.** If you add behavior tied to a requirement, update `docs/TRACEABILITY.md` (component → test → eval). New architectural decision? Add an ADR under `docs/decisions/`.
5. **No store writes without approval.** Anything that mutates a Magento store must go through the review queue and write a rollback-journal entry.

## Setup

```bash
make install   # creates .venv with dev deps
cp .env.example .env
make verify
```

## Project layout

See `CLAUDE.md` and `README.md`. Core logic lives in `src/catalogguard/`; tests in `tests/`;
the eval harness in `evals/`.

## Good first issues

Check the issues labeled `good first issue` — they're scoped and have pointers to the relevant code.

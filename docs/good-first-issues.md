# Good First Issues

Pre-seeded, well-scoped tasks for new contributors. Each keeps the project's bar:
TDD, `make verify` green, 100% core coverage, and a traceability entry where relevant.

### 1. Add a `missing_alt_text` SEO rule  `good first issue`
Flag products whose images lack alt text. Add a rule in `src/catalogguard/rules/seo.py`
and a paired test. Pointers: follow `thin_content` as a template; register in `SEO_RULES`.

### 2. Add `--min-confidence` to the `apply` CLI  `good first issue`
Let users apply only proposals above a confidence threshold without opening the UI.
Touch `src/catalogguard/cli.py` (`apply`) and `ApprovalStore.by_status`.

### 3. CSV export of an audit report  `good first issue`
Add `render_csv(report)` next to `render_markdown` in `src/catalogguard/reporting.py`
with a test; wire a `--format csv` flag into `audit`.

### 4. ChromaDB similarity index implementation  `good first issue` `help wanted`
Implement `providers/chroma_index.py` satisfying the `SimilarityIndex` protocol so
`DuplicateAgent` can use embeddings. Add an integration test behind the `[llm]` extra.

### 5. Ragas fix-quality eval  `good first issue`
Add `evals/fix_quality.py` scoring generated descriptions for faithfulness/length with
Ragas, and surface the numbers in the README scorecard.

---

**Before opening a PR:** `make verify` must be green and any new requirement must appear in
`docs/TRACEABILITY.md`. See `CONTRIBUTING.md`.

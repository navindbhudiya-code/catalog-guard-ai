# CatalogGuard AI — User Guide

A practical, end-to-end guide to auditing a Magento 2 catalog and applying AI-proposed
fixes with human approval and one-command rollback.

---

## 1. Concepts

| Term | Meaning |
|------|---------|
| **Audit** | Read-only scan of the catalog across 5 dimensions producing **Issues**. |
| **Issue** | One detected problem on one product (e.g. `missing_meta_title` on `TS-01`). |
| **Fix proposal** | A suggested new field value for an issue, with a confidence score. Nothing is written until approved. |
| **Review queue** | The list of pending proposals you approve/reject/edit. |
| **Apply** | Writes APPROVED proposals to Magento, journaling the previous value. |
| **Rollback** | Restores the previous values of an applied batch in one command. |

Two principles run through everything:
- **Rules before LLM** — cheap deterministic checks run first; tokens are only spent where needed.
- **No store writes without approval** — `ApplyAgent` only ever touches `APPROVED` proposals.

---

## 2. Install

```bash
cd app/code/NavinDBhudiya/CatalogGuard
make install          # creates .venv (Python 3.11) with dev deps
cp .env.example .env  # then edit .env (see below)
make verify           # lint + types + compile + 100% tests — should print all green
```

`.env` keys:

```ini
MAGENTO_BASE_URL=https://app.demo.test
MAGENTO_ACCESS_TOKEN=<admin integration token>   # System > Integrations
MAGENTO_VERIFY_SSL=false                          # local self-signed certs
CATALOGGUARD_LLM_PROVIDER=claude                  # claude | bedrock | stub
ANTHROPIC_API_KEY=<your key>                      # only for provider=claude
```

> No Anthropic key handy? Set `CATALOGGUARD_LLM_PROVIDER=stub` to run the whole loop offline
> (content checks find nothing and fixes generate empty values, but every command works).

---

## 3. The workflow

### Step 1 — Extract the catalog

```bash
python -m catalogguard extract                 # full catalog
python -m catalogguard extract --max-products 50   # quick sample
```

Pulls products into `catalogguard.sqlite`. Resumable: if it crashes at page 300, rerun and it
continues from the last completed page. Structured logs land in `logs/run-<id>.jsonl`.

### Step 2 — Audit

```bash
python -m catalogguard audit --checks sanity,attributes,duplicates,seo
```

Writes `reports/report.json` and `reports/report.md`. Run a subset any time
(`--checks seo`). The audit is resumable via `--run-id <id>`.

Example `report.md`:

```
# CatalogGuard Audit Report
- Products scanned: 1,240
- Total issues: 318
### Issues by dimension
| Key | Count |
| seo | 142 |
| attribute | 96 |
...
```

### Step 3 — Generate fix proposals

```bash
python -m catalogguard propose --checks seo
```

Audits, then asks the LLM to generate corrected values for fixable issues (meta titles,
descriptions, rewrites) and loads them into `approvals.sqlite` as **pending**.

### Step 4 — Review (human in the loop)

```bash
python -m catalogguard serve         # http://127.0.0.1:8000
```

In the browser you can:
- See each pending fix (SKU, field, proposed value, confidence).
- **Approve** / **Reject** individually.
- **Bulk approve** everything at or above a confidence threshold (e.g. ≥ 0.90).

### Step 5 — Apply

```bash
python -m catalogguard apply --batch nightly-01
```

Writes only APPROVED proposals back to Magento. Every change is journaled with its previous
value in `rollback.sqlite`.

### Step 6 — Rollback (if needed)

```bash
python -m catalogguard rollback --batch nightly-01
```

Restores the previous value of every change in that batch.

---

## 4. What each audit dimension checks

- **sanity** — `zero_price`, `zero_categories`, `special_price_exceeds_regular`, `enabled_zero_stock`.
- **attribute** — `missing_required_attribute` (configure with `--required-attributes brand,color`), `placeholder_value` ("TBD", "lorem ipsum"), `missing_images`, `missing_weight`.
- **duplicate** — `exact_duplicate` (identical text), `near_duplicate` (similarity ≥ threshold).
- **seo** — `missing_meta_title/description`, `meta_*_too_long`, `missing_url_key`, `thin_content`, `duplicate_meta_title`.
- **content** *(LLM)* — `low_quality_description` (too short, keyword-stuffed, copied, wrong language/product).

---

## 5. Magento admin module

Installed at `app/code/NavinDBhudiya/CatalogGuard`:

```bash
bin/magento module:enable NavinDBhudiya_CatalogGuard
bin/magento setup:upgrade
bin/magento setup:di:compile
```

Then in admin: **Catalog → CatalogGuard AI**. Set the service URL under
**Stores → Configuration → Catalog → CatalogGuard AI**, click **Run Audit**, and review the
issues grid. The module talks to the Python service (`/audit`, `/report/latest`).

---

## 6. Evaluation & quality

```bash
python evals/score.py                  # print the precision/recall/F1 scorecard
python evals/score.py --check-baseline # CI gate: fail on any F1 regression
make verify                            # full build gate (100% core coverage)
```

The synthetic generator injects known defects so scores are measured against ground truth.

---

## 7. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `KeyError: MAGENTO_BASE_URL` | Set it in `.env` (CatalogGuard fails loud rather than audit the wrong store). |
| TLS errors against `app.demo.test` | `MAGENTO_VERIFY_SSL=false` for local self-signed certs. |
| `content` check errors | It needs a provider; set `CATALOGGUARD_LLM_PROVIDER` (or `stub` offline). |
| 429s from Magento | The client already backs off and retries; lower `--page-size` if persistent. |
| Want to undo an apply | `python -m catalogguard rollback --batch <id>`. |

"""FastAPI + HTMX review UI for the human-in-the-loop queue (R-HITL).

Single-process app serving an HTML table of pending fix proposals with
Approve / Reject / Edit and bulk-approve-by-confidence. Excluded from the
unit-coverage gate; covered by an opt-in integration test. See ADR-001.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

from fastapi import Body, FastAPI, Form
from fastapi.responses import HTMLResponse

from catalogguard.agents.registry import build_agents
from catalogguard.graph.supervisor import Supervisor
from catalogguard.models import AuditConfig, GraphState, ProposalStatus
from catalogguard.reporting import build_report
from catalogguard.storage.approval import ApprovalStore
from catalogguard.storage.cache import ProductCache


class _NullLogger:
    def info(self, event: str, **kw: object) -> None: ...


def _confidence_badge(confidence: float) -> str:
    level = "high" if confidence >= 0.85 else "med" if confidence >= 0.6 else "low"
    return f'<span class="conf conf-{level}">{confidence:.2f}</span>'


def _row(proposal_id: str, sku: str, field: str, value: str, confidence: float) -> str:
    safe_value = escape(str(value)) or '<em class="muted">— none generated —</em>'
    return f"""
    <tr id="p-{proposal_id}">
      <td class="sku">{escape(sku)}</td>
      <td><code>{escape(field)}</code></td>
      <td class="proposed">{safe_value}</td>
      <td>{_confidence_badge(confidence)}</td>
      <td class="actions">
        <button class="btn btn-approve" hx-post="/proposals/{proposal_id}/approve"
                hx-target="#p-{proposal_id}" hx-swap="outerHTML">Approve</button>
        <button class="btn btn-reject" hx-post="/proposals/{proposal_id}/reject"
                hx-target="#p-{proposal_id}" hx-swap="outerHTML">Reject</button>
      </td>
    </tr>"""


_STYLE = """
  :root { --bg:#f4f6fb; --card:#fff; --ink:#1f2430; --muted:#8a93a6; --line:#e6e9f0;
          --brand:#5b4bdb; --green:#1f9d55; --red:#d64545; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
  .wrap { max-width:1080px; margin:0 auto; padding:32px 24px; }
  header h1 { margin:0 0 4px; font-size:24px; }
  header p { margin:0 0 20px; color:var(--muted); }
  .toolbar { display:flex; align-items:center; gap:10px; background:var(--card);
             border:1px solid var(--line); border-radius:12px; padding:14px 16px; margin-bottom:18px; }
  .toolbar input { width:64px; padding:6px 8px; border:1px solid var(--line); border-radius:8px; }
  .btn { cursor:pointer; border:0; border-radius:8px; padding:7px 14px; font-weight:600; color:#fff; }
  .btn-bulk { background:var(--brand); }
  .btn-approve { background:var(--green); }
  .btn-reject { background:var(--red); margin-left:6px; }
  table { width:100%; border-collapse:separate; border-spacing:0; background:var(--card);
          border:1px solid var(--line); border-radius:12px; overflow:hidden; }
  thead th { text-align:left; font-size:12px; text-transform:uppercase; letter-spacing:.04em;
             color:var(--muted); background:#fafbfe; padding:12px 14px; border-bottom:1px solid var(--line); }
  tbody td { padding:11px 14px; border-bottom:1px solid var(--line); vertical-align:middle; }
  tbody tr:last-child td { border-bottom:0; }
  tbody tr:hover { background:#fafbff; }
  .sku { font-weight:700; }
  code { background:#eef0f7; padding:2px 6px; border-radius:6px; font-size:12px; }
  .proposed { color:#2b2f3a; }
  .muted { color:var(--muted); }
  .conf { font-weight:700; padding:2px 8px; border-radius:999px; font-size:12px; }
  .conf-high { background:#e3f6ec; color:var(--green); }
  .conf-med  { background:#fff4e0; color:#b9770b; }
  .conf-low  { background:#fde8e8; color:var(--red); }
  .actions { white-space:nowrap; }
"""


def _page(rows: str, total: int) -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>CatalogGuard Review</title>
<script src="https://unpkg.com/htmx.org@1.9.10"
        integrity="sha384-D1Kt99CQMDuVetoL1lrYwg5t+9QdHe7NLX/SoJYkXDFfX37iInKRy5xLSi8nO7UC"
        crossorigin="anonymous"></script>
<style>{_STYLE}</style></head>
<body><div class="wrap">
  <header>
    <h1>🛡️ CatalogGuard — Review Queue</h1>
    <p>{total} pending fix proposal(s). Nothing is written to the store until approved.</p>
  </header>
  <form class="toolbar" hx-post="/bulk-approve" hx-target="#queue" hx-swap="innerHTML">
    <span>Bulk approve all with confidence ≥</span>
    <input name="min_confidence" value="0.9"/>
    <button class="btn btn-bulk" type="submit">Approve high-confidence</button>
  </form>
  <table><thead>
    <tr><th>SKU</th><th>Field</th><th>Proposed value</th><th>Confidence</th><th>Action</th></tr>
  </thead><tbody id="queue">{rows}</tbody></table>
</div></body></html>"""


def create_app(
    store: ApprovalStore,
    *,
    cache_db: str = "catalogguard.sqlite",
    reports_dir: str = "reports",
    store_url: str = "https://app.demo.test",
) -> FastAPI:
    """Build the review app bound to an approval store.

    Also exposes ``/audit`` and ``/report/latest`` consumed by the Magento admin
    module (NavinDBhudiya\\CatalogGuard).
    """
    app = FastAPI(title="CatalogGuard Review")
    report_path = Path(reports_dir) / "report.json"

    @app.post("/audit")
    def run_audit(payload: dict[str, str] = Body(default={})) -> dict[str, object]:  # noqa: B008
        checks_raw = payload.get("checks", "sanity,attributes,duplicates,seo")
        aliases = {"attributes": "attribute", "duplicates": "duplicate"}
        checks = [aliases.get(c.strip(), c.strip()) for c in checks_raw.split(",") if c.strip()]
        cache = ProductCache(cache_db)
        try:
            products = cache.all()
        finally:
            cache.close()
        config = AuditConfig(store_url=store_url, checks=checks)
        state = GraphState(config=config, products=products)
        Supervisor(build_agents(config, checks), _NullLogger()).run(state)
        report = build_report(state, products_scanned=len(products))
        Path(reports_dir).mkdir(parents=True, exist_ok=True)
        report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return {"issues": report.issue_count, "products_scanned": report.products_scanned}

    @app.get("/report/latest")
    def latest_report() -> dict[str, object]:
        if not report_path.exists():
            return {}
        loaded: dict[str, object] = json.loads(report_path.read_text(encoding="utf-8"))
        return loaded

    # --- JSON API consumed by the Magento admin UI-component grid ---------

    @app.get("/proposals")
    def list_proposals(page: int = 1, limit: int = 50) -> dict[str, object]:
        pending = store.by_status(ProposalStatus.PENDING)
        start = max(0, (page - 1) * limit)
        window = pending[start : start + limit]
        items = [
            {
                "id": p.id,
                "sku": p.sku,
                "field": p.field,
                "current_value": "" if p.current_value is None else str(p.current_value),
                "proposed_value": str(p.proposed_value),
                "confidence": round(p.confidence, 2),
                "status": p.status.value,
            }
            for p in window
        ]
        return {"items": items, "totalRecords": len(pending)}

    @app.post("/api/proposals/{proposal_id}/approve")
    def api_approve(proposal_id: str) -> dict[str, object]:
        store.set_status(proposal_id, ProposalStatus.APPROVED)
        return {"success": True, "id": proposal_id, "status": "approved"}

    @app.post("/api/proposals/{proposal_id}/reject")
    def api_reject(proposal_id: str) -> dict[str, object]:
        store.set_status(proposal_id, ProposalStatus.REJECTED)
        return {"success": True, "id": proposal_id, "status": "rejected"}

    @app.post("/api/proposals/bulk-approve")
    def api_bulk_approve(payload: dict[str, float] = Body(default={})) -> dict[str, object]:  # noqa: B008
        approved = store.bulk_approve(float(payload.get("min_confidence", 0.9)))
        return {"success": True, "approved": approved}

    def render_queue() -> str:
        pending = store.by_status(ProposalStatus.PENDING)
        return "".join(
            _row(p.id, p.sku, p.field, str(p.proposed_value), p.confidence) for p in pending
        )

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        pending = store.by_status(ProposalStatus.PENDING)
        return _page(render_queue(), total=len(pending))

    @app.post("/proposals/{proposal_id}/approve", response_class=HTMLResponse)
    def approve(proposal_id: str) -> str:
        store.set_status(proposal_id, ProposalStatus.APPROVED)
        return f'<tr id="p-{proposal_id}"><td colspan="5">✅ approved</td></tr>'

    @app.post("/proposals/{proposal_id}/reject", response_class=HTMLResponse)
    def reject(proposal_id: str) -> str:
        store.set_status(proposal_id, ProposalStatus.REJECTED)
        return f'<tr id="p-{proposal_id}"><td colspan="5">🚫 rejected</td></tr>'

    @app.post("/proposals/{proposal_id}/edit", response_class=HTMLResponse)
    def edit(proposal_id: str, value: str = Form(...)) -> str:
        store.edit(proposal_id, value)
        return f'<tr id="p-{proposal_id}"><td colspan="5">✏️ edited &amp; approved</td></tr>'

    @app.post("/bulk-approve", response_class=HTMLResponse)
    def bulk_approve(min_confidence: float = Form(...)) -> str:
        store.bulk_approve(min_confidence)
        return render_queue()

    return app


def default_app() -> FastAPI:
    """Zero-arg factory for ``uvicorn api.app:default_app --factory``."""
    return create_app(ApprovalStore("approvals.sqlite"))

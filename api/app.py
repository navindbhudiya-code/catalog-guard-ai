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


def _row(proposal_id: str, sku: str, field: str, value: str, confidence: float) -> str:
    safe_value = escape(str(value))
    return f"""
    <tr id="p-{proposal_id}">
      <td>{escape(sku)}</td>
      <td>{escape(field)}</td>
      <td><pre>{safe_value}</pre></td>
      <td>{confidence:.2f}</td>
      <td>
        <button hx-post="/proposals/{proposal_id}/approve" hx-target="#p-{proposal_id}"
                hx-swap="outerHTML">Approve</button>
        <button hx-post="/proposals/{proposal_id}/reject" hx-target="#p-{proposal_id}"
                hx-swap="outerHTML">Reject</button>
      </td>
    </tr>"""


def _page(rows: str) -> str:
    return f"""<!doctype html>
<html><head><title>CatalogGuard Review</title>
<script src="https://unpkg.com/htmx.org@1.9.10"
        integrity="sha384-D1Kt99CQMDuVetoL1lrYwg5t+9QdHe7NLX/SoJYkXDFfX37iInKRy5xLSi8nO7UC"
        crossorigin="anonymous"></script></head>
<body>
  <h1>CatalogGuard — Pending Fixes</h1>
  <form hx-post="/bulk-approve" hx-target="#queue" hx-swap="innerHTML">
    Approve all with confidence ≥
    <input name="min_confidence" value="0.9" size="4"/>
    <button type="submit">Bulk approve</button>
  </form>
  <table border="1"><thead>
    <tr><th>SKU</th><th>Field</th><th>Proposed</th><th>Confidence</th><th>Action</th></tr>
  </thead><tbody id="queue">{rows}</tbody></table>
</body></html>"""


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

    def render_queue() -> str:
        pending = store.by_status(ProposalStatus.PENDING)
        return "".join(
            _row(p.id, p.sku, p.field, str(p.proposed_value), p.confidence) for p in pending
        )

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return _page(render_queue())

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

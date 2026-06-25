"""FastAPI + HTMX review UI for the human-in-the-loop queue (R-HITL).

Single-process app serving an HTML table of pending fix proposals with
Approve / Reject / Edit and bulk-approve-by-confidence. Excluded from the
unit-coverage gate; covered by an opt-in integration test. See ADR-001.
"""

from __future__ import annotations

from html import escape

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

from catalogguard.models import ProposalStatus
from catalogguard.storage.approval import ApprovalStore


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


def create_app(store: ApprovalStore) -> FastAPI:
    """Build the review app bound to an approval store."""
    app = FastAPI(title="CatalogGuard Review")

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

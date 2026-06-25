"""Command-line entrypoint: ``python -m catalogguard ...``.

Thin glue that wires settings → client → cache → extractor. Excluded from the
unit-coverage gate (it is exercised by the end-to-end extraction check).
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import typer

from catalogguard.agents.apply import ApplyAgent
from catalogguard.agents.extractor import ExtractorAgent
from catalogguard.agents.fix_proposal import FixProposalAgent
from catalogguard.agents.registry import build_agents
from catalogguard.config import load_settings
from catalogguard.graph.supervisor import Supervisor
from catalogguard.logging import configure_logging
from catalogguard.magento_client import MagentoClient
from catalogguard.models import AuditConfig, GraphState, ProposalStatus
from catalogguard.providers.factory import get_provider
from catalogguard.reporting import build_report, render_markdown
from catalogguard.storage.approval import ApprovalStore
from catalogguard.storage.cache import ProductCache
from catalogguard.storage.checkpoint import AuditCheckpoint
from catalogguard.storage.rollback import RollbackJournal

app = typer.Typer(help="CatalogGuard AI — Magento catalog auditor.")


@app.callback()
def _main() -> None:
    """CatalogGuard AI command group (keeps subcommands explicit, e.g. `extract`)."""


def _load_dotenv(path: str = ".env") -> None:
    file = Path(path)
    if not file.exists():
        return
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@app.command()
def extract(
    max_products: int | None = typer.Option(None, help="Cap products pulled (smoke tests)."),
    page_size: int = typer.Option(100, help="REST page size."),
    db: str = typer.Option("catalogguard.sqlite", help="SQLite cache path."),
) -> None:
    """Pull the catalog from Magento into the local SQLite cache."""
    _load_dotenv()
    settings = load_settings()
    run_id = uuid.uuid4().hex[:8]
    logger = configure_logging(run_id, "logs")

    client = MagentoClient(
        settings.magento_base_url,
        settings.magento_access_token,
        verify_ssl=settings.magento_verify_ssl,
    )
    cache = ProductCache(db)
    try:
        count = ExtractorAgent(client, cache, logger, page_size=page_size).extract(
            max_products=max_products
        )
        typer.echo(
            f"Extracted {count} products into {db} (run {run_id}). Cache total: {cache.count()}."
        )
    finally:
        client.close()
        cache.close()


@app.command()
def audit(
    checks: str = typer.Option(
        "sanity,attributes,duplicates",
        help="Comma-separated checks (sanity, attributes, duplicates).",
    ),
    db: str = typer.Option("catalogguard.sqlite", help="SQLite product cache to audit."),
    out_dir: str = typer.Option("reports", help="Directory for report.json + report.md."),
    required_attributes: str = typer.Option("", help="Comma-separated required attribute codes."),
    run_id: str | None = typer.Option(None, help="Resume a prior audit by run id."),
) -> None:
    """Audit the cached catalog and write JSON + markdown reports."""
    _load_dotenv()
    settings = load_settings()
    run = run_id or uuid.uuid4().hex[:8]
    logger = configure_logging(run, "logs")

    # Normalize friendly plural check names to dimension keys.
    aliases = {"attributes": "attribute", "duplicates": "duplicate"}
    selected = [aliases.get(c.strip(), c.strip()) for c in checks.split(",") if c.strip()]
    required = [a.strip() for a in required_attributes.split(",") if a.strip()]

    cache = ProductCache(db)
    checkpoint = AuditCheckpoint(Path(db).with_suffix(".checkpoint.sqlite"))
    try:
        products = cache.all()
        config = AuditConfig(
            store_url=settings.magento_base_url, checks=selected, required_attributes=required
        )
        state = checkpoint.load(run) or GraphState(config=config, products=products)
        agents = build_agents(config, selected)

        state = Supervisor(agents, logger, checkpoint=checkpoint, run_id=run).run(state)
        report = build_report(state, products_scanned=len(products))

        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
        (out / "report.md").write_text(render_markdown(report), encoding="utf-8")
        typer.echo(
            f"Audited {len(products)} products (run {run}); {report.issue_count} issues. "
            f"Reports in {out}/ (report.json, report.md)."
        )
    finally:
        cache.close()
        checkpoint.close()


@app.command()
def propose(
    checks: str = typer.Option("sanity,attributes,duplicates,seo", help="Checks to audit."),
    db: str = typer.Option("catalogguard.sqlite", help="SQLite product cache."),
    approvals_db: str = typer.Option("approvals.sqlite", help="Approval queue store."),
) -> None:
    """Audit, generate fix proposals, and load them into the review queue."""
    _load_dotenv()
    settings = load_settings()
    run = uuid.uuid4().hex[:8]
    logger = configure_logging(run, "logs")
    aliases = {"attributes": "attribute", "duplicates": "duplicate"}
    selected = [aliases.get(c.strip(), c.strip()) for c in checks.split(",") if c.strip()]

    cache = ProductCache(db)
    store = ApprovalStore(approvals_db)
    try:
        products = cache.all()
        config = AuditConfig(store_url=settings.magento_base_url, checks=selected)
        state = GraphState(config=config, products=products)
        Supervisor(build_agents(config, selected), logger, run_id=run).run(state)

        provider = get_provider(settings)
        proposals = FixProposalAgent(config, provider).propose(state.issues, products)
        store.save_many(proposals)
        typer.echo(
            f"Generated {len(proposals)} fix proposals from {len(state.issues)} issues "
            f"into {approvals_db}. Review with `catalogguard serve`."
        )
    finally:
        cache.close()
        store.close()


@app.command()
def serve(
    approvals_db: str = typer.Option("approvals.sqlite", help="Approval queue store."),
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8000),
) -> None:
    """Launch the HTMX review UI over the approval queue."""
    import uvicorn
    from api.app import create_app

    uvicorn.run(create_app(ApprovalStore(approvals_db)), host=host, port=port)


@app.command()
def apply(
    approvals_db: str = typer.Option("approvals.sqlite", help="Approval queue store."),
    journal_db: str = typer.Option("rollback.sqlite", help="Rollback journal store."),
    batch: str | None = typer.Option(None, help="Batch id (defaults to a new one)."),
) -> None:
    """Apply all APPROVED fixes to the store, journaling each change."""
    _load_dotenv()
    settings = load_settings()
    batch_id = batch or uuid.uuid4().hex[:8]

    store = ApprovalStore(approvals_db)
    journal = RollbackJournal(journal_db)
    client = MagentoClient(
        settings.magento_base_url,
        settings.magento_access_token,
        verify_ssl=settings.magento_verify_ssl,
    )
    try:
        approved = store.by_status(ProposalStatus.APPROVED)
        applied = ApplyAgent(client, journal).apply(approved, batch_id=batch_id)
        for proposal in applied:
            store.set_status(proposal.id, ProposalStatus.APPLIED)
        typer.echo(
            f"Applied {len(applied)} fixes as batch {batch_id}. "
            f"Revert with `catalogguard rollback --batch {batch_id}`."
        )
    finally:
        client.close()
        store.close()
        journal.close()


@app.command()
def rollback(
    batch: str = typer.Option(..., help="Batch id to revert."),
    journal_db: str = typer.Option("rollback.sqlite", help="Rollback journal store."),
) -> None:
    """Revert a previously applied batch, restoring prior values."""
    _load_dotenv()
    settings = load_settings()
    journal = RollbackJournal(journal_db)
    client = MagentoClient(
        settings.magento_base_url,
        settings.magento_access_token,
        verify_ssl=settings.magento_verify_ssl,
    )
    try:
        reverted = ApplyAgent(client, journal).revert(batch)
        typer.echo(f"Reverted {reverted} changes from batch {batch}.")
    finally:
        client.close()
        journal.close()

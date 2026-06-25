"""Command-line entrypoint: ``python -m catalogguard ...``.

Thin glue that wires settings → client → cache → extractor. Excluded from the
unit-coverage gate (it is exercised by the end-to-end extraction check).
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import typer

from catalogguard.agents.extractor import ExtractorAgent
from catalogguard.agents.registry import build_agents
from catalogguard.config import load_settings
from catalogguard.graph.supervisor import Supervisor
from catalogguard.logging import configure_logging
from catalogguard.magento_client import MagentoClient
from catalogguard.models import AuditConfig, GraphState
from catalogguard.reporting import build_report, render_markdown
from catalogguard.storage.cache import ProductCache
from catalogguard.storage.checkpoint import AuditCheckpoint

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

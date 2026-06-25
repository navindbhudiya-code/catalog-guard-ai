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
from catalogguard.config import load_settings
from catalogguard.logging import configure_logging
from catalogguard.magento_client import MagentoClient
from catalogguard.storage.cache import ProductCache

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

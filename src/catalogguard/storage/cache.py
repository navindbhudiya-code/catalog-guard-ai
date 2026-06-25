"""SQLite-backed product cache with a resumable cursor table."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from catalogguard.models import Product

_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    sku        TEXT PRIMARY KEY,
    payload    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cursors (
    name  TEXT PRIMARY KEY,
    value INTEGER NOT NULL
);
"""


class ProductCache:
    """Local cache of extracted products plus extraction checkpoints.

    Backed by SQLite so a large audit can resume after a crash: the extractor
    records the last completed page in ``cursors`` and picks up from there.
    """

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def upsert(self, product: Product) -> None:
        """Insert or replace a product keyed by SKU."""
        self._conn.execute(
            "INSERT OR REPLACE INTO products (sku, payload) VALUES (?, ?)",
            (product.sku, product.model_dump_json()),
        )
        self._conn.commit()

    def get(self, sku: str) -> Product | None:
        """Return a cached product, or None if absent."""
        row = self._conn.execute("SELECT payload FROM products WHERE sku = ?", (sku,)).fetchone()
        if row is None:
            return None
        return Product.model_validate_json(row["payload"])

    def count(self) -> int:
        """Number of cached products."""
        return int(self._conn.execute("SELECT COUNT(*) AS n FROM products").fetchone()["n"])

    def all(self) -> list[Product]:
        """Every cached product."""
        rows = self._conn.execute("SELECT payload FROM products").fetchall()
        return [Product.model_validate_json(row["payload"]) for row in rows]

    def set_cursor(self, name: str, value: int) -> None:
        """Persist a named checkpoint value."""
        self._conn.execute(
            "INSERT OR REPLACE INTO cursors (name, value) VALUES (?, ?)", (name, value)
        )
        self._conn.commit()

    def get_cursor(self, name: str, default: int = 0) -> int:
        """Read a named checkpoint, or ``default`` if unset."""
        row = self._conn.execute("SELECT value FROM cursors WHERE name = ?", (name,)).fetchone()
        return default if row is None else int(row["value"])

    def close(self) -> None:
        """Close the underlying connection."""
        self._conn.close()

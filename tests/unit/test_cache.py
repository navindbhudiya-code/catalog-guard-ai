"""Tests for the SQLite product cache and resumable cursor."""

from __future__ import annotations

from pathlib import Path

from catalogguard.models import Product
from catalogguard.storage.cache import ProductCache


def test_upsert_and_get_roundtrip() -> None:
    cache = ProductCache()
    cache.upsert(Product(sku="A", name="Alpha", price=9.0))

    fetched = cache.get("A")
    assert fetched is not None
    assert fetched.name == "Alpha"
    assert fetched.price == 9.0
    cache.close()


def test_upsert_is_idempotent_on_sku() -> None:
    cache = ProductCache()
    cache.upsert(Product(sku="A", name="first"))
    cache.upsert(Product(sku="A", name="second"))

    assert cache.count() == 1
    assert cache.get("A").name == "second"  # type: ignore[union-attr]
    cache.close()


def test_get_missing_returns_none() -> None:
    cache = ProductCache()
    assert cache.get("nope") is None
    cache.close()


def test_all_returns_every_cached_product() -> None:
    cache = ProductCache()
    cache.upsert(Product(sku="A"))
    cache.upsert(Product(sku="B"))
    assert {p.sku for p in cache.all()} == {"A", "B"}
    cache.close()


def test_cursor_defaults_then_persists(tmp_path: Path) -> None:
    db = tmp_path / "cache.sqlite"
    cache = ProductCache(db)
    assert cache.get_cursor("extract_page") == 0
    assert cache.get_cursor("extract_page", default=1) == 1

    cache.set_cursor("extract_page", 7)
    cache.close()

    # Reopen: cursor must survive a process restart (resumability).
    reopened = ProductCache(db)
    assert reopened.get_cursor("extract_page") == 7
    reopened.close()

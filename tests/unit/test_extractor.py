"""Tests for the ExtractorAgent (R-EXTRACT) — pulls catalog into the cache."""

from __future__ import annotations

from typing import Any

from catalogguard.agents.extractor import ExtractorAgent
from catalogguard.storage.cache import ProductCache


class FakeClient:
    """In-memory stand-in for MagentoClient.fetch_products_page."""

    def __init__(self, pages: dict[int, tuple[list[dict[str, Any]], int]]) -> None:
        self._pages = pages
        self.calls: list[int] = []

    def fetch_products_page(
        self, current_page: int, page_size: int
    ) -> tuple[list[dict[str, Any]], int]:
        self.calls.append(current_page)
        return self._pages[current_page]


class RecordingLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def info(self, event: str, **kw: Any) -> None:
        self.events.append((event, kw))


def _agent(client: FakeClient, cache: ProductCache, page_size: int = 2) -> ExtractorAgent:
    return ExtractorAgent(client, cache, RecordingLogger(), page_size=page_size)


def test_extract_pulls_all_pages_into_cache() -> None:
    client = FakeClient(
        {
            1: ([{"sku": "A"}, {"sku": "B"}], 3),
            2: ([{"sku": "C"}], 3),
        }
    )
    cache = ProductCache()
    count = _agent(client, cache).extract()

    assert count == 3
    assert {p.sku for p in cache.all()} == {"A", "B", "C"}
    assert cache.get_cursor("extract_page") == 2
    cache.close()


def test_extract_respects_max_products_and_stops_early() -> None:
    client = FakeClient({1: ([{"sku": "A"}, {"sku": "B"}, {"sku": "C"}], 3)})
    cache = ProductCache()

    count = _agent(client, cache, page_size=10).extract(max_products=2)

    assert count == 2
    assert cache.count() == 2
    cache.close()


def test_extract_resumes_from_saved_cursor() -> None:
    client = FakeClient({2: ([{"sku": "C"}, {"sku": "D"}], 4)})
    cache = ProductCache()
    cache.set_cursor("extract_page", 1)  # page 1 already done in a prior run

    count = _agent(client, cache).extract()

    assert client.calls == [2]  # never re-fetched page 1
    assert count == 2
    cache.close()


def test_extract_logs_each_page() -> None:
    client = FakeClient({1: ([{"sku": "A"}], 1)})
    cache = ProductCache()
    logger = RecordingLogger()
    ExtractorAgent(client, cache, logger, page_size=10).extract()

    events = [name for name, _ in logger.events]
    assert "extracted_page" in events
    assert "extract_complete" in events
    cache.close()

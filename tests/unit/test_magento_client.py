"""Tests for the Magento REST client (auth, pagination, retry/backoff)."""

from __future__ import annotations

import httpx
import pytest
from tenacity import wait_none

from catalogguard.magento_client import MagentoClient, RetryableStatusError


def _client(handler: httpx.MockTransport) -> MagentoClient:
    http = httpx.Client(transport=handler, base_url="https://app.demo.test")
    return MagentoClient("https://app.demo.test", "tok", client=http, wait=wait_none())


def test_sends_bearer_token_and_returns_page() -> None:
    seen: dict[str, str] = {}

    def handle(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers["Authorization"]
        return httpx.Response(200, json={"items": [{"sku": "A"}], "total_count": 1})

    client = _client(httpx.MockTransport(handle))
    items, total = client.fetch_products_page(current_page=1, page_size=50)

    assert seen["auth"] == "Bearer tok"
    assert items == [{"sku": "A"}]
    assert total == 1


def test_iter_products_paginates_until_total_reached() -> None:
    pages = {
        1: {"items": [{"sku": "A"}, {"sku": "B"}], "total_count": 3},
        2: {"items": [{"sku": "C"}], "total_count": 3},
    }

    def handle(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["searchCriteria[currentPage]"])
        return httpx.Response(200, json=pages[page])

    client = _client(httpx.MockTransport(handle))
    skus = [p["sku"] for p in client.iter_products(page_size=2)]
    assert skus == ["A", "B", "C"]


def test_iter_products_stops_on_empty_page() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["searchCriteria[currentPage]"])
        if page == 1:
            return httpx.Response(200, json={"items": [{"sku": "A"}], "total_count": 999})
        return httpx.Response(200, json={"items": [], "total_count": 999})

    client = _client(httpx.MockTransport(handle))
    skus = [p["sku"] for p in client.iter_products(page_size=1)]
    assert skus == ["A"]


def test_retries_on_429_then_succeeds() -> None:
    calls = {"n": 0}

    def handle(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, json={"message": "slow down"})
        return httpx.Response(200, json={"items": [], "total_count": 0})

    client = _client(httpx.MockTransport(handle))
    items, _total = client.fetch_products_page(1, 10)
    assert calls["n"] == 2
    assert items == []


def test_gives_up_after_max_attempts_on_persistent_5xx() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"message": "down"})

    http = httpx.Client(transport=httpx.MockTransport(handle), base_url="https://app.demo.test")
    client = MagentoClient(
        "https://app.demo.test", "tok", client=http, wait=wait_none(), max_attempts=3
    )
    with pytest.raises(RetryableStatusError):
        client.fetch_products_page(1, 10)


def test_non_retryable_error_raises_immediately() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "missing"})

    client = _client(httpx.MockTransport(handle))
    with pytest.raises(httpx.HTTPStatusError):
        client.fetch_products_page(1, 10)


def test_builds_default_client_and_closes() -> None:
    client = MagentoClient("https://app.demo.test/", "tok", verify_ssl=False)
    client.close()

"""Magento 2 REST client: token auth, pagination, rate-limit backoff, retry."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import httpx
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tenacity.wait import wait_base

_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
_PRODUCTS_PATH = "/rest/V1/products"


class RetryableStatusError(Exception):
    """Raised internally for HTTP statuses worth retrying (429/5xx)."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"retryable status {status_code}")


class MagentoClient:
    """Thin Magento REST client scoped to read-only catalog extraction.

    Retries transient failures (429 + 5xx) with exponential backoff; surfaces
    non-retryable HTTP errors immediately so callers fail fast on bad auth/404s.
    """

    def __init__(
        self,
        base_url: str,
        access_token: str,
        *,
        client: httpx.Client | None = None,
        verify_ssl: bool = True,
        max_attempts: int = 4,
        wait: wait_base | None = None,
    ) -> None:
        base = base_url.rstrip("/")
        self._client = client or httpx.Client(base_url=base, verify=verify_ssl)
        self._headers = {"Authorization": f"Bearer {access_token}"}
        self._max_attempts = max_attempts
        self._wait: wait_base = wait or wait_exponential(multiplier=0.5, max=30)

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        for attempt in Retrying(
            stop=stop_after_attempt(self._max_attempts),
            wait=self._wait,
            retry=retry_if_exception_type(RetryableStatusError),
            reraise=True,
        ):
            with attempt:
                response = self._client.get(path, params=params, headers=self._headers)
                if response.status_code in _RETRYABLE_STATUS:
                    raise RetryableStatusError(response.status_code)
                response.raise_for_status()
                data: dict[str, Any] = response.json()
                return data
        raise AssertionError("unreachable")  # pragma: no cover

    def fetch_products_page(
        self, current_page: int, page_size: int
    ) -> tuple[list[dict[str, Any]], int]:
        """Fetch one page of products; returns (items, total_count)."""
        data = self._get(
            _PRODUCTS_PATH,
            {
                "searchCriteria[pageSize]": page_size,
                "searchCriteria[currentPage]": current_page,
            },
        )
        return data["items"], int(data["total_count"])

    def iter_products(self, page_size: int = 100) -> Iterator[dict[str, Any]]:
        """Yield every product across all pages, stopping at total or empty page."""
        page = 1
        while True:
            items, total = self.fetch_products_page(page, page_size)
            yield from items
            if not items or page * page_size >= total:
                return
            page += 1

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

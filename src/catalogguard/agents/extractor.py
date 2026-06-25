"""ExtractorAgent — pulls the catalog into the local cache, resumably (R-EXTRACT)."""

from __future__ import annotations

from typing import Any, Protocol

from catalogguard.models import Product
from catalogguard.storage.cache import ProductCache

_CURSOR = "extract_page"


class ProductsClient(Protocol):
    """The slice of MagentoClient the extractor depends on."""

    def fetch_products_page(
        self, current_page: int, page_size: int
    ) -> tuple[list[dict[str, Any]], int]: ...


class ExtractorAgent:
    """Paginates the Magento catalog into the SQLite cache.

    Checkpoints the last fully-completed page in the cache so a crashed audit
    resumes where it left off instead of re-pulling 30,000 SKUs. Upserts are
    idempotent, so re-running a partial page is harmless.
    """

    def __init__(
        self,
        client: ProductsClient,
        cache: ProductCache,
        logger: Any,
        *,
        page_size: int = 100,
    ) -> None:
        self._client = client
        self._cache = cache
        self._log = logger
        self._page_size = page_size

    def extract(self, max_products: int | None = None) -> int:
        """Pull products into the cache; returns the count extracted this run."""
        page = self._cache.get_cursor(_CURSOR) + 1
        extracted = 0

        while True:
            items, total = self._client.fetch_products_page(page, self._page_size)
            for raw in items:
                self._cache.upsert(Product.from_magento(raw))
                extracted += 1
                if max_products is not None and extracted >= max_products:
                    self._log.info("extract_complete", extracted=extracted, partial=True)
                    return extracted

            self._cache.set_cursor(_CURSOR, page)
            self._log.info("extracted_page", page=page, count=len(items), total=total)
            if not items or page * self._page_size >= total:
                break
            page += 1

        self._log.info("extract_complete", extracted=extracted, partial=False)
        return extracted

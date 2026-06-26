"""DuplicateAgent — exact and near-duplicate product detection (R-DUP)."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable

from catalogguard.models import AuditConfig, Dimension, Issue, Product, Severity
from catalogguard.providers.similarity import InMemorySimilarityIndex, SimilarityIndex
from catalogguard.rules.base import issue

_WS = re.compile(r"\s+")


def _signature(product: Product) -> str:
    """Normalized text used to detect *exact* duplicates."""
    return _WS.sub(" ", f"{product.name} {product.description or ''}".strip().lower())


def _embedding_text(product: Product) -> str:
    """Text fed to the similarity index for *near*-duplicate detection."""
    parts = [product.name, product.description or "", product.short_description or ""]
    return " ".join(p for p in parts if p)


class DuplicateAgent:
    """Detects identical products (text equality) and near-duplicates (similarity).

    Near-duplicate detection runs through an injectable ``SimilarityIndex`` so the
    default token-cosine index can be swapped for a ChromaDB embedding index.
    """

    name = "DuplicateAgent"

    def __init__(
        self,
        config: AuditConfig,
        *,
        index_factory: Callable[[], SimilarityIndex] = InMemorySimilarityIndex,
        top_k: int = 5,
    ) -> None:
        self._config = config
        self._index_factory = index_factory
        self._top_k = top_k

    def run(self, products: list[Product]) -> list[Issue]:
        by_sku = {p.sku: p for p in products}
        family = self._family_map(products)
        found, exact_pairs = self._exact_duplicates(products, by_sku, family)
        found.extend(self._near_duplicates(products, by_sku, exact_pairs, family))
        return found

    @staticmethod
    def _family_map(products: list[Product]) -> dict[str, int]:
        """Map each variant SKU to its parent id, so siblings aren't 'duplicates'."""
        id_to_sku = {p.id: p.sku for p in products if p.id is not None}
        family: dict[str, int] = {}
        for product in products:
            if not product.variant_child_ids or product.id is None:
                continue
            family[product.sku] = product.id
            for child_id in product.variant_child_ids:
                child_sku = id_to_sku.get(child_id)
                if child_sku is not None:
                    family[child_sku] = product.id
        return family

    @staticmethod
    def _same_family(family: dict[str, int], left: str, right: str) -> bool:
        root = family.get(left)
        return root is not None and root == family.get(right)

    def _exact_duplicates(
        self, products: list[Product], by_sku: dict[str, Product], family: dict[str, int]
    ) -> tuple[list[Issue], set[tuple[str, str]]]:
        groups: dict[str, list[str]] = defaultdict(list)
        for product in products:
            groups[_signature(product)].append(product.sku)

        found: list[Issue] = []
        exact_pairs: set[tuple[str, str]] = set()
        for skus in groups.values():
            if len(skus) < 2:
                continue
            ordered = sorted(skus)
            for sku in ordered:
                others = [s for s in ordered if s != sku and not self._same_family(family, sku, s)]
                if others:
                    found.append(
                        issue(
                            by_sku[sku],
                            Dimension.DUPLICATE,
                            Severity.HIGH,
                            "exact_duplicate",
                            "Product is textually identical to other products.",
                            current_value=others,
                        )
                    )
            for i, left in enumerate(ordered):
                for right in ordered[i + 1 :]:
                    exact_pairs.add((left, right))
        return found, exact_pairs

    def _near_duplicates(
        self,
        products: list[Product],
        by_sku: dict[str, Product],
        exact_pairs: set[tuple[str, str]],
        family: dict[str, int],
    ) -> list[Issue]:
        index = self._index_factory()
        texts = {p.sku: _embedding_text(p) for p in products}
        for sku, text in texts.items():
            index.add(sku, text)

        threshold = self._config.similarity_threshold
        seen: set[tuple[str, str]] = set()
        found: list[Issue] = []
        for product in products:
            for other, similarity in index.query(texts[product.sku], self._top_k):
                if other == product.sku:
                    continue
                pair = (product.sku, other) if product.sku < other else (other, product.sku)
                if (
                    pair in seen
                    or pair in exact_pairs
                    or similarity < threshold
                    or self._same_family(family, pair[0], pair[1])
                ):
                    continue
                seen.add(pair)
                found.append(
                    issue(
                        by_sku[pair[0]],
                        Dimension.DUPLICATE,
                        Severity.MEDIUM,
                        "near_duplicate",
                        "Product is highly similar to another product.",
                        current_value={"duplicate_of": pair[1], "similarity": round(similarity, 3)},
                    )
                )
        return found

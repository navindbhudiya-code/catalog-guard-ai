"""SEOAgent — per-product SEO rules plus cross-product duplicate-meta detection (R-SEO)."""

from __future__ import annotations

from collections import defaultdict

from catalogguard.models import AuditConfig, Dimension, Issue, Product, Severity
from catalogguard.rules.base import issue
from catalogguard.rules.seo import SEO_RULES


class SEOAgent:
    """Rule-based SEO audit. Generated meta fixes are produced by FixProposalAgent."""

    name = "SEOAgent"

    def __init__(self, config: AuditConfig) -> None:
        self._config = config

    def run(self, products: list[Product]) -> list[Issue]:
        found: list[Issue] = []
        for product in products:
            for rule in SEO_RULES:
                found.extend(rule(product, self._config))
        found.extend(self._duplicate_meta_titles(products))
        return found

    def _duplicate_meta_titles(self, products: list[Product]) -> list[Issue]:
        groups: dict[str, list[Product]] = defaultdict(list)
        for product in products:
            title = (product.meta_title or "").strip().lower()
            if title:
                groups[title].append(product)

        found: list[Issue] = []
        for group in groups.values():
            if len(group) < 2:
                continue
            skus = sorted(p.sku for p in group)
            for product in group:
                found.append(
                    issue(
                        product,
                        Dimension.SEO,
                        Severity.MEDIUM,
                        "duplicate_meta_title",
                        "Meta title is shared with other products.",
                        field="meta_title",
                        current_value=[s for s in skus if s != product.sku],
                    )
                )
        return found

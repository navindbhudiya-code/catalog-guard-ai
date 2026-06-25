"""Category / pricing / stock sanity rules (R-SANITY). Pure rules, no LLM."""

from __future__ import annotations

from catalogguard.models import AuditConfig, Dimension, Issue, Product, Severity

from .base import Rule, issue

# Magento visibility 1 = "Not Visible Individually"; such products are exempt
# from the "visible but out of stock" check.
_NOT_VISIBLE = 1


def zero_price_enabled(product: Product, _config: AuditConfig) -> list[Issue]:
    if product.is_enabled and (product.price is None or product.price == 0):
        return [
            issue(
                product,
                Dimension.SANITY,
                Severity.HIGH,
                "zero_price",
                "Enabled product has a price of 0.",
                field="price",
                current_value=product.price,
            )
        ]
    return []


def zero_categories(product: Product, _config: AuditConfig) -> list[Issue]:
    if product.is_enabled and not product.categories:
        return [
            issue(
                product,
                Dimension.SANITY,
                Severity.MEDIUM,
                "zero_categories",
                "Enabled product is assigned to no categories.",
                field="categories",
            )
        ]
    return []


def special_price_exceeds_regular(product: Product, _config: AuditConfig) -> list[Issue]:
    if (
        product.is_enabled
        and product.price is not None
        and product.special_price is not None
        and product.special_price > product.price
    ):
        return [
            issue(
                product,
                Dimension.SANITY,
                Severity.HIGH,
                "special_price_exceeds_regular",
                "Special price is greater than the regular price.",
                field="special_price",
                current_value=product.special_price,
            )
        ]
    return []


def enabled_zero_stock(product: Product, _config: AuditConfig) -> list[Issue]:
    if (
        product.is_enabled
        and product.visibility != _NOT_VISIBLE
        and product.stock_qty is not None
        and product.stock_qty <= 0
    ):
        return [
            issue(
                product,
                Dimension.SANITY,
                Severity.MEDIUM,
                "enabled_zero_stock",
                "Enabled, catalog-visible product has zero stock.",
                field="stock_qty",
                current_value=product.stock_qty,
            )
        ]
    return []


SANITY_RULES: list[Rule] = [
    zero_price_enabled,
    zero_categories,
    special_price_exceeds_regular,
    enabled_zero_stock,
]

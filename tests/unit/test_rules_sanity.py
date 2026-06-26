"""Tests for sanity rule checks (R-SANITY) — pure rules, no LLM."""

from __future__ import annotations

from catalogguard.agents.sanity import SanityAgent
from catalogguard.models import AuditConfig, Dimension, Product

CONFIG = AuditConfig(store_url="https://app.demo.test", checks=["sanity"])


def _codes(products: list[Product]) -> set[str]:
    issues = SanityAgent(CONFIG).run(products)
    assert all(i.dimension is Dimension.SANITY for i in issues)
    return {i.code for i in issues}


def test_clean_product_yields_no_sanity_issues() -> None:
    clean = Product(
        sku="OK",
        name="Fine",
        price=10.0,
        status=1,
        visibility=4,
        stock_qty=5,
        categories=[3],
    )
    assert _codes([clean]) == set()


def test_flags_zero_price_on_enabled_product() -> None:
    assert "zero_price" in _codes([Product(sku="A", status=1, price=0, categories=[1])])


def test_flags_zero_categories_on_enabled_product() -> None:
    assert "zero_categories" in _codes(
        [Product(sku="A", status=1, price=5, categories=[], stock_qty=1)]
    )


def test_flags_special_price_exceeding_regular() -> None:
    product = Product(sku="A", status=1, price=10, special_price=15, categories=[1], stock_qty=1)
    assert "special_price_exceeds_regular" in _codes([product])


def test_flags_enabled_visible_product_with_zero_stock() -> None:
    product = Product(sku="A", status=1, visibility=4, price=5, categories=[1], stock_qty=0)
    assert "enabled_zero_stock" in _codes([product])


def test_does_not_flag_stock_when_not_visible_individually() -> None:
    product = Product(sku="A", status=1, visibility=1, price=5, categories=[1], stock_qty=0)
    assert "enabled_zero_stock" not in _codes([product])


def test_disabled_product_is_exempt_from_sanity_rules() -> None:
    product = Product(sku="A", status=2, price=0, categories=[], stock_qty=0)
    assert _codes([product]) == set()


def test_configurable_parent_is_exempt_from_zero_price() -> None:
    parent = Product(
        sku="WJ01", status=1, type_id="configurable", price=0, categories=[1], stock_qty=1
    )
    assert "zero_price" not in _codes([parent])

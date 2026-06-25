"""Tests for SEOAgent (R-SEO) — meta/url audit + duplicate-meta detection."""

from __future__ import annotations

from catalogguard.agents.seo import SEOAgent
from catalogguard.models import AuditConfig, Dimension, Product

CONFIG = AuditConfig(store_url="https://app.demo.test", checks=["seo"])


def _codes(products: list[Product]) -> set[str]:
    issues = SEOAgent(CONFIG).run(products)
    assert all(i.dimension is Dimension.SEO for i in issues)
    return {i.code for i in issues}


def _clean(**overrides: object) -> Product:
    base: dict[str, object] = {
        "sku": "A",
        "name": "Tee",
        "description": "A nicely detailed description of this comfortable cotton t-shirt.",
        "meta_title": "Comfortable Cotton Tee",
        "meta_description": "Buy our comfortable cotton tee, available in many sizes and colors.",
        "url_key": "comfortable-cotton-tee",
        "status": 1,
    }
    base.update(overrides)
    return Product(**base)


def test_clean_product_has_no_seo_issues() -> None:
    assert _codes([_clean()]) == set()


def test_flags_missing_meta_title_and_description_and_url() -> None:
    codes = _codes([_clean(meta_title=None, meta_description=None, url_key=None)])
    assert {"missing_meta_title", "missing_meta_description", "missing_url_key"} <= codes


def test_flags_meta_length_violations() -> None:
    codes = _codes([_clean(meta_title="x" * 61, meta_description="y" * 161)])
    assert "meta_title_too_long" in codes
    assert "meta_description_too_long" in codes


def test_flags_thin_content_on_enabled_product() -> None:
    assert "thin_content" in _codes([_clean(description="short")])


def test_flags_duplicate_meta_titles_across_products() -> None:
    products = [_clean(sku="A"), _clean(sku="B")]  # identical meta_title
    issues = SEOAgent(CONFIG).run(products)
    dupes = [i for i in issues if i.code == "duplicate_meta_title"]
    assert {i.sku for i in dupes} == {"A", "B"}

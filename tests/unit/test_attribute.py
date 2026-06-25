"""Tests for attribute completeness rules (R-ATTR) — rules-first."""

from __future__ import annotations

from catalogguard.agents.attribute import AttributeAgent
from catalogguard.models import AuditConfig, Dimension, Product


def _run(product: Product, *, required: list[str] | None = None) -> set[str]:
    config = AuditConfig(
        store_url="https://app.demo.test",
        checks=["attribute"],
        required_attributes=required or [],
    )
    issues = AttributeAgent(config).run([product])
    assert all(i.dimension is Dimension.ATTRIBUTE for i in issues)
    return {i.code for i in issues}


def test_complete_product_yields_no_attribute_issues() -> None:
    product = Product(
        sku="A",
        name="Tee",
        description="A comfy cotton tee.",
        type_id="simple",
        weight=0.5,
        images=["/a/b.jpg"],
        custom_attributes={"brand": "Acme"},
    )
    assert _run(product, required=["brand"]) == set()


def test_flags_missing_required_attribute() -> None:
    product = Product(sku="A", name="Tee", images=["x.jpg"], weight=1.0)
    assert "missing_required_attribute" in _run(product, required=["brand"])


def test_present_first_class_required_attribute_is_satisfied() -> None:
    product = Product(sku="A", name="Tee", images=["x.jpg"], weight=1.0)
    assert "missing_required_attribute" not in _run(product, required=["name"])


def test_flags_placeholder_text() -> None:
    product = Product(sku="A", name="Tee", description="TBD", images=["x.jpg"], weight=1.0)
    assert "placeholder_value" in _run(product)


def test_flags_lorem_ipsum_in_custom_attribute() -> None:
    product = Product(
        sku="A",
        name="Tee",
        images=["x.jpg"],
        weight=1.0,
        custom_attributes={"care": "Lorem ipsum dolor sit amet"},
    )
    assert "placeholder_value" in _run(product)


def test_flags_missing_images() -> None:
    product = Product(sku="A", name="Tee", images=[], weight=1.0)
    assert "missing_images" in _run(product)


def test_flags_missing_weight_on_shippable_simple_product() -> None:
    product = Product(sku="A", name="Tee", type_id="simple", weight=None, images=["x.jpg"])
    assert "missing_weight" in _run(product)


def test_virtual_product_is_exempt_from_missing_weight() -> None:
    product = Product(sku="A", name="Tee", type_id="virtual", weight=None, images=["x.jpg"])
    assert "missing_weight" not in _run(product)


def test_required_list_attribute_is_flagged_when_empty() -> None:
    product = Product(sku="A", name="Tee", categories=[], images=["x.jpg"], weight=1.0)
    assert "missing_required_attribute" in _run(product, required=["categories"])


def test_required_list_attribute_is_satisfied_when_present() -> None:
    product = Product(sku="A", name="Tee", categories=[5], images=["x.jpg"], weight=1.0)
    assert "missing_required_attribute" not in _run(product, required=["categories"])


def test_required_non_string_scalar_attribute_is_satisfied() -> None:
    product = Product(sku="A", name="Tee", status=1, images=["x.jpg"], weight=1.0)
    assert "missing_required_attribute" not in _run(product, required=["status"])


def test_non_string_custom_attribute_is_ignored_for_placeholders() -> None:
    product = Product(
        sku="A",
        name="Tee",
        images=["x.jpg"],
        weight=1.0,
        custom_attributes={"rating": 5, "note": "fine"},
    )
    assert "placeholder_value" not in _run(product)

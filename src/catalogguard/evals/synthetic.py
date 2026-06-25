"""Synthetic broken-catalog generator (R-EVAL).

Produces a deterministic catalog with known, independently-labelled defects so we
can measure the audit's precision/recall against ground truth. Each defective
product carries exactly one injected defect; descriptions use distinct vocabulary
so they are not accidentally flagged as duplicates.
"""

from __future__ import annotations

from typing import Any

from catalogguard.models import Product

Finding = tuple[str, str, str]  # (sku, dimension, code)


def _clean(sku: str, name: str, description: str, **overrides: Any) -> Product:
    fields: dict[str, Any] = {
        "sku": sku,
        "name": name,
        "description": description,
        "price": 20.0,
        "status": 1,
        "visibility": 4,
        "type_id": "simple",
        "weight": 1.0,
        "stock_qty": 5,
        "categories": [1],
        "images": ["i.jpg"],
        "meta_title": f"{name} | Shop",
        "meta_description": f"Buy {name} online today with fast shipping and easy returns.",
        "url_key": sku.lower(),
    }
    fields.update(overrides)
    return Product(**fields)


def generate_catalog() -> tuple[list[Product], set[Finding]]:
    """Return (products, expected_findings) for the synthetic benchmark."""
    products: list[Product] = []
    expected: set[Finding] = set()

    def add(product: Product, *defects: tuple[str, str]) -> None:
        products.append(product)
        for dimension, code in defects:
            expected.add((product.sku, dimension, code))

    # Clean control — no defects expected.
    add(_clean("OK", "Cotton Tee", "Soft organic cotton t-shirt with a relaxed fit and collar."))

    # Sanity defects.
    add(
        _clean(
            "ZP", "Water Bottle", "Stainless steel bottle that keeps drinks cold all day.", price=0
        ),
        ("sanity", "zero_price"),
    )
    add(
        _clean(
            "ZC",
            "Soy Candle",
            "Hand poured soy candle with warm vanilla and amber notes.",
            categories=[],
        ),
        ("sanity", "zero_categories"),
    )
    add(
        _clean(
            "SP",
            "Office Chair",
            "Ergonomic office chair with adjustable lumbar and arms.",
            special_price=25.0,
        ),
        ("sanity", "special_price_exceeds_regular"),
    )
    add(
        _clean(
            "ST",
            "Keyboard",
            "Wireless mechanical keyboard with hot swap switches glow.",
            stock_qty=0,
        ),
        ("sanity", "enabled_zero_stock"),
    )

    # Attribute defects.
    add(
        _clean(
            "IMG",
            "Coffee Mug",
            "Ceramic coffee mug glazed by hand holding twelve ounces.",
            images=[],
        ),
        ("attribute", "missing_images"),
    )
    add(
        _clean(
            "WT",
            "Skillet",
            "Cast iron skillet pre seasoned ready for searing and baking.",
            weight=None,
        ),
        ("attribute", "missing_weight"),
    )
    add(
        _clean("PH", "Beanie", "Lorem ipsum dolor sit amet consectetur adipiscing elit sed."),
        ("attribute", "placeholder_value"),
    )

    # SEO defects.
    add(
        _clean(
            "MT",
            "Cutting Board",
            "Bamboo cutting board with juice groove and rubber feet.",
            meta_title=None,
        ),
        ("seo", "missing_meta_title"),
    )
    add(
        _clean(
            "MD",
            "Throw Pillow",
            "Linen throw pillow cover in sage green with hidden zipper.",
            meta_description=None,
        ),
        ("seo", "missing_meta_description"),
    )
    add(
        _clean(
            "UK",
            "Wool Socks",
            "Merino wool socks that are warm breathable and washable.",
            url_key=None,
        ),
        ("seo", "missing_url_key"),
    )
    add(
        _clean(
            "TL",
            "Notebook",
            "Dotted hardcover notebook with elastic band and pocket.",
            meta_title="x" * 61,
        ),
        ("seo", "meta_title_too_long"),
    )
    add(_clean("TC", "Phone Case", "short"), ("seo", "thin_content"))

    # Duplicate pair — identical name + description.
    dup_name, dup_desc = (
        "Travel Backpack",
        "Durable travel backpack with padded laptop sleeve and zip.",
    )
    add(
        _clean("DUP1", dup_name, dup_desc, meta_title="Backpack A", url_key="dup1"),
        ("duplicate", "exact_duplicate"),
    )
    add(
        _clean("DUP2", dup_name, dup_desc, meta_title="Backpack B", url_key="dup2"),
        ("duplicate", "exact_duplicate"),
    )

    return products, expected

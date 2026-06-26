"""Attribute completeness rules (R-ATTR) — rules-first; LLM checks land in Phase 3."""

from __future__ import annotations

from catalogguard.models import AuditConfig, Dimension, Issue, Product, Severity

from .base import PARENT_PRODUCT_TYPES, Rule, issue

_PLACEHOLDERS = {"tbd", "n/a", "na", "todo", "xxx", "placeholder", "test"}
# Product types that need no weight: non-shipped (virtual/downloadable) and
# composite parents (configurable/grouped/bundle) whose weight lives on children.
_WEIGHTLESS_TYPES = {"virtual", "downloadable"} | set(PARENT_PRODUCT_TYPES)
# First-class text fields scanned for placeholder content.
_TEXT_FIELDS = (
    "name",
    "description",
    "short_description",
    "meta_title",
    "meta_description",
    "meta_keyword",
)


def _attribute_value(product: Product, code: str) -> object:
    value = getattr(product, code, None)
    if value is None:
        return product.custom_attributes.get(code)
    return value


def _is_empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return not value
    return False


def missing_required_attributes(product: Product, config: AuditConfig) -> list[Issue]:
    found: list[Issue] = []
    for code in config.required_attributes:
        if _is_empty(_attribute_value(product, code)):
            found.append(
                issue(
                    product,
                    Dimension.ATTRIBUTE,
                    Severity.HIGH,
                    "missing_required_attribute",
                    f"Required attribute '{code}' is empty.",
                    field=code,
                )
            )
    return found


def _text_values(product: Product) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for field in _TEXT_FIELDS:
        raw = getattr(product, field, None)
        if isinstance(raw, str) and raw.strip():
            values.append((field, raw))
    for code, raw in product.custom_attributes.items():
        if isinstance(raw, str) and raw.strip():
            values.append((code, raw))
    return values


def placeholder_values(product: Product, _config: AuditConfig) -> list[Issue]:
    found: list[Issue] = []
    for field, text in _text_values(product):
        normalized = text.strip().lower()
        if normalized in _PLACEHOLDERS or "lorem ipsum" in normalized:
            found.append(
                issue(
                    product,
                    Dimension.ATTRIBUTE,
                    Severity.MEDIUM,
                    "placeholder_value",
                    f"Field '{field}' contains placeholder text.",
                    field=field,
                    current_value=text,
                )
            )
    return found


def missing_images(product: Product, _config: AuditConfig) -> list[Issue]:
    # Composite parents inherit imagery from their variants; don't flag them.
    if product.type_id in PARENT_PRODUCT_TYPES:
        return []
    if not product.images:
        return [
            issue(
                product,
                Dimension.ATTRIBUTE,
                Severity.MEDIUM,
                "missing_images",
                "Product has no images.",
                field="images",
            )
        ]
    return []


def missing_weight(product: Product, _config: AuditConfig) -> list[Issue]:
    if product.type_id not in _WEIGHTLESS_TYPES and product.weight is None:
        return [
            issue(
                product,
                Dimension.ATTRIBUTE,
                Severity.LOW,
                "missing_weight",
                "Shippable product is missing a weight.",
                field="weight",
            )
        ]
    return []


ATTRIBUTE_RULES: list[Rule] = [
    missing_required_attributes,
    placeholder_values,
    missing_images,
    missing_weight,
]

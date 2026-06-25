"""Shared helpers for rule-based checks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from catalogguard.models import AuditConfig, DetectedBy, Dimension, Issue, Product

# A rule inspects one product (with run config) and returns zero or more issues.
Rule = Callable[[Product, AuditConfig], list[Issue]]


def issue(
    product: Product,
    dimension: Dimension,
    severity: Any,
    code: str,
    message: str,
    *,
    field: str | None = None,
    current_value: Any | None = None,
) -> Issue:
    """Construct a rule-detected Issue for a product."""
    return Issue(
        sku=product.sku,
        dimension=dimension,
        severity=severity,
        code=code,
        message=message,
        field=field,
        current_value=current_value,
        detected_by=DetectedBy.RULE,
    )

"""SEO rules (R-SEO) — meta presence/length, url key, thin content."""

from __future__ import annotations

from catalogguard.models import AuditConfig, Dimension, Issue, Product, Severity

from .base import Rule, issue

_META_TITLE_MAX = 60
_META_DESCRIPTION_MAX = 160
_THIN_CONTENT_MIN = 50


def missing_meta_title(product: Product, _config: AuditConfig) -> list[Issue]:
    if not (product.meta_title or "").strip():
        return [
            issue(
                product,
                Dimension.SEO,
                Severity.MEDIUM,
                "missing_meta_title",
                "Missing meta title.",
                field="meta_title",
            )
        ]
    return []


def missing_meta_description(product: Product, _config: AuditConfig) -> list[Issue]:
    if not (product.meta_description or "").strip():
        return [
            issue(
                product,
                Dimension.SEO,
                Severity.MEDIUM,
                "missing_meta_description",
                "Missing meta description.",
                field="meta_description",
            )
        ]
    return []


def meta_title_too_long(product: Product, _config: AuditConfig) -> list[Issue]:
    if product.meta_title and len(product.meta_title) > _META_TITLE_MAX:
        return [
            issue(
                product,
                Dimension.SEO,
                Severity.LOW,
                "meta_title_too_long",
                f"Meta title exceeds {_META_TITLE_MAX} characters.",
                field="meta_title",
            )
        ]
    return []


def meta_description_too_long(product: Product, _config: AuditConfig) -> list[Issue]:
    if product.meta_description and len(product.meta_description) > _META_DESCRIPTION_MAX:
        return [
            issue(
                product,
                Dimension.SEO,
                Severity.LOW,
                "meta_description_too_long",
                f"Meta description exceeds {_META_DESCRIPTION_MAX} characters.",
                field="meta_description",
            )
        ]
    return []


def missing_url_key(product: Product, _config: AuditConfig) -> list[Issue]:
    if not (product.url_key or "").strip():
        return [
            issue(
                product,
                Dimension.SEO,
                Severity.MEDIUM,
                "missing_url_key",
                "Missing URL key.",
                field="url_key",
            )
        ]
    return []


def thin_content(product: Product, _config: AuditConfig) -> list[Issue]:
    if product.is_enabled and len((product.description or "").strip()) < _THIN_CONTENT_MIN:
        return [
            issue(
                product,
                Dimension.SEO,
                Severity.LOW,
                "thin_content",
                "Description is too thin for SEO.",
                field="description",
            )
        ]
    return []


SEO_RULES: list[Rule] = [
    missing_meta_title,
    missing_meta_description,
    meta_title_too_long,
    meta_description_too_long,
    missing_url_key,
    thin_content,
]

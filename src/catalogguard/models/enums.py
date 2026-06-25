"""Enumerations shared across the audit pipeline."""

from __future__ import annotations

from enum import StrEnum


class Dimension(StrEnum):
    """The five audit dimensions."""

    DUPLICATE = "duplicate"
    ATTRIBUTE = "attribute"
    CONTENT = "content"
    SEO = "seo"
    SANITY = "sanity"


class Severity(StrEnum):
    """Issue severity, low to critical."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectedBy(StrEnum):
    """Whether an issue was found by a cheap rule or an LLM."""

    RULE = "rule"
    LLM = "llm"


class ProposalStatus(StrEnum):
    """Lifecycle of a fix proposal through the human-in-the-loop queue."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"

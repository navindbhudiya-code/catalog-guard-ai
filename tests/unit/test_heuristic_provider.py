"""Tests for the offline heuristic provider (R-PROVIDER)."""

from __future__ import annotations

from catalogguard.agents.fix_proposal import FixProposalAgent
from catalogguard.models import AuditConfig, Dimension, Issue, Product, Severity
from catalogguard.providers.heuristic import HeuristicProvider


def _prompt(field: str, name: str) -> str:
    return f"Field to fix: {field}\nIssue: x\nProduct name: {name}\nCurrent description: "


def test_generates_meta_title_from_product_name() -> None:
    result = HeuristicProvider().generate("sys", _prompt("meta_title", "Red Cotton Tee"), {})
    assert result["value"].startswith("Red Cotton Tee")
    assert len(result["value"]) <= 60
    assert result["confidence"] == 0.9


def test_generates_meta_description_from_product_name() -> None:
    result = HeuristicProvider().generate("sys", _prompt("meta_description", "Red Tee"), {})
    assert "Red Tee" in result["value"]
    assert len(result["value"]) <= 160
    assert result["confidence"] == 0.8


def test_generates_description_rewrite() -> None:
    result = HeuristicProvider().generate("sys", _prompt("description", "Red Tee"), {})
    assert "Red Tee" in result["value"]
    assert result["confidence"] == 0.7


def test_falls_back_when_field_unknown_or_name_missing() -> None:
    result = HeuristicProvider().generate("sys", "no recognizable fields here", {})
    assert result["value"]
    assert 0.0 <= result["confidence"] <= 1.0


def test_works_end_to_end_with_fix_proposal_agent() -> None:
    config = AuditConfig(store_url="https://x", checks=["seo"])
    product = Product(sku="A", name="Blue Mug", meta_title=None)
    issue = Issue(
        sku="A",
        dimension=Dimension.SEO,
        severity=Severity.MEDIUM,
        code="missing_meta_title",
        message="m",
        field="meta_title",
    )
    proposals = FixProposalAgent(config, HeuristicProvider()).propose([issue], [product])
    assert proposals[0].proposed_value.startswith("Blue Mug")
    assert proposals[0].confidence == 0.9

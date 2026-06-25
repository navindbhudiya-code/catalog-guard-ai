"""Tests for FixProposalAgent (R-CONTENT/R-SEO fixes), structured output."""

from __future__ import annotations

from typing import Any

from catalogguard.agents.fix_proposal import FixProposalAgent
from catalogguard.logging.cost import CostLedger
from catalogguard.models import (
    AuditConfig,
    Dimension,
    Issue,
    Product,
    ProposalStatus,
    Severity,
)

CONFIG = AuditConfig(store_url="https://app.demo.test", checks=["seo"])


class FakeProvider:
    name = "fake"

    def __init__(self, response: dict[str, Any]) -> None:
        self._response = response
        self.calls = 0

    def generate(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        return self._response


def _issue(code: str, sku: str = "A", field: str | None = None) -> Issue:
    return Issue(
        sku=sku,
        dimension=Dimension.SEO,
        severity=Severity.MEDIUM,
        code=code,
        message="m",
        field=field,
    )


def test_generates_proposal_for_fixable_seo_issue() -> None:
    provider = FakeProvider({"value": "Great Cotton Tee", "confidence": 0.92, "rationale": "ok"})
    product = Product(sku="A", name="Tee", meta_title=None)
    ledger = CostLedger()

    proposals = FixProposalAgent(CONFIG, provider, ledger=ledger).propose(
        [_issue("missing_meta_title")], [product]
    )

    assert len(proposals) == 1
    p = proposals[0]
    assert p.field == "meta_title"
    assert p.proposed_value == "Great Cotton Tee"
    assert p.confidence == 0.92
    assert p.status is ProposalStatus.PENDING


def test_skips_non_fixable_issue_codes() -> None:
    provider = FakeProvider({"value": "x", "confidence": 0.5})
    product = Product(sku="A", name="Tee")

    proposals = FixProposalAgent(CONFIG, provider).propose([_issue("zero_price")], [product])
    assert proposals == []
    assert provider.calls == 0


def test_skips_issue_when_product_missing() -> None:
    provider = FakeProvider({"value": "x", "confidence": 0.5})
    proposals = FixProposalAgent(CONFIG, provider).propose(
        [_issue("missing_meta_title", sku="GHOST")], []
    )
    assert proposals == []


def test_records_tokens_in_ledger_when_provider_reports_them() -> None:
    provider = FakeProvider({"value": "Generated Title", "confidence": 0.8, "tokens": 33})
    product = Product(sku="A", name="Tee", meta_title=None)
    ledger = CostLedger()

    FixProposalAgent(CONFIG, provider, ledger=ledger).propose(
        [_issue("missing_meta_title")], [product]
    )
    assert ledger.per_agent()["FixProposalAgent"] == 33


def test_defaults_confidence_when_provider_omits_it() -> None:
    provider = FakeProvider({"value": "Generated"})
    product = Product(sku="A", name="Tee")
    proposals = FixProposalAgent(CONFIG, provider).propose(
        [_issue("low_quality_description")], [product]
    )
    assert proposals[0].confidence == 0.5

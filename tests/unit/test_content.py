"""Tests for ContentAgent (R-CONTENT) — LLM scoring with structured output."""

from __future__ import annotations

from typing import Any

from catalogguard.agents.content import ContentAgent
from catalogguard.logging.cost import CostLedger
from catalogguard.models import AuditConfig, DetectedBy, Dimension, Product

CONFIG = AuditConfig(store_url="https://app.demo.test", checks=["content"])


class FakeProvider:
    name = "fake"

    def __init__(self, response: dict[str, Any]) -> None:
        self._response = response
        self.calls = 0

    def generate(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        return self._response


def test_flags_low_quality_description_with_llm_problems() -> None:
    provider = FakeProvider(
        {
            "acceptable": False,
            "severity": "high",
            "problems": ["too short", "keyword stuffed"],
            "tokens": 42,
        }
    )
    product = Product(sku="A", name="Tee", description="cheap tee buy cheap tee")
    ledger = CostLedger()

    issues = ContentAgent(CONFIG, provider, ledger=ledger).run([product])

    assert {i.message for i in issues} == {"too short", "keyword stuffed"}
    assert all(i.dimension is Dimension.CONTENT for i in issues)
    assert all(i.detected_by is DetectedBy.LLM for i in issues)
    assert ledger.per_agent()["ContentAgent"] == 42


def test_skips_products_without_description_to_save_tokens() -> None:
    provider = FakeProvider({"acceptable": False, "problems": ["x"]})
    product = Product(sku="A", name="Tee", description=None)

    issues = ContentAgent(CONFIG, provider).run([product])

    assert issues == []
    assert provider.calls == 0  # rules-before-LLM: never spent a token


def test_acceptable_description_yields_no_issues() -> None:
    provider = FakeProvider({"acceptable": True, "problems": []})
    product = Product(sku="A", name="Tee", description="A well written, accurate description.")

    assert ContentAgent(CONFIG, provider).run([product]) == []

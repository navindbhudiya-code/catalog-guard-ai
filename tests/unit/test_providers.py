"""Tests for the provider abstraction (R-PROVIDER) via the offline stub."""

from __future__ import annotations

from catalogguard.agents.content import ContentAgent
from catalogguard.models import AuditConfig, Product
from catalogguard.providers.stub import StubProvider


def test_stub_returns_canned_response_when_configured() -> None:
    provider = StubProvider({"acceptable": False, "problems": ["too short"]})
    result = provider.generate("sys", "user", {"type": "object"})
    assert result["problems"] == ["too short"]


def test_stub_defaults_to_acceptable_when_unconfigured() -> None:
    provider = StubProvider()
    assert provider.generate("sys", "user", {})["acceptable"] is True


def test_stub_satisfies_provider_protocol_for_content_agent() -> None:
    # The stub flags nothing, so an offline content audit finds no issues.
    config = AuditConfig(store_url="https://x", checks=["content"])
    product = Product(sku="A", name="Tee", description="A perfectly fine description here.")
    assert ContentAgent(config, StubProvider()).run([product]) == []

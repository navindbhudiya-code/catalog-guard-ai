"""Tests for the agent registry that wires checks to agents (R-SUPERVISOR)."""

from __future__ import annotations

from typing import Any

import pytest

from catalogguard.agents.attribute import AttributeAgent
from catalogguard.agents.content import ContentAgent
from catalogguard.agents.duplicate import DuplicateAgent
from catalogguard.agents.registry import SUPPORTED_CHECKS, build_agents
from catalogguard.agents.sanity import SanityAgent
from catalogguard.agents.seo import SEOAgent
from catalogguard.models import AuditConfig


class FakeProvider:
    name = "fake"

    def generate(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {}


def test_build_agents_instantiates_requested_rule_checks() -> None:
    config = AuditConfig(store_url="https://x", checks=["sanity", "attribute", "duplicate", "seo"])
    agents = build_agents(config, ["sanity", "attribute", "duplicate", "seo"])

    assert isinstance(agents["sanity"], SanityAgent)
    assert isinstance(agents["attribute"], AttributeAgent)
    assert isinstance(agents["duplicate"], DuplicateAgent)
    assert isinstance(agents["seo"], SEOAgent)


def test_supported_checks_are_exposed() -> None:
    assert {"sanity", "attribute", "duplicate", "seo", "content"} <= set(SUPPORTED_CHECKS)


def test_content_check_requires_a_provider() -> None:
    with pytest.raises(ValueError, match="requires an LLM provider"):
        build_agents(AuditConfig(store_url="https://x"), ["content"])


def test_content_check_builds_with_provider() -> None:
    config = AuditConfig(store_url="https://x", checks=["content"])
    agents = build_agents(config, ["content"], provider=FakeProvider())
    assert isinstance(agents["content"], ContentAgent)


def test_unknown_check_raises() -> None:
    with pytest.raises(KeyError):
        build_agents(AuditConfig(store_url="https://x"), ["bogus"])

"""Tests for the agent registry that wires checks to agents (R-SUPERVISOR)."""

from __future__ import annotations

import pytest

from catalogguard.agents.attribute import AttributeAgent
from catalogguard.agents.duplicate import DuplicateAgent
from catalogguard.agents.registry import SUPPORTED_CHECKS, build_agents
from catalogguard.agents.sanity import SanityAgent
from catalogguard.models import AuditConfig


def test_build_agents_instantiates_requested_checks() -> None:
    config = AuditConfig(store_url="https://x", checks=["sanity", "attribute", "duplicate"])
    agents = build_agents(config, ["sanity", "attribute", "duplicate"])

    assert isinstance(agents["sanity"], SanityAgent)
    assert isinstance(agents["attribute"], AttributeAgent)
    assert isinstance(agents["duplicate"], DuplicateAgent)


def test_supported_checks_are_exposed() -> None:
    assert {"sanity", "attribute", "duplicate"} <= set(SUPPORTED_CHECKS)


def test_unknown_check_raises() -> None:
    with pytest.raises(KeyError):
        build_agents(AuditConfig(store_url="https://x"), ["bogus"])

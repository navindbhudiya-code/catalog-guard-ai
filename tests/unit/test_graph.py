"""Tests for the Supervisor orchestration (R-SUPERVISOR)."""

from __future__ import annotations

from typing import Any

from catalogguard.agents.sanity import SanityAgent
from catalogguard.graph.supervisor import Supervisor
from catalogguard.models import AuditConfig, GraphState, Product


class NullLogger:
    def info(self, event: str, **kw: Any) -> None: ...


def _state(checks: list[str]) -> GraphState:
    config = AuditConfig(store_url="https://app.demo.test", checks=checks)
    products = [Product(sku="A", status=1, price=0, categories=[])]  # trips sanity rules
    return GraphState(config=config, products=products)


def test_supervisor_runs_only_requested_checks() -> None:
    state = _state(["sanity"])
    agents = {"sanity": SanityAgent(state.config)}

    result = Supervisor(agents, NullLogger()).run(state)

    assert result.completed_agents == ["sanity"]
    assert result.issues  # sanity issues were collected
    assert all(i.dimension.value == "sanity" for i in result.issues)


def test_supervisor_skips_already_completed_agents() -> None:
    state = _state(["sanity"])

    class CountingAgent:
        name = "sanity"

        def __init__(self) -> None:
            self.calls = 0

        def run(self, products: list[Product]) -> list:
            self.calls += 1
            return []

    agent = CountingAgent()
    state.mark_agent_done("sanity")  # pretend it already ran

    Supervisor({"sanity": agent}, NullLogger()).run(state)
    assert agent.calls == 0

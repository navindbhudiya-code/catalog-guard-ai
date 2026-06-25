"""Tests for SQLite checkpointing + crash-resume (R-CHECKPOINT)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from catalogguard.agents.attribute import AttributeAgent
from catalogguard.agents.sanity import SanityAgent
from catalogguard.graph.supervisor import Supervisor
from catalogguard.models import AuditConfig, GraphState, Product
from catalogguard.storage.checkpoint import AuditCheckpoint


class NullLogger:
    def info(self, event: str, **kw: Any) -> None: ...


def _state() -> GraphState:
    config = AuditConfig(
        store_url="https://app.demo.test",
        checks=["sanity", "attribute"],
        required_attributes=["brand"],
    )
    products = [Product(sku="A", status=1, price=0, categories=[], images=[])]
    return GraphState(config=config, products=products)


def test_checkpoint_roundtrips_state(tmp_path: Path) -> None:
    cp = AuditCheckpoint(tmp_path / "cp.sqlite")
    state = _state()
    state.mark_agent_done("sanity")

    cp.save("run1", state)
    cp.close()

    reopened = AuditCheckpoint(tmp_path / "cp.sqlite")
    loaded = reopened.load("run1")
    assert loaded is not None
    assert loaded.completed_agents == ["sanity"]
    assert reopened.load("missing") is None
    reopened.close()


def test_audit_resumes_after_crash_without_rerunning_completed_agents(tmp_path: Path) -> None:
    cp = AuditCheckpoint(tmp_path / "cp.sqlite")
    state = _state()

    class Boom:
        name = "attribute"

        def run(self, products: list[Product]) -> list:
            raise RuntimeError("crashed mid-audit")

    # First run: sanity succeeds + checkpoints, attribute crashes.
    crashing = {"sanity": SanityAgent(state.config), "attribute": Boom()}
    with pytest.raises(RuntimeError):
        Supervisor(crashing, NullLogger(), checkpoint=cp, run_id="run1").run(state)

    saved = cp.load("run1")
    assert saved is not None
    assert saved.completed_agents == ["sanity"]
    sanity_issue_count = len(saved.issues)
    assert sanity_issue_count > 0

    # Resume: sanity must be skipped, attribute now runs to completion.
    class CountingSanity(SanityAgent):
        calls = 0

        def run(self, products: list[Product]) -> list:
            type(self).calls += 1
            return super().run(products)

    healthy = {
        "sanity": CountingSanity(saved.config),
        "attribute": AttributeAgent(saved.config),
    }
    final = Supervisor(healthy, NullLogger(), checkpoint=cp, run_id="run1").run(saved)

    assert CountingSanity.calls == 0  # never re-ran the completed agent
    assert final.completed_agents == ["sanity", "attribute"]
    # Sanity issues were not duplicated by the resume.
    assert sum(1 for i in final.issues if i.dimension.value == "sanity") == sanity_issue_count
    assert any(i.dimension.value == "attribute" for i in final.issues)
    cp.close()

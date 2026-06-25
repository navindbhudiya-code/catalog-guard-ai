"""Tests for the approval store (R-HITL)."""

from __future__ import annotations

from pathlib import Path

from catalogguard.models import FixProposal, ProposalStatus
from catalogguard.storage.approval import ApprovalStore


def _proposal(pid: str, confidence: float) -> FixProposal:
    return FixProposal(
        id=pid,
        issue_id="i",
        sku="A",
        field="meta_title",
        proposed_value=f"value-{pid}",
        confidence=confidence,
    )


def test_save_and_query_by_status() -> None:
    store = ApprovalStore()
    store.save_many([_proposal("p1", 0.9), _proposal("p2", 0.5)])

    assert {p.id for p in store.by_status(ProposalStatus.PENDING)} == {"p1", "p2"}
    assert store.get("p1").proposed_value == "value-p1"  # type: ignore[union-attr]
    store.close()


def test_set_status_transitions_a_proposal() -> None:
    store = ApprovalStore()
    store.save_many([_proposal("p1", 0.9)])

    store.set_status("p1", ProposalStatus.APPROVED)
    assert store.get("p1").status is ProposalStatus.APPROVED  # type: ignore[union-attr]
    store.close()


def test_edit_updates_value_and_approves() -> None:
    store = ApprovalStore()
    store.save_many([_proposal("p1", 0.9)])

    store.edit("p1", "Hand-edited title")
    edited = store.get("p1")
    assert edited is not None
    assert edited.proposed_value == "Hand-edited title"
    assert edited.status is ProposalStatus.APPROVED
    store.close()


def test_bulk_approve_by_confidence_threshold() -> None:
    store = ApprovalStore()
    store.save_many([_proposal("hi", 0.95), _proposal("lo", 0.40)])

    count = store.bulk_approve(min_confidence=0.9)

    assert count == 1
    assert store.get("hi").status is ProposalStatus.APPROVED  # type: ignore[union-attr]
    assert store.get("lo").status is ProposalStatus.PENDING  # type: ignore[union-attr]
    store.close()


def test_set_status_and_edit_are_noops_for_unknown_id() -> None:
    store = ApprovalStore()
    store.set_status("ghost", ProposalStatus.APPROVED)  # must not raise
    store.edit("ghost", "x")  # must not raise
    assert store.get("ghost") is None
    store.close()


def test_store_persists_across_reopen(tmp_path: Path) -> None:
    db = tmp_path / "approvals.sqlite"
    store = ApprovalStore(db)
    store.save_many([_proposal("p1", 0.9)])
    store.close()

    reopened = ApprovalStore(db)
    assert reopened.get("p1") is not None
    assert reopened.get("missing") is None
    reopened.close()

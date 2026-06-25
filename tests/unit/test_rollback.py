"""Tests for the ApplyAgent + rollback journal (R-ROLLBACK)."""

from __future__ import annotations

from pathlib import Path

from catalogguard.agents.apply import ApplyAgent
from catalogguard.models import FixProposal, ProposalStatus
from catalogguard.storage.rollback import RollbackJournal


class FakeWriter:
    """Records writes instead of calling Magento."""

    def __init__(self) -> None:
        self.writes: list[tuple[str, str, object]] = []

    def update_field(self, sku: str, field: str, value: object) -> None:
        self.writes.append((sku, field, value))


def _approved(pid: str, value: str) -> FixProposal:
    return FixProposal(
        id=pid,
        issue_id="i",
        sku="A",
        field="meta_title",
        current_value="old title",
        proposed_value=value,
        confidence=0.9,
        status=ProposalStatus.APPROVED,
    )


def test_apply_writes_only_approved_and_journals_previous_value() -> None:
    writer = FakeWriter()
    journal = RollbackJournal()
    pending = _approved("p1", "New Title")
    pending.status = ProposalStatus.PENDING  # not approved -> must be skipped

    applied = ApplyAgent(writer, journal).apply(
        [_approved("p2", "New Title"), pending], batch_id="b1"
    )

    assert [p.id for p in applied] == ["p2"]
    assert writer.writes == [("A", "meta_title", "New Title")]
    assert applied[0].status is ProposalStatus.APPLIED
    entries = journal.entries("b1")
    assert len(entries) == 1
    assert entries[0].old_value == "old title"
    journal.close()


def test_revert_restores_previous_values_and_marks_reverted() -> None:
    writer = FakeWriter()
    journal = RollbackJournal()
    agent = ApplyAgent(writer, journal)
    agent.apply([_approved("p1", "New Title")], batch_id="b1")
    writer.writes.clear()

    reverted = agent.revert("b1")

    assert reverted == 1
    assert writer.writes == [("A", "meta_title", "old title")]  # restored
    assert journal.entries("b1") == []  # batch consumed by revert
    journal.close()


def test_journal_persists_across_reopen(tmp_path: Path) -> None:
    db = tmp_path / "journal.sqlite"
    journal = RollbackJournal(db)
    journal.record("b1", "A", "meta_title", old_value="old", new_value="new", proposal_id="p1")
    journal.close()

    reopened = RollbackJournal(db)
    assert len(reopened.entries("b1")) == 1
    reopened.close()

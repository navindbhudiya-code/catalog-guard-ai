"""SQLite approval store for the human-in-the-loop review queue (R-HITL)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from catalogguard.models import FixProposal, ProposalStatus

_SCHEMA = """
CREATE TABLE IF NOT EXISTS proposals (
    id      TEXT PRIMARY KEY,
    status  TEXT NOT NULL,
    payload TEXT NOT NULL
);
"""


class ApprovalStore:
    """Persists fix proposals and their approval state."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def save_many(self, proposals: list[FixProposal]) -> None:
        """Insert or replace proposals."""
        self._conn.executemany(
            "INSERT OR REPLACE INTO proposals (id, status, payload) VALUES (?, ?, ?)",
            [(p.id, p.status.value, p.model_dump_json()) for p in proposals],
        )
        self._conn.commit()

    def get(self, proposal_id: str) -> FixProposal | None:
        """Return a proposal by id, or None."""
        row = self._conn.execute(
            "SELECT payload FROM proposals WHERE id = ?", (proposal_id,)
        ).fetchone()
        if row is None:
            return None
        return FixProposal.model_validate_json(row["payload"])

    def by_status(self, status: ProposalStatus) -> list[FixProposal]:
        """Return all proposals in a given status."""
        rows = self._conn.execute(
            "SELECT payload FROM proposals WHERE status = ?", (status.value,)
        ).fetchall()
        return [FixProposal.model_validate_json(row["payload"]) for row in rows]

    def set_status(self, proposal_id: str, status: ProposalStatus) -> None:
        """Transition a proposal to a new status."""
        proposal = self.get(proposal_id)
        if proposal is None:
            return
        proposal.status = status
        self.save_many([proposal])

    def edit(self, proposal_id: str, new_value: object) -> None:
        """Replace the proposed value and approve it (edit-then-approve)."""
        proposal = self.get(proposal_id)
        if proposal is None:
            return
        proposal.proposed_value = new_value
        proposal.status = ProposalStatus.APPROVED
        self.save_many([proposal])

    def bulk_approve(self, min_confidence: float) -> int:
        """Approve all pending proposals at or above a confidence threshold."""
        approved = 0
        for proposal in self.by_status(ProposalStatus.PENDING):
            if proposal.confidence >= min_confidence:
                proposal.status = ProposalStatus.APPROVED
                self.save_many([proposal])
                approved += 1
        return approved

    def close(self) -> None:
        """Close the underlying connection."""
        self._conn.close()

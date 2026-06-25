"""ApplyAgent — writes APPROVED fixes back to the store with a rollback journal (R-ROLLBACK)."""

from __future__ import annotations

from typing import Any, Protocol

from catalogguard.models import FixProposal, ProposalStatus
from catalogguard.storage.rollback import RollbackJournal


class CatalogWriter(Protocol):
    """The single write operation the ApplyAgent needs."""

    def update_field(self, sku: str, field: str, value: Any) -> None: ...


class ApplyAgent:
    """Applies approved fixes and supports one-command revert.

    Never touches a proposal that is not ``APPROVED``, and always journals the
    previous value *before* writing, so any batch can be reverted.
    """

    name = "ApplyAgent"

    def __init__(self, writer: CatalogWriter, journal: RollbackJournal) -> None:
        self._writer = writer
        self._journal = journal

    def apply(self, proposals: list[FixProposal], batch_id: str) -> list[FixProposal]:
        """Apply every approved proposal; returns the ones applied."""
        applied: list[FixProposal] = []
        for proposal in proposals:
            if not proposal.is_approved:
                continue
            self._journal.record(
                batch_id,
                proposal.sku,
                proposal.field,
                old_value=proposal.current_value,
                new_value=proposal.proposed_value,
                proposal_id=proposal.id,
            )
            self._writer.update_field(proposal.sku, proposal.field, proposal.proposed_value)
            proposal.status = ProposalStatus.APPLIED
            applied.append(proposal)
        return applied

    def revert(self, batch_id: str) -> int:
        """Restore previous values for a batch; returns entries reverted."""
        entries = self._journal.entries(batch_id)
        for entry in reversed(entries):
            self._writer.update_field(entry.sku, entry.field, entry.old_value)
        self._journal.mark_reverted(batch_id)
        return len(entries)

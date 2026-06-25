"""The FixProposal model — a proposed, approvable change to one field."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import ProposalStatus


class FixProposal(BaseModel):
    """A proposed fix for an Issue, pending human approval.

    ``current_value`` is captured so the ApplyAgent can write a rollback-journal
    entry before mutating the store.
    """

    id: str = Field(default_factory=lambda: uuid4().hex)
    issue_id: str
    sku: str
    field: str
    current_value: Any | None = None
    proposed_value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""
    status: ProposalStatus = ProposalStatus.PENDING

    @property
    def is_approved(self) -> bool:
        """True only when a human has approved this proposal."""
        return self.status is ProposalStatus.APPROVED

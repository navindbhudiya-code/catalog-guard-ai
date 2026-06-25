"""The AuditReport model — the consolidated output of an audit run."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from .issue import Issue
from .proposal import FixProposal


def _now() -> datetime:
    return datetime.now(tz=UTC)


class AuditReport(BaseModel):
    """Everything an audit produced: issues, proposals, and cost accounting."""

    store_url: str
    generated_at: datetime = Field(default_factory=_now)
    products_scanned: int = 0
    checks_run: list[str] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)
    proposals: list[FixProposal] = Field(default_factory=list)
    token_cost: dict[str, int] = Field(default_factory=dict)

    @property
    def issue_count(self) -> int:
        """Total number of issues found."""
        return len(self.issues)

    def counts_by_dimension(self) -> dict[str, int]:
        """Issue counts keyed by audit dimension."""
        return dict(Counter(issue.dimension.value for issue in self.issues))

    def counts_by_severity(self) -> dict[str, int]:
        """Issue counts keyed by severity."""
        return dict(Counter(issue.severity.value for issue in self.issues))

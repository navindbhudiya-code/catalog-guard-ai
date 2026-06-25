"""AuditConfig and GraphState — the typed state flowing through the graph."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .enums import Dimension
from .issue import Issue
from .product import Product
from .proposal import FixProposal


class AuditConfig(BaseModel):
    """User-supplied configuration for one audit run.

    ``checks`` holds the dimensions the Supervisor should run (e.g. ``["seo",
    "sanity"]``), letting users run "SEO only" or a full audit.
    """

    store_url: str
    checks: list[str] = Field(default_factory=list)
    similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    required_attributes: list[str] = Field(default_factory=list)
    max_products: int | None = None

    def should_run(self, dimension: Dimension) -> bool:
        """Whether the given dimension is in scope for this run."""
        return dimension.value in self.checks


class GraphState(BaseModel):
    """Shared, typed state passed between LangGraph nodes."""

    config: AuditConfig
    products: list[Product] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)
    proposals: list[FixProposal] = Field(default_factory=list)
    cursor: int = 0
    token_ledger: dict[str, int] = Field(default_factory=dict)
    completed_agents: list[str] = Field(default_factory=list)

    def record_tokens(self, agent: str, tokens: int) -> None:
        """Accumulate token usage for an agent (rules-before-LLM cost tracking)."""
        self.token_ledger[agent] = self.token_ledger.get(agent, 0) + tokens

    def mark_agent_done(self, agent: str) -> None:
        """Record that an agent finished; idempotent so resumes don't duplicate."""
        if agent not in self.completed_agents:
            self.completed_agents.append(agent)

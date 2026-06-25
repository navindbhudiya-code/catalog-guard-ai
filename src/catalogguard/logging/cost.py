"""Per-agent token and cost accounting (R-COST)."""

from __future__ import annotations

from collections import defaultdict


class CostLedger:
    """Accumulates token usage per agent and estimates spend.

    Rules-before-LLM means most products never reach a token; this ledger makes
    the savings visible by reporting exactly where tokens were spent.
    """

    def __init__(self) -> None:
        self._tokens: dict[str, int] = defaultdict(int)

    def record(self, agent: str, tokens: int) -> None:
        """Add token usage for an agent."""
        self._tokens[agent] += tokens

    def per_agent(self) -> dict[str, int]:
        """Token totals keyed by agent."""
        return dict(self._tokens)

    def total_tokens(self) -> int:
        """Total tokens across all agents."""
        return sum(self._tokens.values())

    def estimated_cost_usd(self, usd_per_1k: float = 0.003) -> float:
        """Estimate spend at a given $/1k-token rate."""
        return self.total_tokens() / 1000 * usd_per_1k

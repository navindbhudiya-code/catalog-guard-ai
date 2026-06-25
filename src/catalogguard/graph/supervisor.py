"""Supervisor — orchestrates the selected audit agents over shared state.

This is the native orchestration engine: it runs the agents named in
``config.checks``, accumulates their issues into ``GraphState``, and checkpoints
after each agent so a crashed audit resumes without re-running completed work.
A LangGraph ``StateGraph`` adapter (the ``[llm]`` extra) wraps these same agents
for tracing in Phase 3 — see ``docs/decisions/ADR-002``.
"""

from __future__ import annotations

from typing import Any

from catalogguard.agents.base import AuditAgent
from catalogguard.models import GraphState
from catalogguard.storage.checkpoint import AuditCheckpoint


class Supervisor:
    """Runs requested agents in order, accumulating issues and checkpointing."""

    def __init__(
        self,
        agents: dict[str, AuditAgent],
        logger: Any,
        *,
        checkpoint: AuditCheckpoint | None = None,
        run_id: str = "default",
    ) -> None:
        self._agents = agents
        self._log = logger
        self._checkpoint = checkpoint
        self._run_id = run_id

    def run(self, state: GraphState) -> GraphState:
        """Execute the audit, returning the updated state."""
        for dimension in state.config.checks:
            if dimension in state.completed_agents:
                self._log.info("skip_completed", agent=dimension)
                continue

            agent = self._agents[dimension]
            issues = agent.run(state.products)
            state.issues.extend(issues)
            state.mark_agent_done(dimension)

            if self._checkpoint is not None:
                self._checkpoint.save(self._run_id, state)
            self._log.info("agent_complete", agent=dimension, issues=len(issues))

        return state

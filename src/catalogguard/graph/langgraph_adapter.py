"""Optional LangGraph StateGraph wrapper over the native agents (R-SUPERVISOR).

Requires the ``[llm]`` extra (langgraph). Each audit agent becomes a graph node;
LangGraph's SqliteSaver provides checkpointing/tracing. The native Supervisor
remains the tested source of truth (see ADR-002); this adapter is for users who
want LangGraph's tracing. Excluded from the unit-coverage gate.
"""

from __future__ import annotations

from typing import Any

from catalogguard.agents.base import AuditAgent
from catalogguard.models import GraphState


def build_audit_graph(agents: dict[str, AuditAgent], checkpoint_path: str = "audit.sqlite") -> Any:
    """Build and compile a LangGraph StateGraph from the given agents."""
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.graph import END, StateGraph

    builder: Any = StateGraph(GraphState)
    previous: str | None = None
    for name, agent in agents.items():

        def node(state: GraphState, _agent: AuditAgent = agent, _name: str = name) -> GraphState:
            state.issues.extend(_agent.run(state.products))
            state.mark_agent_done(_name)
            return state

        builder.add_node(name, node)
        if previous is None:
            builder.set_entry_point(name)
        else:
            builder.add_edge(previous, name)
        previous = name

    if previous is not None:
        builder.add_edge(previous, END)

    saver = SqliteSaver.from_conn_string(checkpoint_path)
    return builder.compile(checkpointer=saver)

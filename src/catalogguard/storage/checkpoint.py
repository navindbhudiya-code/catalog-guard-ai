"""SQLite checkpoint store for resumable audits (R-CHECKPOINT)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from catalogguard.models import GraphState

_SCHEMA = """
CREATE TABLE IF NOT EXISTS checkpoints (
    run_id TEXT PRIMARY KEY,
    state  TEXT NOT NULL
);
"""


class AuditCheckpoint:
    """Persists GraphState after each agent so a crashed audit can resume.

    A 50,000-SKU audit that dies at SKU 30,000 reloads its last checkpoint and
    skips agents already recorded in ``GraphState.completed_agents``.
    """

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def save(self, run_id: str, state: GraphState) -> None:
        """Persist (or overwrite) the state for a run."""
        self._conn.execute(
            "INSERT OR REPLACE INTO checkpoints (run_id, state) VALUES (?, ?)",
            (run_id, state.model_dump_json()),
        )
        self._conn.commit()

    def load(self, run_id: str) -> GraphState | None:
        """Load the saved state for a run, or None if there is none."""
        row = self._conn.execute(
            "SELECT state FROM checkpoints WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row is None:
            return None
        return GraphState.model_validate_json(row["state"])

    def close(self) -> None:
        """Close the underlying connection."""
        self._conn.close()

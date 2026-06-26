"""Rollback journal: every applied change stores its previous value (R-ROLLBACK)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS journal (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id    TEXT NOT NULL,
    sku         TEXT NOT NULL,
    field       TEXT NOT NULL,
    old_value   TEXT,
    new_value   TEXT,
    proposal_id TEXT NOT NULL,
    reverted    INTEGER NOT NULL DEFAULT 0
);
"""


@dataclass(frozen=True)
class RollbackEntry:
    """One journaled change with the value to restore on revert."""

    batch_id: str
    sku: str
    field: str
    old_value: Any
    new_value: Any
    proposal_id: str


class RollbackJournal:
    """Append-only journal enabling one-command revert of any applied batch."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def record(
        self,
        batch_id: str,
        sku: str,
        field: str,
        *,
        old_value: Any,
        new_value: Any,
        proposal_id: str,
    ) -> None:
        """Journal a change before it is written to the store."""
        self._conn.execute(
            "INSERT INTO journal (batch_id, sku, field, old_value, new_value, proposal_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (batch_id, sku, field, json.dumps(old_value), json.dumps(new_value), proposal_id),
        )
        self._conn.commit()

    def entries(self, batch_id: str) -> list[RollbackEntry]:
        """Return the not-yet-reverted entries for a batch, in apply order."""
        rows = self._conn.execute(
            "SELECT * FROM journal WHERE batch_id = ? AND reverted = 0 ORDER BY id",
            (batch_id,),
        ).fetchall()
        return [
            RollbackEntry(
                batch_id=row["batch_id"],
                sku=row["sku"],
                field=row["field"],
                old_value=json.loads(row["old_value"]),
                new_value=json.loads(row["new_value"]),
                proposal_id=row["proposal_id"],
            )
            for row in rows
        ]

    def mark_reverted(self, batch_id: str) -> None:
        """Mark every entry in a batch as reverted."""
        self._conn.execute("UPDATE journal SET reverted = 1 WHERE batch_id = ?", (batch_id,))
        self._conn.commit()

    def close(self) -> None:
        """Close the underlying connection."""
        self._conn.close()

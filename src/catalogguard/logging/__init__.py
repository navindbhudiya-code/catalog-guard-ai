"""Structured JSON run logging (R-COST foundation)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog


def configure_logging(run_id: str, log_dir: str | Path) -> Any:
    """Configure structlog to emit JSON lines to ``logs/run-<id>.jsonl``.

    Every record is stamped with ``run_id`` so audit runs can be traced and
    correlated after the fact. Returns a bound logger.
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"run-{run_id}.jsonl"
    handle = log_path.open("a", encoding="utf-8")

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.WriteLoggerFactory(file=handle),
        cache_logger_on_first_use=False,
    )
    return structlog.get_logger().bind(run_id=run_id)

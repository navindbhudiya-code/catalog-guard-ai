"""Tests for structured JSON run logging."""

from __future__ import annotations

import json
from pathlib import Path

from catalogguard.logging import configure_logging


def test_configure_logging_writes_json_lines_stamped_with_run_id(tmp_path: Path) -> None:
    log = configure_logging("run42", tmp_path)
    log.info("extracted_page", page=1, count=100)

    log_file = tmp_path / "run-run42.jsonl"
    assert log_file.exists()
    record = json.loads(log_file.read_text().strip().splitlines()[-1])
    assert record["run_id"] == "run42"
    assert record["event"] == "extracted_page"
    assert record["page"] == 1
    assert record["count"] == 100

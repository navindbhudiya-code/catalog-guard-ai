"""Tests for the requirement-traceability checker (R-TRACE)."""

from __future__ import annotations

from pathlib import Path

import pytest

from catalogguard.tools import trace_check

MATRIX = """\
# Matrix

| Req ID | Description | Component | Tests | Eval | ADR | Status |
|--------|-------------|-----------|-------|------|-----|--------|
| R-ONE | first | `src/a.py` | `t/one.py` | — | — | done |
| R-TWO | second | `src/b.py` | `t/two.py`, `t/two2.py` | — | — | planned |
| R-THREE | third | `src/c.py` | `t/miss.py` | — | — | done |
"""


def test_parse_matrix_extracts_id_tests_and_status() -> None:
    reqs = trace_check.parse_matrix(MATRIX)

    assert [r.id for r in reqs] == ["R-ONE", "R-TWO", "R-THREE"]
    one, two, three = reqs
    assert one.status == "done"
    assert one.tests == ["t/one.py"]
    assert two.status == "planned"
    assert two.tests == ["t/two.py", "t/two2.py"]
    assert three.tests == ["t/miss.py"]


def test_parse_matrix_without_table_returns_empty() -> None:
    assert trace_check.parse_matrix("# no table here\n\njust prose\n") == []


def test_parse_matrix_ignores_pipe_lines_before_header_and_non_requirement_rows() -> None:
    matrix = (
        "> a | quoted aside before the header\n"
        "| Req ID | Tests | Status |\n"
        "|--|--|--|\n"
        "| R-ONE | `t/one.py` | done |\n"
        "| Total | 1 | — |\n"  # non-requirement row, must be skipped
    )
    reqs = trace_check.parse_matrix(matrix)
    assert [r.id for r in reqs] == ["R-ONE"]


def test_find_untraced_flags_done_rows_with_missing_tests(tmp_path: Path) -> None:
    (tmp_path / "t").mkdir(parents=True)
    (tmp_path / "t" / "one.py").write_text("x = 1\n")
    # t/miss.py intentionally absent.

    reqs = trace_check.parse_matrix(MATRIX)
    untraced = trace_check.find_untraced(reqs, tmp_path)

    # R-ONE is done + test exists -> ok. R-TWO is planned -> skipped.
    # R-THREE is done but its test file is missing -> flagged.
    assert untraced == ["R-THREE"]


def test_find_untraced_flags_done_row_with_no_tests(tmp_path: Path) -> None:
    matrix = "| Req ID | Tests | Status |\n|--|--|--|\n| R-X | — | done |\n"
    reqs = trace_check.parse_matrix(matrix)
    assert trace_check.find_untraced(reqs, tmp_path) == ["R-X"]


def test_main_returns_zero_when_all_done_requirements_traced(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "TRACEABILITY.md").write_text(
        "| Req ID | Tests | Status |\n|--|--|--|\n| R-OK | `tests/unit/test_ok.py` | done |\n"
    )
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "unit" / "test_ok.py").write_text("x = 1\n")

    code = trace_check.main(["--repo-root", str(tmp_path)])

    assert code == 0
    assert "traceable" in capsys.readouterr().out.lower()


def test_main_returns_one_and_reports_when_untraced(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "TRACEABILITY.md").write_text(
        "| Req ID | Tests | Status |\n|--|--|--|\n| R-BAD | `tests/unit/test_nope.py` | done |\n"
    )

    code = trace_check.main(["--repo-root", str(tmp_path)])

    out = capsys.readouterr().out
    assert code == 1
    assert "R-BAD" in out


def test_main_defaults_repo_root_to_package_parent(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # With no --repo-root, it resolves the real repo and checks the committed matrix.
    code = trace_check.main([])
    capsys.readouterr()
    assert code == 0

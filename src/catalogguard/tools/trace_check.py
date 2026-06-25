"""Machine-check the requirement traceability matrix (R-TRACE).

Parses ``docs/TRACEABILITY.md`` and fails the build if any requirement whose
status is ``done`` references a test file that does not exist on disk. ``planned``
requirements are listed but not gated, so the matrix can stay complete while the
project is built phase by phase.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

_PLACEHOLDERS = {"", "-", "—", "n/a", "tbd"}


@dataclass(frozen=True)
class Requirement:
    """One row of the traceability matrix."""

    id: str
    tests: list[str]
    status: str


def _split_row(line: str) -> list[str]:
    """Split a markdown table row into trimmed cells."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _clean_tests(cell: str) -> list[str]:
    """Extract test paths from a Tests cell, dropping backticks and placeholders."""
    refs: list[str] = []
    for raw in cell.split(","):
        ref = raw.strip().strip("`").strip()
        if ref.lower() not in _PLACEHOLDERS:
            refs.append(ref)
    return refs


def parse_matrix(markdown: str) -> list[Requirement]:
    """Parse a traceability-matrix markdown table into Requirement rows."""
    header: list[str] | None = None
    requirements: list[Requirement] = []

    for line in markdown.splitlines():
        if "|" not in line:
            continue
        cells = _split_row(line)
        lowered = [c.lower() for c in cells]
        if header is None:
            if "req id" in lowered:
                header = lowered
            continue
        if set("".join(cells)) <= {"-", ":"}:  # separator row
            continue
        row = dict(zip(header, cells, strict=False))
        req_id = row.get("req id", "")
        if not req_id.startswith("R-"):
            continue
        requirements.append(
            Requirement(
                id=req_id,
                tests=_clean_tests(row.get("tests", "")),
                status=row.get("status", "").lower(),
            )
        )
    return requirements


def find_untraced(requirements: list[Requirement], repo_root: Path) -> list[str]:
    """Return ids of ``done`` requirements lacking an existing test file."""
    untraced: list[str] = []
    for req in requirements:
        if req.status != "done":
            continue
        existing = [t for t in req.tests if (repo_root / t).exists()]
        if not existing:
            untraced.append(req.id)
    return untraced


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code (0 ok, 1 untraced)."""
    parser = argparse.ArgumentParser(description="Check requirement traceability.")
    default_root = Path(__file__).resolve().parents[3]
    parser.add_argument("--repo-root", type=Path, default=default_root)
    args = parser.parse_args(argv)

    matrix_path = args.repo_root / "docs" / "TRACEABILITY.md"
    requirements = parse_matrix(matrix_path.read_text(encoding="utf-8"))
    untraced = find_untraced(requirements, args.repo_root)

    done = sum(1 for r in requirements if r.status == "done")
    if untraced:
        print(f"❌ {len(untraced)} requirement(s) marked done without a resolvable test:")
        for req_id in untraced:
            print(f"   - {req_id}")
        return 1

    print(f"✅ traceable — {done} done requirement(s), all backed by an existing test.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

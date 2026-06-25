"""Eval runner: score the audit on the synthetic catalog and emit a scorecard.

Usage:
    python evals/score.py                 # print scorecard
    python evals/score.py --write-baseline
    python evals/score.py --check-baseline  # CI gate: fail if F1 drops below baseline

The scoring logic lives in ``catalogguard.evals`` (unit-tested at 100%); this is a
thin runner around it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from catalogguard.agents.registry import build_agents
from catalogguard.evals.scoring import render_scorecard, score_by_dimension
from catalogguard.evals.synthetic import generate_catalog
from catalogguard.graph.supervisor import Supervisor
from catalogguard.models import AuditConfig, GraphState

_CHECKS = ["sanity", "attribute", "duplicate", "seo"]
_BASELINE = Path(__file__).parent / "baseline.json"


class _Logger:
    def info(self, event: str, **kw: object) -> None: ...


def run() -> dict[str, float]:
    products, expected = generate_catalog()
    config = AuditConfig(store_url="synthetic", checks=_CHECKS)
    state = GraphState(config=config, products=products)
    Supervisor(build_agents(config, _CHECKS), _Logger()).run(state)
    detected = {(i.sku, i.dimension.value, i.code) for i in state.issues}
    per_dim = score_by_dimension(expected, detected)
    print(render_scorecard(per_dim))
    return {dim: round(metric.f1, 4) for dim, metric in per_dim.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--check-baseline", action="store_true")
    args = parser.parse_args(argv)

    f1_by_dim = run()

    if args.write_baseline:
        _BASELINE.write_text(json.dumps(f1_by_dim, indent=2), encoding="utf-8")
        print(f"Wrote baseline to {_BASELINE}")
        return 0

    if args.check_baseline:
        if not _BASELINE.exists():
            print("No baseline.json — run with --write-baseline first.")
            return 1
        baseline = json.loads(_BASELINE.read_text(encoding="utf-8"))
        regressions = [dim for dim, f1 in baseline.items() if f1_by_dim.get(dim, 0.0) < f1 - 1e-9]
        if regressions:
            print(f"F1 regressed for: {', '.join(regressions)}")
            return 1
        print("Eval gate passed: no F1 regression.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

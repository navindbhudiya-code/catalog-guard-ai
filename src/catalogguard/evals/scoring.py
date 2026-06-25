"""Precision / recall / F1 scoring for audit results (R-EVAL)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

# A labelled finding: (sku, dimension, code).
Finding = tuple[str, str, str]


@dataclass(frozen=True)
class Metric:
    """Precision/recall/F1 with the underlying confusion counts."""

    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    fn: int


def prf(expected: set[Finding], detected: set[Finding]) -> Metric:
    """Compute precision/recall/F1 between expected and detected findings."""
    tp = len(expected & detected)
    fp = len(detected - expected)
    fn = len(expected - detected)
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return Metric(precision, recall, f1, tp, fp, fn)


def _by_dimension(findings: set[Finding]) -> dict[str, set[Finding]]:
    grouped: dict[str, set[Finding]] = defaultdict(set)
    for finding in findings:
        grouped[finding[1]].add(finding)
    return grouped


def score_by_dimension(expected: set[Finding], detected: set[Finding]) -> dict[str, Metric]:
    """Compute a Metric per dimension across expected and detected findings."""
    exp = _by_dimension(expected)
    det = _by_dimension(detected)
    dimensions = sorted(set(exp) | set(det))
    return {dim: prf(exp.get(dim, set()), det.get(dim, set())) for dim in dimensions}


def render_scorecard(per_dimension: dict[str, Metric]) -> str:
    """Render a markdown scorecard table from per-dimension metrics."""
    lines = [
        "| Dimension | Precision | Recall | F1 |",
        "| --- | --- | --- | --- |",
    ]
    for dimension, metric in per_dimension.items():
        lines.append(
            f"| {dimension} | {metric.precision:.2f} | {metric.recall:.2f} | {metric.f1:.2f} |"
        )
    return "\n".join(lines) + "\n"

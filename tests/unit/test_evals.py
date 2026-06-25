"""Tests for the eval harness (R-EVAL) — synthetic catalog + scoring."""

from __future__ import annotations

from catalogguard.agents.registry import build_agents
from catalogguard.evals.scoring import prf, render_scorecard, score_by_dimension
from catalogguard.evals.synthetic import generate_catalog
from catalogguard.graph.supervisor import Supervisor
from catalogguard.models import AuditConfig, GraphState


class NullLogger:
    def info(self, event: str, **kw: object) -> None: ...


def _detected(products: list, checks: list[str]) -> set[tuple[str, str, str]]:
    config = AuditConfig(store_url="https://x", checks=checks)
    state = GraphState(config=config, products=products)
    Supervisor(build_agents(config, checks), NullLogger()).run(state)
    return {(i.sku, i.dimension.value, i.code) for i in state.issues}


def test_prf_is_perfect_on_exact_match() -> None:
    s = {("A", "seo", "missing_meta_title")}
    metric = prf(s, s)
    assert (metric.precision, metric.recall, metric.f1) == (1.0, 1.0, 1.0)


def test_prf_penalizes_false_positives_and_negatives() -> None:
    expected = {("A", "seo", "x"), ("B", "seo", "y")}
    detected = {("A", "seo", "x"), ("C", "seo", "z")}  # 1 tp, 1 fp, 1 fn
    metric = prf(expected, detected)
    assert metric.precision == 0.5
    assert metric.recall == 0.5
    assert round(metric.f1, 3) == 0.5


def test_prf_empty_sets_are_perfect() -> None:
    metric = prf(set(), set())
    assert metric.f1 == 1.0  # nothing to find, nothing wrongly found


def test_audit_scores_high_on_synthetic_catalog() -> None:
    products, expected = generate_catalog()
    checks = ["sanity", "attribute", "duplicate", "seo"]
    detected = _detected(products, checks)

    per_dim = score_by_dimension(expected, detected)
    # Deterministic rules should perfectly recover every injected defect.
    for dimension, metric in per_dim.items():
        assert metric.f1 == 1.0, f"{dimension} imperfect: {metric}"


def test_render_scorecard_produces_markdown_table() -> None:
    products, expected = generate_catalog()
    detected = _detected(products, ["sanity", "attribute", "duplicate", "seo"])
    md = render_scorecard(score_by_dimension(expected, detected))
    assert "| Dimension | Precision | Recall | F1 |" in md
    assert "sanity" in md

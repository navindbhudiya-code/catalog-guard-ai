"""Tests for audit report building + markdown rendering (R-SANITY/R-SUPERVISOR output)."""

from __future__ import annotations

from catalogguard.models import AuditConfig, Dimension, GraphState, Issue, Product, Severity
from catalogguard.reporting import build_report, render_markdown


def _state_with_issues() -> GraphState:
    config = AuditConfig(store_url="https://app.demo.test", checks=["sanity"])
    state = GraphState(config=config, products=[Product(sku="A"), Product(sku="B")])
    state.issues.append(
        Issue(
            sku="A",
            dimension=Dimension.SANITY,
            severity=Severity.HIGH,
            code="zero_price",
            message="m",
        )
    )
    state.token_ledger["SanityAgent"] = 0
    return state


def test_build_report_carries_state_into_report() -> None:
    report = build_report(_state_with_issues(), products_scanned=2)
    assert report.store_url == "https://app.demo.test"
    assert report.products_scanned == 2
    assert report.checks_run == ["sanity"]
    assert report.issue_count == 1
    assert report.counts_by_dimension() == {"sanity": 1}


def test_render_markdown_includes_summary_and_issue_rows() -> None:
    report = build_report(_state_with_issues(), products_scanned=2)
    md = render_markdown(report)

    assert "# CatalogGuard Audit Report" in md
    assert "https://app.demo.test" in md
    assert "Products scanned" in md
    assert "zero_price" in md
    assert "| A |" in md  # issue row for SKU A


def test_render_markdown_handles_clean_catalog() -> None:
    config = AuditConfig(store_url="https://app.demo.test", checks=["sanity"])
    report = build_report(GraphState(config=config), products_scanned=0)
    md = render_markdown(report)
    assert "No issues found" in md

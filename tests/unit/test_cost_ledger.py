"""Tests for per-agent token/cost tracking (R-COST)."""

from __future__ import annotations

from catalogguard.logging.cost import CostLedger


def test_records_and_totals_tokens_per_agent() -> None:
    ledger = CostLedger()
    ledger.record("ContentAgent", 120)
    ledger.record("ContentAgent", 80)
    ledger.record("SEOAgent", 50)

    assert ledger.per_agent() == {"ContentAgent": 200, "SEOAgent": 50}
    assert ledger.total_tokens() == 250


def test_estimates_cost_from_rate() -> None:
    ledger = CostLedger()
    ledger.record("ContentAgent", 1000)
    # 1000 tokens at $0.003 / 1k tokens = $0.003
    assert round(ledger.estimated_cost_usd(usd_per_1k=0.003), 6) == 0.003


def test_empty_ledger_is_zero() -> None:
    ledger = CostLedger()
    assert ledger.total_tokens() == 0
    assert ledger.estimated_cost_usd() == 0.0

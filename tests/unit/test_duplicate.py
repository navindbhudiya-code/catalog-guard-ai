"""Tests for duplicate / near-duplicate detection (R-DUP)."""

from __future__ import annotations

from catalogguard.agents.duplicate import DuplicateAgent
from catalogguard.models import AuditConfig, Dimension, Product
from catalogguard.providers.similarity import InMemorySimilarityIndex


def _config(threshold: float) -> AuditConfig:
    return AuditConfig(
        store_url="https://app.demo.test", checks=["duplicate"], similarity_threshold=threshold
    )


# --- InMemorySimilarityIndex ---------------------------------------------


def test_inmemory_index_scores_identical_text_as_one() -> None:
    index = InMemorySimilarityIndex()
    index.add("a", "red cotton tee")
    index.add("b", "red cotton tee")
    results = dict(index.query("red cotton tee", k=5))
    assert round(results["a"], 6) == 1.0


def test_inmemory_index_scores_disjoint_text_as_zero() -> None:
    index = InMemorySimilarityIndex()
    index.add("a", "blue denim jeans")
    assert dict(index.query("red cotton tee", k=5))["a"] == 0.0


def test_inmemory_index_handles_empty_query() -> None:
    index = InMemorySimilarityIndex()
    index.add("a", "anything")
    assert dict(index.query("", k=5))["a"] == 0.0


def test_inmemory_index_respects_k_limit() -> None:
    index = InMemorySimilarityIndex()
    for i in range(5):
        index.add(f"s{i}", "red cotton tee number")
    assert len(index.query("red cotton tee", k=2)) == 2


# --- DuplicateAgent ------------------------------------------------------


def test_identical_products_flagged_as_exact_duplicates() -> None:
    products = [
        Product(sku="A", name="Red Tee", description="Soft cotton."),
        Product(sku="B", name="Red Tee", description="Soft cotton."),
    ]
    issues = DuplicateAgent(_config(0.5)).run(products)
    codes = [i.code for i in issues]
    assert codes.count("exact_duplicate") == 2
    assert "near_duplicate" not in codes  # exact pair is not double-reported as near
    assert all(i.dimension is Dimension.DUPLICATE for i in issues)


def test_similar_products_flagged_as_single_near_duplicate() -> None:
    products = [
        Product(sku="A", name="Red Cotton T-Shirt Large"),
        Product(sku="B", name="Red Cotton T-Shirt Small"),
    ]
    issues = DuplicateAgent(_config(0.5)).run(products)
    near = [i for i in issues if i.code == "near_duplicate"]
    assert len(near) == 1
    assert near[0].current_value["duplicate_of"] in {"A", "B"}


def test_dissimilar_products_yield_no_duplicate_issues() -> None:
    products = [
        Product(sku="A", name="Red Cotton Tee"),
        Product(sku="B", name="Leather Office Chair"),
    ]
    assert DuplicateAgent(_config(0.85)).run(products) == []


def test_threshold_boundary_uses_injected_index() -> None:
    class FakeIndex:
        # The A-B pair has similarity 0.80 from either direction.
        def add(self, doc_id: str, text: str) -> None:
            pass

        def query(self, text: str, k: int) -> list[tuple[str, float]]:
            if text == "x":  # product A querying
                return [("A", 1.0), ("B", 0.80)]
            return [("B", 1.0), ("A", 0.80)]  # product B querying

    products = [Product(sku="A", name="x"), Product(sku="B", name="y")]
    # threshold above 0.80 -> the A/B pair (sim 0.80) is below cutoff -> no near dup.
    assert DuplicateAgent(_config(0.85), index_factory=FakeIndex).run(products) == []
    # threshold at/below 0.80 -> flagged.
    near = DuplicateAgent(_config(0.80), index_factory=FakeIndex).run(products)
    assert [i.code for i in near] == ["near_duplicate"]

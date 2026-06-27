"""Opt-in integration test for the FastAPI review app (R-HITL).

Skipped unless the ``[api]`` extra (fastapi) is installed.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from catalogguard.models import FixProposal, ProposalStatus
from catalogguard.storage.approval import ApprovalStore

pytestmark = pytest.mark.integration


class _FakeWriter:
    """Records catalog writes instead of calling Magento."""

    def __init__(self) -> None:
        self.writes: list[tuple[str, str, object]] = []

    def update_field(self, sku: str, field: str, value: object) -> None:
        self.writes.append((sku, field, value))


def _store() -> ApprovalStore:
    store = ApprovalStore()
    store.save_many(
        [
            FixProposal(
                id="p1",
                issue_id="i",
                sku="TS-01",
                field="meta_title",
                proposed_value="Great Tee",
                confidence=0.95,
            )
        ]
    )
    return store


def test_index_lists_pending_proposal() -> None:
    from api.app import create_app

    client = TestClient(create_app(_store()))
    response = client.get("/")
    assert response.status_code == 200
    assert "TS-01" in response.text
    assert "Great Tee" in response.text


def test_approve_transitions_proposal() -> None:
    from api.app import create_app

    store = _store()
    client = TestClient(create_app(store))
    response = client.post("/proposals/p1/approve")
    assert response.status_code == 200
    assert store.get("p1").status is ProposalStatus.APPROVED  # type: ignore[union-attr]


def test_apply_then_rollback_round_trip(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from api.app import create_app

    store = _store()
    store.save_many(
        [
            FixProposal(
                id="p1",
                issue_id="i",
                sku="TS-01",
                field="meta_title",
                current_value="Old Title",
                proposed_value="Great Tee",
                confidence=0.95,
                status=ProposalStatus.APPROVED,
            )
        ]
    )
    writer = _FakeWriter()
    client = TestClient(create_app(store, writer=writer, journal_db=str(tmp_path / "j.sqlite")))

    applied = client.post("/apply").json()
    assert applied["success"] is True
    assert applied["applied"] == 1
    assert writer.writes == [("TS-01", "meta_title", "Great Tee")]
    assert store.get("p1").status is ProposalStatus.APPLIED  # type: ignore[union-attr]

    writer.writes.clear()
    reverted = client.post("/rollback").json()
    assert reverted["reverted"] == 1
    assert writer.writes == [("TS-01", "meta_title", "Old Title")]  # restored


def test_apply_without_writer_reports_unconfigured() -> None:
    from api.app import create_app

    client = TestClient(create_app(_store()))
    assert client.post("/apply").json()["success"] is False

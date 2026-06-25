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

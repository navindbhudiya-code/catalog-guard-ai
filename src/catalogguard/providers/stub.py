"""Offline deterministic LLM provider — for tests and no-API demos (R-PROVIDER)."""

from __future__ import annotations

from typing import Any


class StubProvider:
    """Returns a fixed response (or a benign default) without any network call.

    Lets ``content`` audits and fix generation run fully offline: by default it
    marks descriptions acceptable and emits empty generated values.
    """

    name = "stub"

    def __init__(self, response: dict[str, Any] | None = None) -> None:
        self._response = response

    def generate(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        if self._response is not None:
            return self._response
        return {"acceptable": True, "problems": [], "value": "", "confidence": 0.0}

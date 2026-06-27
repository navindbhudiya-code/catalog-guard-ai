"""Offline heuristic provider — deterministic, plausible field values (R-PROVIDER).

Generates meta titles/descriptions and description rewrites from the product name
parsed out of the FixProposalAgent prompt, without any LLM call. Useful for demos
and CI where no API key is available, while still producing realistic content.
"""

from __future__ import annotations

import re
from typing import Any

_FIELD = re.compile(r"Field to fix:\s*(.+)")
_NAME = re.compile(r"Product name:\s*(.+)")
_TITLE_MAX = 60
_DESC_MAX = 160


def _extract(pattern: re.Pattern[str], text: str, default: str) -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else default


class HeuristicProvider:
    """Deterministic field generator that needs no network or API key."""

    name = "heuristic"

    def generate(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        field = _extract(_FIELD, user, "")
        name = _extract(_NAME, user, "this product")

        if field == "meta_title":
            value, confidence = f"{name} | Buy Online"[:_TITLE_MAX], 0.9
        elif field == "meta_description":
            value = f"Shop the {name} — premium quality, fast shipping, easy returns."[:_DESC_MAX]
            confidence = 0.8
        elif field == "description":
            value = f"{name}: crafted for everyday performance, comfort, and lasting quality."
            confidence = 0.7
        else:
            value, confidence = name, 0.6

        return {
            "value": value,
            "confidence": confidence,
            "rationale": "generated offline from product attributes",
            "tokens": len(value),
        }

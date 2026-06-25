"""LLM provider abstraction (R-PROVIDER).

Agents depend only on this protocol, so Claude API ↔ AWS Bedrock is a config
flag and tests inject a deterministic fake. Every call uses a JSON schema for
structured output — never free-text parsing.
"""

from __future__ import annotations

from typing import Any, Protocol


class LLMProvider(Protocol):
    """Minimal structured-generation surface used by LLM agents."""

    name: str

    def generate(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Return a dict conforming to ``schema`` (structured output)."""
        ...

"""Claude API provider (R-PROVIDER). Requires the ``[llm]`` extra (anthropic).

Network glue — excluded from the unit-coverage gate; exercised via integration.
Uses tool-use to force structured JSON output (never free-text parsing).
"""

from __future__ import annotations

import json
from typing import Any


class ClaudeProvider:
    """LLM provider backed by the Anthropic Claude API."""

    name = "claude"

    def __init__(self, api_key: str, model: str = "claude-opus-4-8") -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        tool = {
            "name": "emit",
            "description": "Return the structured result.",
            "input_schema": schema,
        }
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            tools=[tool],
            tool_choice={"type": "tool", "name": "emit"},
            messages=[{"role": "user", "content": user}],
        )
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                data: dict[str, Any] = dict(block.input)
                usage = getattr(response, "usage", None)
                if usage is not None:
                    data.setdefault("tokens", int(usage.input_tokens) + int(usage.output_tokens))
                return data
        # Fallback: parse text as JSON if no tool block was returned.
        fallback: dict[str, Any] = json.loads(response.content[0].text)
        return fallback

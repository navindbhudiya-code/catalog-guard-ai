"""AWS Bedrock (Claude) provider (R-PROVIDER). Requires the ``[llm]`` extra (boto3).

Network glue — excluded from the unit-coverage gate; exercised via integration.
"""

from __future__ import annotations

import json
from typing import Any


class BedrockProvider:
    """LLM provider backed by Claude on AWS Bedrock."""

    name = "bedrock"

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        region: str = "us-east-1",
    ) -> None:
        import boto3

        self._client = boto3.client("bedrock-runtime", region_name=region)
        self._model_id = model_id

    def generate(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": system,
            "tools": [{"name": "emit", "input_schema": schema}],
            "tool_choice": {"type": "tool", "name": "emit"},
            "messages": [{"role": "user", "content": user}],
        }
        response = self._client.invoke_model(modelId=self._model_id, body=json.dumps(body))
        payload = json.loads(response["body"].read())
        for block in payload.get("content", []):
            if block.get("type") == "tool_use":
                result: dict[str, Any] = dict(block["input"])
                return result
        raise ValueError("Bedrock returned no structured tool output")

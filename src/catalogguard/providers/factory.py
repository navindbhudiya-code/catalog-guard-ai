"""Select an LLM provider from settings (R-PROVIDER).

Concrete providers are imported lazily so the core (and the offline stub path)
never needs anthropic/boto3 installed. Excluded from the unit-coverage gate.
"""

from __future__ import annotations

from catalogguard.config import Settings
from catalogguard.providers.base import LLMProvider
from catalogguard.providers.stub import StubProvider


def get_provider(settings: Settings) -> LLMProvider:
    """Return the configured provider (claude | bedrock | stub)."""
    choice = settings.llm_provider.lower()
    if choice == "claude":
        from catalogguard.providers.claude import ClaudeProvider

        return ClaudeProvider(api_key=settings.anthropic_api_key, model=settings.llm_model)
    if choice == "bedrock":
        from catalogguard.providers.bedrock import BedrockProvider

        return BedrockProvider()
    if choice == "stub":
        return StubProvider()
    if choice == "heuristic":
        from catalogguard.providers.heuristic import HeuristicProvider

        return HeuristicProvider()
    raise ValueError(f"unknown LLM provider: {settings.llm_provider}")

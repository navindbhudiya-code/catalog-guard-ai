"""Maps audit check names to agent instances."""

from __future__ import annotations

from collections.abc import Callable

from catalogguard.models import AuditConfig
from catalogguard.providers.base import LLMProvider

from .attribute import AttributeAgent
from .base import AuditAgent
from .content import ContentAgent
from .duplicate import DuplicateAgent
from .sanity import SanityAgent
from .seo import SEOAgent

# Rule-based agents need only config.
_FACTORIES: dict[str, Callable[..., AuditAgent]] = {
    "sanity": SanityAgent,
    "attribute": AttributeAgent,
    "duplicate": DuplicateAgent,
    "seo": SEOAgent,
}

# Agents that require an LLM provider.
_LLM_CHECKS = ("content",)

SUPPORTED_CHECKS: tuple[str, ...] = (*_FACTORIES, *_LLM_CHECKS)


def build_agents(
    config: AuditConfig,
    checks: list[str],
    *,
    provider: LLMProvider | None = None,
) -> dict[str, AuditAgent]:
    """Instantiate the agents for the requested checks.

    ``content`` requires an LLM provider; the rest are pure rule agents.
    """
    agents: dict[str, AuditAgent] = {}
    for check in checks:
        if check in _LLM_CHECKS:
            if provider is None:
                raise ValueError(f"check '{check}' requires an LLM provider")
            agents[check] = ContentAgent(config, provider)
        else:
            agents[check] = _FACTORIES[check](config)
    return agents

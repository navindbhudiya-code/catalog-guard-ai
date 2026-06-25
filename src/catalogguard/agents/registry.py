"""Maps audit check names to agent instances."""

from __future__ import annotations

from collections.abc import Callable

from catalogguard.models import AuditConfig

from .attribute import AttributeAgent
from .base import AuditAgent
from .duplicate import DuplicateAgent
from .sanity import SanityAgent

_FACTORIES: dict[str, Callable[..., AuditAgent]] = {
    "sanity": SanityAgent,
    "attribute": AttributeAgent,
    "duplicate": DuplicateAgent,
}

SUPPORTED_CHECKS: tuple[str, ...] = tuple(_FACTORIES)


def build_agents(config: AuditConfig, checks: list[str]) -> dict[str, AuditAgent]:
    """Instantiate the agents for the requested checks."""
    return {check: _FACTORIES[check](config) for check in checks}

"""Shared base for rules-first agents."""

from __future__ import annotations

from typing import ClassVar, Protocol

from catalogguard.models import AuditConfig, Issue, Product
from catalogguard.rules.base import Rule


class AuditAgent(Protocol):
    """The surface every audit agent exposes to the Supervisor."""

    name: str

    def run(self, products: list[Product]) -> list[Issue]: ...


class RuleAgent:
    """Applies a fixed set of rules to every product.

    Rules-first by design: a cheap deterministic pass that never spends a token.
    Subclasses set ``rules`` (and an optional ``name``).
    """

    rules: ClassVar[list[Rule]] = []
    name: str = "rule-agent"

    def __init__(self, config: AuditConfig) -> None:
        self._config = config

    def run(self, products: list[Product]) -> list[Issue]:
        """Return every issue the rules find across the given products."""
        found: list[Issue] = []
        for product in products:
            for rule in self.rules:
                found.extend(rule(product, self._config))
        return found

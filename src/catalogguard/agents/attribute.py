"""AttributeAgent — attribute completeness checks (R-ATTR), rules-first."""

from __future__ import annotations

from typing import ClassVar

from catalogguard.rules.attributes import ATTRIBUTE_RULES
from catalogguard.rules.base import Rule

from .base import RuleAgent


class AttributeAgent(RuleAgent):
    """Rule-based attribute validation. LLM-assisted checks arrive in Phase 3."""

    name = "AttributeAgent"
    rules: ClassVar[list[Rule]] = list(ATTRIBUTE_RULES)

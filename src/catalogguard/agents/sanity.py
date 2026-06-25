"""SanityAgent — category/price/stock rule checks (R-SANITY)."""

from __future__ import annotations

from typing import ClassVar

from catalogguard.rules.base import Rule
from catalogguard.rules.sanity import SANITY_RULES

from .base import RuleAgent


class SanityAgent(RuleAgent):
    """Pure-rule sanity checks; no LLM, cheap to run first."""

    name = "SanityAgent"
    rules: ClassVar[list[Rule]] = list(SANITY_RULES)

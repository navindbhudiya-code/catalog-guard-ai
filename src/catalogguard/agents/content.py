"""ContentAgent — LLM-scored description quality (R-CONTENT), structured output."""

from __future__ import annotations

from typing import Any

from catalogguard.logging.cost import CostLedger
from catalogguard.models import AuditConfig, DetectedBy, Dimension, Issue, Product, Severity
from catalogguard.providers.base import LLMProvider
from catalogguard.rules.base import issue

_SYSTEM = (
    "You are a meticulous e-commerce content auditor. Judge whether a product "
    "description is high quality: not too short, not keyword-stuffed, not copied "
    "verbatim, valid HTML, correct language, and matching the product."
)

# JSON schema for structured output — never free-text parsing.
CONTENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "acceptable": {"type": "boolean"},
        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
        "problems": {"type": "array", "items": {"type": "string"}},
        "tokens": {"type": "integer"},
    },
    "required": ["acceptable"],
}

_SEVERITY = {"low": Severity.LOW, "medium": Severity.MEDIUM, "high": Severity.HIGH}


class ContentAgent:
    """Scores descriptions with an LLM and flags low-quality content.

    Rules-before-LLM: products with no description are skipped without a call.
    """

    name = "ContentAgent"

    def __init__(
        self,
        config: AuditConfig,
        provider: LLMProvider,
        *,
        ledger: CostLedger | None = None,
    ) -> None:
        self._config = config
        self._provider = provider
        self._ledger = ledger

    def _prompt(self, product: Product) -> str:
        return f"Product name: {product.name}\nDescription:\n{product.description}"

    def run(self, products: list[Product]) -> list[Issue]:
        found: list[Issue] = []
        for product in products:
            if not (product.description or "").strip():
                continue
            result = self._provider.generate(_SYSTEM, self._prompt(product), CONTENT_SCHEMA)
            if self._ledger is not None and "tokens" in result:
                self._ledger.record(self.name, int(result["tokens"]))
            if result.get("acceptable", True):
                continue
            severity = _SEVERITY.get(result.get("severity", "medium"), Severity.MEDIUM)
            problems = result.get("problems") or ["Low-quality description."]
            found.extend(
                issue(
                    product,
                    Dimension.CONTENT,
                    severity,
                    "low_quality_description",
                    problem,
                    field="description",
                    detected_by=DetectedBy.LLM,
                )
                for problem in problems
            )
        return found

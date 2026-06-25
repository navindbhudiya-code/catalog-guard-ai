"""FixProposalAgent — consolidates issues into approvable fix payloads (R-CONTENT/R-SEO)."""

from __future__ import annotations

from typing import Any

from catalogguard.logging.cost import CostLedger
from catalogguard.models import AuditConfig, FixProposal, Issue, Product
from catalogguard.providers.base import LLMProvider

_SYSTEM = (
    "You generate corrected e-commerce catalog field values. Stay faithful to the "
    "product's real attributes — never invent features. Return concise, compliant values."
)

# Issue code -> the product field a generated fix would write to.
_GENERATED_FIELD: dict[str, str] = {
    "missing_meta_title": "meta_title",
    "meta_title_too_long": "meta_title",
    "duplicate_meta_title": "meta_title",
    "missing_meta_description": "meta_description",
    "meta_description_too_long": "meta_description",
    "low_quality_description": "description",
    "thin_content": "description",
}

FIX_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "value": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "rationale": {"type": "string"},
        "tokens": {"type": "integer"},
    },
    "required": ["value"],
}


class FixProposalAgent:
    """Turns fixable issues into FixProposals with confidence scores via the LLM."""

    name = "FixProposalAgent"

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

    def _prompt(self, product: Product, issue: Issue, field: str) -> str:
        return (
            f"Field to fix: {field}\nIssue: {issue.message}\n"
            f"Product name: {product.name}\nCurrent description: {product.description or ''}"
        )

    def propose(self, issues: list[Issue], products: list[Product]) -> list[FixProposal]:
        by_sku = {p.sku: p for p in products}
        proposals: list[FixProposal] = []
        for issue in issues:
            field = _GENERATED_FIELD.get(issue.code)
            if field is None:
                continue
            product = by_sku.get(issue.sku)
            if product is None:
                continue

            result = self._provider.generate(
                _SYSTEM, self._prompt(product, issue, field), FIX_SCHEMA
            )
            if self._ledger is not None and "tokens" in result:
                self._ledger.record(self.name, int(result["tokens"]))

            proposals.append(
                FixProposal(
                    issue_id=issue.id,
                    sku=issue.sku,
                    field=field,
                    current_value=getattr(product, field, None),
                    proposed_value=result["value"],
                    confidence=float(result.get("confidence", 0.5)),
                    rationale=result.get("rationale", ""),
                )
            )
        return proposals

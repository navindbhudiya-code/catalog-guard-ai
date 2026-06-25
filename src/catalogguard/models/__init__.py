"""Shared typed state models for CatalogGuard (R-STATE)."""

from __future__ import annotations

from .enums import DetectedBy, Dimension, ProposalStatus, Severity
from .issue import Issue
from .product import Product
from .proposal import FixProposal
from .report import AuditReport
from .state import AuditConfig, GraphState

__all__ = [
    "AuditConfig",
    "AuditReport",
    "DetectedBy",
    "Dimension",
    "FixProposal",
    "GraphState",
    "Issue",
    "Product",
    "ProposalStatus",
    "Severity",
]

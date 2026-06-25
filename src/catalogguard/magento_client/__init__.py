"""Magento REST client package (R-EXTRACT)."""

from __future__ import annotations

from .client import MagentoClient, RetryableStatusError

__all__ = ["MagentoClient", "RetryableStatusError"]

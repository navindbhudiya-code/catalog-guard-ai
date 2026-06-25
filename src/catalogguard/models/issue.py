"""The Issue model — one data-quality problem found on one product."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import DetectedBy, Dimension, Severity


class Issue(BaseModel):
    """A single detected catalog problem."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    sku: str
    dimension: Dimension
    severity: Severity
    code: str
    message: str
    field: str | None = None
    current_value: Any | None = None
    detected_by: DetectedBy = DetectedBy.RULE

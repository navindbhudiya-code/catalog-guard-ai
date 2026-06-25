"""The Product model — a normalized view of a Magento catalog product."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

# Magento custom_attributes whose codes map directly onto first-class fields.
_MAPPED_ATTRIBUTES = {
    "description",
    "short_description",
    "meta_title",
    "meta_description",
    "meta_keyword",
    "url_key",
}


class Product(BaseModel):
    """A Magento product normalized for auditing.

    Magento-native numeric conventions are preserved (``status`` 1=enabled/2=disabled,
    ``visibility`` 1-4) with convenience accessors layered on top.
    """

    sku: str = Field(min_length=1)
    name: str = ""
    description: str | None = None
    short_description: str | None = None
    price: float | None = None
    special_price: float | None = None
    status: int = 1
    visibility: int = 4
    type_id: str = "simple"
    attribute_set_id: int = 4
    weight: float | None = None
    stock_qty: float | None = None
    categories: list[int] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keyword: str | None = None
    url_key: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("price", "special_price")
    @classmethod
    def _non_negative(cls, value: float | None) -> float | None:
        if value is not None and value < 0:
            raise ValueError("price cannot be negative")
        return value

    @property
    def is_enabled(self) -> bool:
        """True when the Magento status flag marks the product enabled."""
        return self.status == 1

    @classmethod
    def from_magento(cls, payload: dict[str, Any]) -> Product:
        """Build a Product from a Magento REST product payload.

        Top-level fields are copied directly; ``custom_attributes`` (a list of
        ``{attribute_code, value}``) is split between mapped first-class fields and
        the catch-all ``custom_attributes`` dict.
        """
        fields: dict[str, Any] = {
            key: payload[key]
            for key in (
                "sku",
                "name",
                "price",
                "status",
                "visibility",
                "type_id",
                "attribute_set_id",
                "weight",
            )
            if key in payload
        }

        mapped: dict[str, Any] = {}
        extra: dict[str, Any] = {}
        for attr in payload.get("custom_attributes", []):
            code = attr["attribute_code"]
            value = attr["value"]
            if code in _MAPPED_ATTRIBUTES:
                mapped[code] = value
            else:
                extra[code] = value

        return cls(**fields, **mapped, custom_attributes=extra)

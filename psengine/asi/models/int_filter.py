from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Optional


class IntEqFilter(BaseModel):
    eq: int
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class IntInFilter(BaseModel):
    in_: list[int]
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class IntRangeFilter(BaseModel):
    start: Optional[int]
    end: Optional[int]
    # additional_properties: dict[str, Any] = Field(default_factory=dict)

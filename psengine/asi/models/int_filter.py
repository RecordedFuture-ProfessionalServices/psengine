from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Optional


class IntEqFilter(BaseModel):
    eq: int


class IntInFilter(BaseModel):
    in_: list[int]


class IntRangeFilter(BaseModel):
    start: Optional[int]
    end: Optional[int]

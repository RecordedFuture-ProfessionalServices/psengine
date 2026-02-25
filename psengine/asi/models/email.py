from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any

class EmailEqFilter(BaseModel):

    eq: str
    additional_properties: dict[str, Any] = Field(default_factory=dict)

class EmailInFilter(BaseModel):

    in_: list[str]
    additional_properties: dict[str, Any] = Field(default_factory=dict)

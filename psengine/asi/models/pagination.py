from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Optional


class Pagination(BaseModel):
    next_cursor: Optional[str] = None
    limit: Optional[int] = 50
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class PaginationResponse(BaseModel):
    next_cursor: Optional[str] = None
    limit: Optional[int] = 50
    total: Optional[int] = None
    sort: Optional[list[list[str]]] = None
    additional_properties: dict[str, Any] = Field(default_factory=dict)

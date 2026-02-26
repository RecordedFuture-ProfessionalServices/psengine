from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Optional
from .pagination import PaginationResponse


class ApiCount(BaseModel):
    returned: int
    total: Optional[int] = None
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class ApiMetaParamsType0(BaseModel):
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class ApiMeta(BaseModel):
    params: Optional[ApiMetaParamsType0] = None
    counts: Optional[ApiCount] = None
    pagination: Optional[PaginationResponse] = None
    request_id: Optional[str] = None
    additional_properties: dict[str, Any] = Field(default_factory=dict)

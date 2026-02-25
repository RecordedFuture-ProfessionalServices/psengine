from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Optional
from .api import ApiMeta
from .static import StaticAssetsOperations, StaticAssetsResult

class UpdateStaticAssetsRequest(BaseModel):

    static_assets: StaticAssetsOperations
    additional_properties: dict[str, Any] = Field(default_factory=dict)

class UpdateStaticAssetsResponse(BaseModel):

    data: StaticAssetsResult
    meta: Optional[ApiMeta] = None
    additional_properties: dict[str, Any] = Field(default_factory=dict)

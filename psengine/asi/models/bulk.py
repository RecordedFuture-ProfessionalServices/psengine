from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any
from .core import TagAssetRequest


class BulkTagAssetsRequestAssetTags(BaseModel):
    additional_properties: dict[str, TagAssetRequest] = Field(default_factory=dict)


class BulkTagAssetsRequest(BaseModel):
    asset_tags: BulkTagAssetsRequestAssetTags
    additional_properties: dict[str, Any] = Field(default_factory=dict)

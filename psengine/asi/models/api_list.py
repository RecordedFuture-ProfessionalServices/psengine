from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any
from .api import ApiMeta
from .core import Asset, AssetExposure, CustomTagPublic, ExposureSummary
from .static import StaticAsset


class ApiListResponseAsset(BaseModel):
    data: list[Asset]
    meta: ApiMeta
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class ApiListResponseAssetExposure(BaseModel):
    data: list[AssetExposure]
    meta: ApiMeta
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class ApiListResponseCustomTagPublic(BaseModel):
    data: list[CustomTagPublic]
    meta: ApiMeta
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class ApiListResponseExposureSummary(BaseModel):
    data: list[ExposureSummary]
    meta: ApiMeta
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class ApiListResponseStaticAsset(BaseModel):
    data: list[StaticAsset]
    meta: ApiMeta
    additional_properties: dict[str, Any] = Field(default_factory=dict)

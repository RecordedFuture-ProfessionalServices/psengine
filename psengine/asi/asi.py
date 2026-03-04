from pydantic import Field
from psengine.asi.models.api import ApiMeta
from ..common_models import RFBaseModel
from .models import AssetExposure, ExposureSignature

from typing import Optional


class Exposure(RFBaseModel):
    asset_count: int
    asset_exposures: Optional[list[AssetExposure]] = Field(default_factory=[])
    signature: ExposureSignature


class ExposureSearchOut(RFBaseModel):
    content: list[Exposure]
    meta: ApiMeta

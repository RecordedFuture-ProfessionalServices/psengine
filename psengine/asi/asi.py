from typing import Optional

from psengine.asi.models.api import ApiMeta
from psengine.asi.models.core import AssetWithExposure

from ..common_models import RFBaseModel
from .models import AssetExposure, ExposureSignature


class AssetWithExposureSearch(RFBaseModel):
    asset_exposures: Optional[list[AssetWithExposure]] = []
    signature: ExposureSignature
    meta: Optional[ApiMeta] = None

    def __str__(self) -> str:
        msg = 'Name: {}, Id: {}, Severity: {}'
        return msg.format(
            self.signature.name,
            self.signature.id,
            self.signature.severity.value,
        )

    def __hash__(self) -> int:
        return hash(self.signature.id)

    def __eq__(self, other: 'AssetWithExposureSearch'):
        return self.signature.id == other.signature.id

    def __gt__(self, other: 'AssetWithExposureSearch'):
        return (self.signature.severity.value, self.signature.id) == (
            other.signature.severity.value,
            other.signature.id,
        )


class ExposureSearch(RFBaseModel):
    asset_count: int
    asset_exposures: Optional[list[AssetExposure]] = []
    signature: ExposureSignature

    def __str__(self) -> str:
        msg = 'Name: {}, Id: {}, Severity: {}, Asset Count: {}'
        return msg.format(
            self.signature.name,
            self.signature.id,
            self.signature.severity.value,
            self.asset_count,
        )

    def __hash__(self) -> int:
        return hash(self.signature.id)

    def __eq__(self, other: 'ExposureSearch'):
        return self.signature.id == other.signature.id

    def __gt__(self, other: 'ExposureSearch'):
        return (self.signature.severity.value, self.asset_count, self.signature.id) == (
            other.signature.severity.value,
            other.asset_count,
            other.signature.id,
        )


class ExposureSearchOut(RFBaseModel):
    content: list[ExposureSearch]
    meta: ApiMeta

    def __str__(self) -> str:
        return '\n'.join(str(c) for c in sorted(self.content))

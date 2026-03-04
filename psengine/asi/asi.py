from typing import Optional

from psengine.asi.models.api import ApiMeta

from ..common_models import RFBaseModel
from .models import AssetExposure, ExposureSignature


class Exposure(RFBaseModel):
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

    def __eq__(self, other: 'Exposure'):
        return self.signature.id == other.signature.id

    def __gt__(self, other: 'Exposure'):
        return (self.signature.severity.value, self.asset_count, self.signature.id) == (
            other.signature.severity.value,
            other.asset_count,
            other.signature.id,
        )


class ExposureSearchOut(RFBaseModel):
    content: list[Exposure]
    meta: ApiMeta

    def __str__(self) -> str:
        return '\n'.join(str(c) for c in sorted(self.content))

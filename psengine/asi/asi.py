from datetime import datetime
from typing import Optional

from pydantic import Field

from psengine.asi.models.api import ApiMeta
from psengine.asi.models.core import AssetWithExposure

from ..common_models import RFBaseModel
from .models import (
    AssetExposure,
    CertificateInstance,
    DefensiveControl,
    DNSRecord,
    Exposure,
    ExposureSignature,
    ScannedIP,
    WHOISRecord,
)


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


class Asset(RFBaseModel):
    project_id: str
    id_: str = Field(alias='id')
    name: str
    type_: str = Field(alias='type')
    discovered_at: Optional[datetime]
    added_to_project_at: datetime
    last_scanned_at: Optional[datetime] = None
    apex_domain: Optional[str] = None
    exposure_score: Optional[int] = None
    is_static_asset: Optional[bool] = False
    custom_tags: Optional[list[str]] = None
    resolved_ips: Optional[list[str]] = None
    dns_records: Optional[list[DNSRecord]] = None
    whois: Optional[WHOISRecord] = None
    certificates: Optional[list[CertificateInstance]] = None
    defenses: Optional[list[DefensiveControl]] = None
    exposures: Optional[list[Exposure]] = None
    scanned_ips: Optional[list[ScannedIP]] = None

    def __str__(self) -> str:
        msg = 'Name: {}, Type: {}, Exposure Score: {}'
        return msg.format(self.name, self.type_, self.exposure_score or 'N/A')

    def __hash__(self) -> int:
        return hash(self.id_, self.project_id)

    def __eq__(self, other: 'Asset'):
        return (self.id_, self.project_id) == (other.id_, other.project_id)

    def __gt__(self, other: 'Asset'):
        return (self.exposure_score or 0, self.id_) == (self.exposure_score or 0, self.id_)


class AssetResponse(RFBaseModel):
    content: list[Asset]
    meta: ApiMeta

    def __str__(self) -> str:
        return '\n'.join(str(c) for c in sorted(self.content))

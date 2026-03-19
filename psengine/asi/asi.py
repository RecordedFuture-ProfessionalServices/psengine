##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

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
    """Validate data received from the `/v2/projects/{project_id}/exposures/{signature_id}`
    endpoint.

    This class supports hashing, equality comparison, greater-than comparison, and string
    representation of `AssetWithExposureSearch` instances.

    Hashing:
        Returns a hash value based on the exposure signature `id`.

    Equality:
        Checks equality between two `AssetWithExposureSearch` instances based on the exposure
        signature `id`.

    Greater-than Comparison:
        Defines a greater-than comparison between two `AssetWithExposureSearch` instances based on
        the signature severity and `id`.

    String Representation:
        Returns a string representation of the `AssetWithExposureSearch` instance including the
        signature name, `id`, and severity.

        ```python
        >>> print(asset_with_exposure)
        Name: Exposed Service, Id: exp-123, Severity: critical
        ```
    """

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
    """Validate data received from the `/v2/projects/{project_id}/exposures` endpoint.

    This class supports hashing, equality comparison, greater-than comparison, and string
    representation of `ExposureSearch` instances.

    Hashing:
        Returns a hash value based on the exposure signature `id`.

    Equality:
        Checks equality between two `ExposureSearch` instances based on the exposure signature
        `id`.

    Greater-than Comparison:
        Defines a greater-than comparison between two `ExposureSearch` instances based on the
        signature severity, asset count, and `id`.

    String Representation:
        Returns a string representation of the `ExposureSearch` instance including the signature
        name, `id`, severity, and asset count.

        ```python
        >>> print(exposure)
        Name: Exposed Service, Id: exp-123, Severity: critical, Asset Count: 42
        ```
    """

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
    """Validate data received from the `/v2/projects/{project_id}/exposures` endpoint."""

    content: list[ExposureSearch]
    meta: ApiMeta

    def __str__(self) -> str:
        return '\n'.join(str(c) for c in sorted(self.content))


class Asset(RFBaseModel):
    """Validate data received from the `/v2/projects/{project_id}/assets`,
    `/v2/projects/{project_id}/assets/{asset_id}`,
    `/v2/projects/{project_id}/assets/{asset_id}/exposures`, and
    `/v2/projects/{project_id}/assets/_search` endpoints.

    This class supports hashing, equality comparison, greater-than comparison, and string
    representation of `Asset` instances.

    Hashing:
        Returns a hash value based on the asset `id_` and `project_id`.

    Equality:
        Checks equality between two `Asset` instances based on the asset `id_` and `project_id`.

    Greater-than Comparison:
        Defines a greater-than comparison between two `Asset` instances based on the exposure
        score and `id_`.

    String Representation:
        Returns a string representation of the `Asset` instance including the name, type, and
        exposure score.

        ```python
        >>> print(asset)
        Name: example.com, Type: domain, Exposure Score: 85
        ```
    """

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
    """Validate data received from the `/v2/projects/{project_id}/assets` and
    `/v2/projects/{project_id}/assets/_search` endpoints.
    """

    content: list[Asset]
    meta: ApiMeta

    def __str__(self) -> str:
        return '\n'.join(str(c) for c in sorted(self.content))

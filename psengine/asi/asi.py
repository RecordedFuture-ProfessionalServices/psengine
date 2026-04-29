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

from pydantic import Field

from ..common_models import RFBaseModel
from .models import (
    ApiMeta,
    AssetExposure,
    AssetWithExposure,
    CertificateInstance,
    DefensiveControl,
    DNSRecord,
    Exposure,
    ExposureSignature,
    ScannedIP,
    WHOISRecord,
)


class AssetWithExposureSearch(RFBaseModel):
    """Validate data received from the `/projects/{project_id}/exposures/{signature_id}`
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

    asset_exposures: list[AssetWithExposure] | None = []
    signature: ExposureSignature
    meta: ApiMeta | None = None

    def __str__(self) -> str:
        msg = 'Name: {}, Id: {}, Severity: {}'
        return msg.format(
            self.signature.name,
            self.signature.id_,
            self.signature.severity.value,
        )

    def __hash__(self) -> int:
        return hash(self.signature.id_)

    def __eq__(self, other: 'AssetWithExposureSearch'):
        return self.signature.id_ == other.signature.id_

    def __gt__(self, other: 'AssetWithExposureSearch'):
        return (self.signature.severity.value, self.signature.id_) > (
            other.signature.severity.value,
            other.signature.id_,
        )


class ExposureSearch(RFBaseModel):
    """Validate data received from the `/projects/{project_id}/exposures` endpoint.

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
    asset_exposures: list[AssetExposure] | None = []
    signature: ExposureSignature

    def __str__(self) -> str:
        msg = 'Name: {}, Id: {}, Severity: {}, Asset Count: {}'
        return msg.format(
            self.signature.name,
            self.signature.id_,
            self.signature.severity.value,
            self.asset_count,
        )

    def __hash__(self) -> int:
        return hash(self.signature.id_)

    def __eq__(self, other: 'ExposureSearch'):
        return self.signature.id_ == other.signature.id_

    def __gt__(self, other: 'ExposureSearch'):
        return (self.signature.severity.value, self.asset_count, self.signature.id_) > (
            other.signature.severity.value,
            other.asset_count,
            other.signature.id_,
        )


class ExposureSearchOut(RFBaseModel):
    """Validate data received from the `/projects/{project_id}/exposures` endpoint."""

    data: list[ExposureSearch]
    meta: ApiMeta

    def __str__(self) -> str:
        return '\n'.join(str(c) for c in sorted(self.data))


class Asset(RFBaseModel):
    """Validate data received from the `/projects/{project_id}/assets`,
    `/projects/{project_id}/assets/{asset_id}`,
    `/projects/{project_id}/assets/{asset_id}/exposures`, and
    `/projects/{project_id}/assets/_search` endpoints.

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
    discovered_at: datetime | None
    added_to_project_at: datetime
    last_scanned_at: datetime | None = None
    apex_domain: str | None = None
    exposure_score: int | None = None
    is_static_asset: bool | None = False
    custom_tags: list[str] | None = None
    resolved_ips: list[str] | None = None
    dns_records: list[DNSRecord] | None = None
    whois: WHOISRecord | None = None
    certificates: list[CertificateInstance] | None = None
    defenses: list[DefensiveControl] | None = None
    exposures: list[Exposure] | None = None
    scanned_ips: list[ScannedIP] | None = None

    def __str__(self) -> str:
        msg = 'Name: {}, Type: {}, Exposure Score: {}'
        return msg.format(self.name, self.type_, self.exposure_score or 'N/A')

    def __hash__(self) -> int:
        return hash((self.id_, self.project_id))

    def __eq__(self, other: 'Asset'):
        return (self.id_, self.project_id) == (other.id_, other.project_id)

    def __gt__(self, other: 'Asset'):
        return (self.exposure_score or 0, self.id_) > (other.exposure_score or 0, other.id_)


class AssetResponse(RFBaseModel):
    """Validate data received from the `/projects/{project_id}/assets` and
    `/projects/{project_id}/assets/_search` endpoints.
    """

    data: list[Asset]
    meta: ApiMeta

    def __str__(self) -> str:
        return '\n'.join(str(c) for c in sorted(self.data, reverse=True))


class Project(RFBaseModel):
    """Validate data received from the `/projects` endpoint.

    This class supports hashing, equality comparison, greater-than comparison, and string
    representation of `Project` instances.

    Hashing:
        Returns a hash value based on the project `id`.

    Equality:
        Checks equality between two `Project` instances based on the project `id`.

    Greater-than Comparison:
        Defines a greater-than comparison between two `Project` instances based on the project
        title.

    String Representation:
        Returns a string representation of the `Project` instance including the title, `id`, and
        whether scanning is enabled.

        ```python
        >>> print(project)
        Name: Example Project, Id: 123e4567-e89b-12d3-a456-426614174000, Enabled: True
        ```
    """

    id_: str = Field(alias='id')
    title: str
    scanning_enabled: bool | None = None
    last_scanned_at: datetime | None = None
    inserted_at: datetime | None = None
    max_exposure_score: int | None = None

    def __str__(self) -> str:
        msg = 'Name: {}, Id: {}, Enabled: {}'
        return msg.format(
            self.title,
            self.id_,
            self.scanning_enabled or 'False',
        )

    def __hash__(self) -> int:
        return hash(self.id_)

    def __eq__(self, other: 'Project'):
        return self.id_ == other.id_

    def __gt__(self, other: 'Project'):
        return self.title > other.title


class ProjectListOut(RFBaseModel):
    """Validate data received from the `/projects` endpoint."""

    data: list[Project]
    meta: ApiMeta

    def __str__(self) -> str:
        return '\n'.join(str(c) for c in sorted(self.data))


class AssetExposuresOut(RFBaseModel):
    """Validate data received from the `/projects/{project_id}/assets/{asset_id}/exposures`."""

    data: list[AssetWithExposure]
    meta: ApiMeta

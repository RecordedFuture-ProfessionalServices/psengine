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

from datetime import date, datetime
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from pydantic import Field

from ..common_models import RFBaseModel


class SortDirection(str, Enum):
    ASC = 'asc'
    DESC = 'desc'


class ExposureSeverity(str, Enum):
    CRITICAL = 'critical'
    INFORMATIONAL = 'informational'
    MODERATE = 'moderate'
    UNKNOWN = 'unknown'


class AssetEnrichment(str, Enum):
    CERTIFICATES = 'certificates'
    CERTIFICATE_CHAIN = 'certificate_chain'
    CUSTOM_TAGS = 'custom_tags'
    DEFENSES = 'defenses'
    DNS_RECORDS = 'dns_records'
    EXPOSURES = 'exposures'
    EXPOSURE_INSTANCE_DETAILS = 'exposure_instance_details'
    IP_METADATA = 'ip_metadata'
    OPEN_TCP_PORTS = 'open_tcp_ports'
    OPEN_UDP_PORTS = 'open_udp_ports'
    WEB_TECHNOLOGIES = 'web_technologies'
    WHOIS = 'whois'


class AssetSortField(str, Enum):
    ADDED_TO_PROJECT_AT = 'added_to_project_at'
    APEX_DOMAIN = 'apex_domain'
    ASSET_ID = 'asset_id'
    DISCOVERED_AT = 'discovered_at'
    EXPOSURE_SCORE = 'exposure_score'
    LAST_SCANNED_AT = 'last_scanned_at'


FilterValueT = TypeVar('FilterValueT')


class NeqFilter(RFBaseModel, Generic[FilterValueT]):
    neq: FilterValueT


class QuickSearchFilter(RFBaseModel):
    search: str


class RequireAllFilter(RFBaseModel, Generic[FilterValueT]):
    in_: list[FilterValueT] = Field(alias='in')


class EqFilter(RFBaseModel, Generic[FilterValueT]):
    eq: FilterValueT


class InFilter(RFBaseModel, Generic[FilterValueT]):
    in_: list[FilterValueT] = Field(alias='in')


class ContainsFilter(RFBaseModel):
    contains: str


class RangeFilter(RFBaseModel, Generic[FilterValueT]):
    start: FilterValueT | None = None
    end: FilterValueT | None = None


class PaginationResponse(RFBaseModel):
    next_cursor: str | None = None
    limit: int | None = 50
    total: int | None = None
    sort: list[list[str]] | None = None


class ApiCount(RFBaseModel):
    returned: int
    total: int | None = None


class ApiMeta(RFBaseModel):
    counts: ApiCount | None = None
    pagination: PaginationResponse | None = None
    request_id: str | None = None


class Pagination(RFBaseModel):
    next_cursor: str | None = None
    limit: int | None = 50


class CertificateEntity(RFBaseModel):
    common_name: str | None = None
    organization_name: str | None = None
    organizational_unit_name: str | None = None
    country_name: str | None = None


class Certificate(RFBaseModel):
    expires_at: datetime
    issued_at: datetime
    sha256: str
    subject: CertificateEntity
    subject_alt_names: list[str] | None = None
    issuer: CertificateEntity | None = None
    chain: list['Certificate'] | None = None
    signature_algorithm: str | None = None


class ExposureInstance(RFBaseModel):
    port_number: int
    url: str | None = None


class VulnerabilityPublic(RFBaseModel):
    name: str
    slug: str
    cvss_score: float | None = None
    cvss_metrics: str | None = None
    references: list[str]
    cve_id: str | None = None
    cwe_ids: list[str | None] | None = None
    epss_score: float | None = None


class ExposureSignature(RFBaseModel):
    id_: str = Field(alias='id')
    name: str
    description: str | None
    severity: ExposureSeverity | None
    references: list[str] | None
    added_at: datetime | None = None
    vulnerabilities: list[VulnerabilityPublic] | None = None


class AssetExposure(RFBaseModel):
    asset_id: str
    instances: list[ExposureInstance]
    signature: ExposureSignature


class AssetWithExposure(RFBaseModel):
    asset_id: str
    details: Any
    instances: list[ExposureInstance]
    signature: ExposureSignature | None = None


class Exposure(RFBaseModel):
    id_: str = Field(alias='id')
    detection_id: str | None
    severity: ExposureSeverity
    instances: list[ExposureInstance]
    supports_evidence: bool | None = None


class GeoLocation(RFBaseModel):
    continent: str | None = None
    country: str | None = None
    city: str | None = None
    country_iso: str | None = None


class CertificatePropertiesFilter(RFBaseModel):
    certificate_subject: ContainsFilter | EqFilter[str] | InFilter[str] | None = None
    certificate_subject_alt_name: ContainsFilter | EqFilter[str] | InFilter[str] | None = None
    certificate_sha256: EqFilter[str] | None = None
    certificate_expires_at: RangeFilter[date] | None = None
    certificate_issued_at: RangeFilter[date] | None = None
    certificate_issuer: EqFilter[str] | InFilter[str] | None = None
    certificate_covers_domain: ContainsFilter | EqFilter[str] | InFilter[str] | None = None


class ExposurePropertiesFilter(RFBaseModel):
    severity: EqFilter[ExposureSeverity] | InFilter[ExposureSeverity] | None = None
    signature_id: EqFilter[str] | InFilter[str] | None = None
    asset_exposure_score: RangeFilter[int] | None = None
    last_scanned_at: RangeFilter[date] | None = None


class IPMetadata(RFBaseModel):
    as_number: int | None = None
    owner_name: str | None = None
    registry: str | None = None
    owner_geo: GeoLocation | None = None


class AssetPropertiesFilter(RFBaseModel):
    asset_id: EqFilter[str] | None = None
    name: ContainsFilter | None = None
    static_asset: EqFilter[bool] | None = None
    apex: EqFilter[str] | InFilter[str] | None = None
    added_to_project: RangeFilter[date] | None = None
    discovered: RangeFilter[date] | None = None
    asset_type: EqFilter[str] | None = None
    referenced_ip: ContainsFilter | EqFilter[str] | InFilter[str] | None = None
    cname_reference: ContainsFilter | EqFilter[str] | None = None
    referenced_ip_at: RangeFilter[date] | None = None
    valid_record_type: EqFilter[str] | InFilter[str] | NeqFilter[str] | None = None
    dns_resolves: EqFilter[bool] | None = None
    custom_tags: EqFilter[str] | InFilter[str] | RequireAllFilter[str] | None = None
    custom_tags_strict: EqFilter[str] | InFilter[str] | RequireAllFilter[str] | None = None
    asn: EqFilter[int] | InFilter[int] | None = None
    ip_geo_country_iso: EqFilter[str] | InFilter[str] | None = None
    ip_owner: EqFilter[str] | InFilter[str] | None = None
    registry: EqFilter[str] | InFilter[str] | None = None
    whois_email_current: EqFilter[str] | InFilter[str] | None = None
    whois_email: EqFilter[str] | InFilter[str] | None = None


class TechnologyInstance(RFBaseModel):
    seen_at: datetime
    seen_port: int
    seen_url: str | None = None


class DefensiveControl(RFBaseModel):
    name: str
    vendor: str | None = None
    technology_type: str | None = None
    version: str | None = None
    instances: list[TechnologyInstance] | None = None


class TechnologyPropertiesFilter(RFBaseModel):
    open_port_number: EqFilter[int] | InFilter[int] | None = None
    open_port_service: EqFilter[str] | InFilter[str] | None = None
    open_port_protocol: EqFilter[str] | InFilter[str] | None = None
    open_port_technology: EqFilter[str] | InFilter[str] | None = None
    waf_detected: EqFilter[bool] | None = None
    waf_name: EqFilter[str] | InFilter[str] | None = None
    technology_name: EqFilter[str] | InFilter[str] | None = None
    web_technology_name: EqFilter[str] | InFilter[str] | None = None
    is_responsive: EqFilter[bool] | None = None


class AssetSearchFilterIn(RFBaseModel):
    asset_properties: AssetPropertiesFilter | None = None
    certificate_properties: CertificatePropertiesFilter | None = None
    exposure_properties: ExposurePropertiesFilter | None = None
    technology_properties: TechnologyPropertiesFilter | None = None
    quick_search: QuickSearchFilter | None = None


class AssetSearchRequest(RFBaseModel):
    filter_: AssetSearchFilterIn | None = Field(None, alias='filter')
    pagination: Pagination | None = None
    enrichments: list[AssetEnrichment] | None = None
    sort: list[AssetSortField] | list[list[AssetSortField | SortDirection]] | None = None


class TechnologyWithInstances(RFBaseModel):
    name: str
    vendor: str | None = None
    technology_type: str | None = None
    version: str | None = None
    instances: list[TechnologyInstance] | None = None


class PortInstance(RFBaseModel):
    seen_ip: str
    seen_at: datetime
    service: str | None = None
    technology: TechnologyWithInstances | None = None
    web_technologies: list[TechnologyWithInstances] | None = None
    exposures: list[Exposure] | None = None
    defenses: list[DefensiveControl] | None = None


class Port(RFBaseModel):
    port: int
    protocol: str
    instances: list[PortInstance] | None = None
    certificate: Certificate | None = None


class CertificateInstance(RFBaseModel):
    certificate: Certificate
    seen_ports: list[Port] | None = None


class ScannedIP(RFBaseModel):
    ip: str
    last_scanned_at: datetime | None = None
    whois: Optional['WHOISRecord'] = None
    open_ports: list[Port] | None = None
    metadata: IPMetadata | None = None
    is_responsive: bool | None = None


class WHOISContact(RFBaseModel):
    email: str | None = None
    name: str | None = None
    organization: str | None = None
    is_current: bool | None = True


class WHOISRecord(RFBaseModel):
    registrar: str | None = None
    expires_at: datetime | None = None
    updated_at: datetime | None = None
    created_at: datetime | None = None
    is_private: bool | None = None
    is_from_parent: bool | None = False
    contacts: list[WHOISContact] | None = None
    name_servers: list[str] | None = None


class DNSValue(RFBaseModel):
    value: Any
    last_resolved_at: datetime | None
    seen_from: list[str] | None = None
    first_seen_at: datetime | None = None


class DNSRecord(RFBaseModel):
    record_type: str
    value: list[DNSValue] | None
    is_virtual: bool | None = False

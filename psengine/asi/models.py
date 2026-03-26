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
    start: Optional[FilterValueT] = None
    end: Optional[FilterValueT] = None


class PaginationResponse(RFBaseModel):
    next_cursor: Optional[str] = None
    limit: Optional[int] = 50
    total: Optional[int] = None
    sort: Optional[list[list[str]]] = None


class ApiCount(RFBaseModel):
    returned: int
    total: Optional[int] = None


class ApiMeta(RFBaseModel):
    counts: Optional[ApiCount] = None
    pagination: Optional[PaginationResponse] = None
    request_id: Optional[str] = None


class Pagination(RFBaseModel):
    next_cursor: Optional[str] = None
    limit: Optional[int] = 50


class CertificateEntity(RFBaseModel):
    common_name: Optional[str] = None
    organization_name: Optional[str] = None
    organizational_unit_name: Optional[str] = None
    country_name: Optional[str] = None


class Certificate(RFBaseModel):
    expires_at: datetime
    issued_at: datetime
    sha256: str
    subject: CertificateEntity
    subject_alt_names: Optional[list[str]] = None
    issuer: Optional[CertificateEntity] = None
    chain: Optional[list['Certificate']] = None
    signature_algorithm: Optional[str] = None


class ExposureInstance(RFBaseModel):
    port_number: int
    url: Optional[str] = None


class VulnerabilityPublic(RFBaseModel):
    name: str
    slug: str
    cvss_score: Optional[float] = None
    cvss_metrics: Optional[str] = None
    references: list[str]
    cve_id: Optional[str] = None
    cwe_ids: Optional[list[Optional[str]]] = None
    epss_score: Optional[float] = None


class ExposureSignature(RFBaseModel):
    id_: str = Field(alias='id')
    name: str
    description: Optional[str]
    severity: Optional[ExposureSeverity]
    references: Optional[list[str]]
    added_at: Optional[datetime] = None
    vulnerabilities: Optional[list[VulnerabilityPublic]] = None


class AssetExposure(RFBaseModel):
    asset_id: str
    instances: list[ExposureInstance]
    signature: ExposureSignature


class AssetWithExposure(RFBaseModel):
    asset_id: str
    details: Any
    instances: list[ExposureInstance]
    signature: Optional[ExposureSignature] = None


class Exposure(RFBaseModel):
    id_: str = Field(alias='id')
    detection_id: Optional[str]
    severity: ExposureSeverity
    instances: list[ExposureInstance]
    supports_evidence: Optional[bool] = None


class GeoLocation(RFBaseModel):
    continent: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    country_iso: Optional[str] = None


class CertificatePropertiesFilter(RFBaseModel):
    certificate_subject: Optional[ContainsFilter | EqFilter[str] | InFilter[str]] = None
    certificate_subject_alt_name: Optional[ContainsFilter | EqFilter[str] | InFilter[str]] = (
        None
    )
    certificate_sha256: Optional[EqFilter[str]] = None
    certificate_expires_at: Optional[RangeFilter[date]] = None
    certificate_issued_at: Optional[RangeFilter[date]] = None
    certificate_issuer: Optional[EqFilter[str] | InFilter[str]] = None
    certificate_covers_domain: Optional[ContainsFilter | EqFilter[str] | InFilter[str]] = None


class ExposurePropertiesFilter(RFBaseModel):
    severity: Optional[EqFilter[ExposureSeverity] | InFilter[ExposureSeverity]] = None
    signature_id: Optional[EqFilter[str] | InFilter[str]] = None
    asset_exposure_score: Optional[RangeFilter[int]] = None
    last_scanned_at: Optional[RangeFilter[date]] = None


class IPMetadata(RFBaseModel):
    as_number: Optional[int] = None
    owner_name: Optional[str] = None
    registry: Optional[str] = None
    owner_geo: Optional[GeoLocation] = None


class AssetPropertiesFilter(RFBaseModel):
    asset_id: Optional[EqFilter[str]] = None
    name: Optional[ContainsFilter] = None
    static_asset: Optional[EqFilter[bool]] = None
    apex: Optional[EqFilter[str] | InFilter[str]] = None
    added_to_project: Optional[RangeFilter[date]] = None
    discovered: Optional[RangeFilter[date]] = None
    asset_type: Optional[EqFilter[str]] = None
    referenced_ip: Optional[ContainsFilter | EqFilter[str] | InFilter[str]] = None
    cname_reference: Optional[ContainsFilter | EqFilter[str]] = None
    referenced_ip_at: Optional[RangeFilter[date]] = None
    valid_record_type: Optional[EqFilter[str] | InFilter[str] | NeqFilter[str]] = None
    dns_resolves: Optional[EqFilter[bool]] = None
    custom_tags: Optional[EqFilter[str] | InFilter[str] | RequireAllFilter[str]] = None
    custom_tags_strict: Optional[EqFilter[str] | InFilter[str] | RequireAllFilter[str]] = None
    asn: Optional[EqFilter[int] | InFilter[int]] = None
    ip_geo_country_iso: Optional[EqFilter[str] | InFilter[str]] = None
    ip_owner: Optional[EqFilter[str] | InFilter[str]] = None
    registry: Optional[EqFilter[str] | InFilter[str]] = None
    whois_email_current: Optional[EqFilter[str] | InFilter[str]] = None
    whois_email: Optional[EqFilter[str] | InFilter[str]] = None


class TechnologyInstance(RFBaseModel):
    seen_at: datetime
    seen_port: int
    seen_url: Optional[str] = None


class DefensiveControl(RFBaseModel):
    name: str
    vendor: Optional[str] = None
    technology_type: Optional[str] = None
    version: Optional[str] = None
    instances: Optional[list[TechnologyInstance]] = None


class TechnologyPropertiesFilter(RFBaseModel):
    open_port_number: Optional[EqFilter[int] | InFilter[int]] = None
    open_port_service: Optional[EqFilter[str] | InFilter[str]] = None
    open_port_protocol: Optional[EqFilter[str] | InFilter[str]] = None
    open_port_technology: Optional[EqFilter[str] | InFilter[str]] = None
    waf_detected: Optional[EqFilter[bool]] = None
    waf_name: Optional[EqFilter[str] | InFilter[str]] = None
    technology_name: Optional[EqFilter[str] | InFilter[str]] = None
    web_technology_name: Optional[EqFilter[str] | InFilter[str]] = None
    is_responsive: Optional[EqFilter[bool]] = None


class AssetSearchFilterIn(RFBaseModel):
    asset_properties: Optional[AssetPropertiesFilter] = None
    certificate_properties: Optional[CertificatePropertiesFilter] = None
    exposure_properties: Optional[ExposurePropertiesFilter] = None
    technology_properties: Optional[TechnologyPropertiesFilter] = None
    quick_search: Optional[QuickSearchFilter] = None


class AssetSearchRequest(RFBaseModel):
    filter_: Optional[AssetSearchFilterIn] = Field(None, alias='filter')
    pagination: Optional[Pagination] = None
    enrichments: Optional[list[AssetEnrichment]] = None
    sort: Optional[
        list[AssetSortField] | list[list[AssetSortField | SortDirection]]
    ] = None


class TechnologyWithInstances(RFBaseModel):
    name: str
    vendor: Optional[str] = None
    technology_type: Optional[str] = None
    version: Optional[str] = None
    instances: Optional[list[TechnologyInstance]] = None


class PortInstance(RFBaseModel):
    seen_ip: str
    seen_at: datetime
    service: Optional[str] = None
    technology: Optional[TechnologyWithInstances] = None
    web_technologies: Optional[list[TechnologyWithInstances]] = None
    exposures: Optional[list[Exposure]] = None
    defenses: Optional[list[DefensiveControl]] = None


class Port(RFBaseModel):
    port: int
    protocol: str
    instances: Optional[list[PortInstance]] = None
    certificate: Optional[Certificate] = None


class CertificateInstance(RFBaseModel):
    certificate: Certificate
    seen_ports: Optional[list[Port]] = None


class ScannedIP(RFBaseModel):
    ip: str
    last_scanned_at: Optional[datetime] = None
    whois: Optional['WHOISRecord'] = None
    open_ports: Optional[list[Port]] = None
    metadata: Optional[IPMetadata] = None
    is_responsive: Optional[bool] = None


class WHOISContact(RFBaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    organization: Optional[str] = None
    is_current: Optional[bool] = True


class WHOISRecord(RFBaseModel):
    registrar: Optional[str] = None
    expires_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    is_private: Optional[bool] = None
    is_from_parent: Optional[bool] = False
    contacts: Optional[list[WHOISContact]] = None
    name_servers: Optional[list[str]] = None


class DNSValue(RFBaseModel):
    value: Any
    last_resolved_at: Optional[datetime]
    seen_from: Optional[list[str]] = None
    first_seen_at: Optional[datetime] = None


class DNSRecord(RFBaseModel):
    record_type: str
    value: Optional[list[DNSValue]]
    is_virtual: Optional[bool] = False

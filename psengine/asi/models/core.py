from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from .api import Pagination


class AssetCountDateRangeFilter(BaseModel):
    name: str
    asset_count: int
    start: Optional[Union[date, float]]
    end: Optional[Union[date, float]]


class AssetCountEqFilter(BaseModel):
    name: str
    asset_count: int
    value: Union[int, str]


class AssetCountValueRangeFilter(BaseModel):
    name: str
    asset_count: int
    start: int
    end: int


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


class AssetState(BaseModel):
    added: Optional[str] = None
    errors: Optional[list[str]] = None


class AssetTagResponse(BaseModel):
    add_tags: Optional[list[str]] = None
    remove_tags: Optional[list[str]] = None
    assets: Optional[list[str]] = None
    complete: Optional[bool] = False
    task_ids: Optional[list[str]] = None


class CertificateEntity(BaseModel):
    common_name: Optional[str] = None
    organization_name: Optional[str] = None
    organizational_unit_name: Optional[str] = None
    country_name: Optional[str] = None


class Certificate(BaseModel):
    expires_at: datetime
    issued_at: datetime
    sha256: str
    subject: CertificateEntity
    subject_alt_names: Optional[list[str]] = None
    issuer: Optional[CertificateEntity] = None
    chain: Optional[list[Certificate]] = None
    signature_algorithm: Optional[str] = None


class ExposureInstance(BaseModel):
    port_number: int
    url: Optional[str] = None


class AssetWithExposure(BaseModel):
    asset_id: str
    instances: list[ExposureInstance]


class ExposureSeverity(str, Enum):
    CRITICAL = 'critical'
    INFORMATIONAL = 'informational'
    MODERATE = 'moderate'
    UNKNOWN = 'unknown'


class Exposure(BaseModel):
    id: str
    detection_id: Optional[str]
    severity: ExposureSeverity
    instances: list[ExposureInstance]
    supports_evidence: Optional[bool] = None


class FilterOptionsDateRange(BaseModel):
    name: str
    filter_query: list[str]
    filter_path: str
    filters: list[AssetCountDateRangeFilter]
    filter_type: Optional[str] = 'date_range'


class FilterOptionsEq(BaseModel):
    name: str
    filter_query: list[str]
    filter_path: str
    filters: list[AssetCountEqFilter]
    filter_type: Optional[str] = 'eq'


class FilterOptionsIn(BaseModel):
    name: str
    filter_query: list[str]
    filter_path: str
    filters: list[AssetCountEqFilter]
    filter_type: Optional[str] = 'in'


class AssetPropertiesFilterOptions(BaseModel):
    asset_type: Optional[FilterOptionsEq] = None
    asn: Optional[FilterOptionsIn] = None
    custom_tags: Optional[FilterOptionsIn] = None
    added_to_project: Optional[FilterOptionsDateRange] = None
    discovered: Optional[FilterOptionsDateRange] = None
    apex: Optional[FilterOptionsIn] = None
    static_asset: Optional[FilterOptionsEq] = None
    ip_geo_country_iso: Optional[FilterOptionsIn] = None
    ip_owner: Optional[FilterOptionsIn] = None
    registry: Optional[FilterOptionsIn] = None
    referenced_ip: Optional[FilterOptionsIn] = None


class CertificatePropertiesFilterOptions(BaseModel):
    certificate_issuer: Optional[FilterOptionsIn] = None
    certificate_expires_at: Optional[FilterOptionsDateRange] = None
    certificate_issued_at: Optional[FilterOptionsDateRange] = None


class FilterOptionsValueRange(BaseModel):
    name: str
    filter_query: list[str]
    filter_path: str
    filters: list[AssetCountValueRangeFilter]
    filter_type: Optional[str] = 'value_range'


class ExposurePropertiesFilterOptions(BaseModel):
    signature_id: Optional[FilterOptionsIn] = None
    severity: Optional[FilterOptionsIn] = None
    asset_exposure_score: Optional[FilterOptionsValueRange] = None
    last_scanned_at: Optional[FilterOptionsDateRange] = None


class BooleanFilter(BaseModel):
    eq: bool


class ContainsFilter(BaseModel):
    contains: str


class CustomTagPublic(BaseModel):
    title: str


class DateRangeFilter(BaseModel):
    start: Optional[date] = None
    end: Optional[date] = None


class EqFilter(BaseModel):
    eq: Union[date, int, str]


class GeoLocation(BaseModel):
    continent: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    country_iso: Optional[str] = None


class InFilter(BaseModel):
    in_: list[Union[date, ExposureSeverity, int, str]] = Field(alias='in')


class IntEqFilter(BaseModel):
    eq: int


class IntInFilter(BaseModel):
    in_: list[int] = Field(alias='in')


class IntRangeFilter(BaseModel):
    start: Optional[int]
    end: Optional[int]


class CertificatePropertiesFilter(BaseModel):
    certificate_subject: Optional[Union[ContainsFilter, EqFilter, InFilter]] = None
    certificate_subject_alt_name: Optional[Union[ContainsFilter, EqFilter, InFilter]] = None
    certificate_sha256: Optional[EqFilter] = None
    certificate_expires_at: Optional[DateRangeFilter] = None
    certificate_issued_at: Optional[DateRangeFilter] = None
    certificate_issuer: Optional[Union[EqFilter, InFilter]] = None
    certificate_covers_domain: Optional[Union[ContainsFilter, EqFilter, InFilter]] = None


class ExposurePropertiesFilter(BaseModel):
    severity: Optional[Union[EqFilter, InFilter]] = None
    signature_id: Optional[Union[EqFilter, InFilter]] = None
    asset_exposure_score: Optional[IntRangeFilter] = None
    last_scanned_at: Optional[DateRangeFilter] = None


class IPMetadata(BaseModel):
    as_number: Optional[int] = None
    owner_name: Optional[str] = None
    registry: Optional[str] = None
    owner_geo: Optional[GeoLocation] = None


class MembershipType(str, Enum):
    EXCLUDE = 'exclude'
    INCLUDE = 'include'


class NeqFilter(BaseModel):
    neq: Union[date, int, str]


class QuickSearchFilter(BaseModel):
    search: str


class RequireAllFilter(BaseModel):
    in_: list[Union[date, ExposureSeverity, int, str]] = Field(alias='in')


class EmailEqFilter(BaseModel):
    eq: str


class EmailInFilter(BaseModel):
    in_: list[str]


class AssetPropertiesFilter(BaseModel):
    asset_id: Optional[EqFilter] = None
    name: Optional[ContainsFilter] = None
    static_asset: Optional[BooleanFilter] = None
    apex: Optional[Union[EqFilter, InFilter]] = None
    added_to_project: Optional[DateRangeFilter] = None
    discovered: Optional[DateRangeFilter] = None
    asset_type: Optional[EqFilter] = None
    referenced_ip: Optional[Union[ContainsFilter, EqFilter, InFilter]] = None
    cname_reference: Optional[Union[ContainsFilter, EqFilter]] = None
    referenced_ip_at: Optional[DateRangeFilter] = None
    valid_record_type: Optional[Union[EqFilter, InFilter, NeqFilter]] = None
    dns_resolves: Optional[BooleanFilter] = None
    custom_tags: Optional[Union[EqFilter, InFilter, RequireAllFilter]] = None
    custom_tags_strict: Optional[Union[EqFilter, InFilter, RequireAllFilter]] = None
    asn: Optional[Union[IntEqFilter, IntInFilter]] = None
    ip_geo_country_iso: Optional[Union[EqFilter, InFilter]] = None
    ip_owner: Optional[Union[EqFilter, InFilter]] = None
    registry: Optional[Union[EqFilter, InFilter]] = None
    whois_email_current: Optional[Union[EmailEqFilter, EmailInFilter]] = None
    whois_email: Optional[Union[EmailEqFilter, EmailInFilter]] = None


class SortDirection(str, Enum):
    ASC = 'asc'
    DESC = 'desc'


class TagAssetRequest(BaseModel):
    add_tags: Optional[list[str]] = None
    remove_tags: Optional[list[str]] = None


class ValidationError(BaseModel):
    loc: list[Union[int, str]]
    msg: str
    type_: str


class HTTPValidationError(BaseModel):
    detail: Optional[list[ValidationError]] = None


class VulnerabilityPublic(BaseModel):
    name: str
    slug: str
    cvss_score: Optional[float] = None
    cvss_metrics: Optional[str] = None
    references: list[str]
    cve_id: Optional[str] = None
    cwe_ids: Optional[list[Optional[str]]] = None
    epss_score: Optional[float] = None


class ExposureSignature(BaseModel):
    id: str
    name: str
    description: Optional[str]
    severity: Optional[ExposureSeverity]
    references: Optional[list[str]]
    added_at: Optional[datetime] = None
    vulnerabilities: Optional[list[VulnerabilityPublic]] = None


class AssetExposure(BaseModel):
    asset_id: str
    instances: list[ExposureInstance]
    signature: ExposureSignature


class ExposureSummary(BaseModel):
    signature: ExposureSignature
    asset_count: int


class TechnologyInstance(BaseModel):
    seen_at: datetime
    seen_port: int
    seen_url: Optional[str] = None


class DefensiveControl(BaseModel):
    name: str
    vendor: Optional[str] = None
    technology_type: Optional[str] = None
    version: Optional[str] = None
    instances: Optional[list[TechnologyInstance]] = None


class TechnologyPropertiesFilter(BaseModel):
    open_port_number: Optional[Union[IntEqFilter, IntInFilter]] = None
    open_port_service: Optional[Union[EqFilter, InFilter]] = None
    open_port_protocol: Optional[Union[EqFilter, InFilter]] = None
    open_port_technology: Optional[Union[EqFilter, InFilter]] = None
    waf_detected: Optional[BooleanFilter] = None
    waf_name: Optional[Union[EqFilter, InFilter]] = None
    technology_name: Optional[Union[EqFilter, InFilter]] = None
    web_technology_name: Optional[Union[EqFilter, InFilter]] = None
    is_responsive: Optional[BooleanFilter] = None


class AssetSearchFilterIn(BaseModel):
    asset_properties: Optional[AssetPropertiesFilter] = None
    certificate_properties: Optional[CertificatePropertiesFilter] = None
    exposure_properties: Optional[ExposurePropertiesFilter] = None
    technology_properties: Optional[TechnologyPropertiesFilter] = None
    quick_search: Optional[QuickSearchFilter] = None


class AssetSearchRequest(BaseModel):
    filter_: Optional[AssetSearchFilterIn] = Field(None, alias='filter')
    pagination: Optional[Pagination] = None
    enrichments: Optional[list[AssetEnrichment]] = None
    sort: Optional[
        Union[list[AssetSortField], list[list[Union[AssetSortField, SortDirection]]]]
    ] = None


class AssetsFilterRequest(BaseModel):
    filter_: Optional[AssetSearchFilterIn] = None
    filter_fields: Optional[list[str]] = None


class TechnologyPropertiesFilterOptions(BaseModel):
    open_port_number: Optional[FilterOptionsIn] = None
    open_port_service: Optional[FilterOptionsIn] = None
    open_port_protocol: Optional[FilterOptionsIn] = None
    waf_detected: Optional[FilterOptionsEq] = None
    waf_name: Optional[FilterOptionsIn] = None
    technology_name: Optional[FilterOptionsIn] = None
    is_responsive: Optional[FilterOptionsEq] = None


class FiltersResponse(BaseModel):
    asset_properties: AssetPropertiesFilterOptions
    exposure_properties: ExposurePropertiesFilterOptions
    technology_properties: TechnologyPropertiesFilterOptions
    certificate_properties: CertificatePropertiesFilterOptions


class TechnologyWithInstances(BaseModel):
    name: str
    vendor: Optional[str] = None
    technology_type: Optional[str] = None
    version: Optional[str] = None
    instances: Optional[list[TechnologyInstance]] = None


class PortInstance(BaseModel):
    seen_ip: str
    seen_at: datetime
    service: Optional[str] = None
    technology: Optional[TechnologyWithInstances] = None
    web_technologies: Optional[list[TechnologyWithInstances]] = None
    exposures: Optional[list[Exposure]] = None
    defenses: Optional[list[DefensiveControl]] = None


class Port(BaseModel):
    port: int
    protocol: str
    instances: Optional[list[PortInstance]] = None
    certificate: Optional[Certificate] = None


class CertificateInstance(BaseModel):
    certificate: Certificate
    seen_ports: Optional[list[Port]] = None


class ScannedIP(BaseModel):
    ip: str
    last_scanned_at: Optional[datetime] = None
    whois: Optional[WHOISRecord] = None
    open_ports: Optional[list[Port]] = None
    metadata: Optional[IPMetadata] = None
    is_responsive: Optional[bool] = None


class WHOISContact(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    organization: Optional[str] = None
    is_current: Optional[bool] = True


class WHOISRecord(BaseModel):
    registrar: Optional[str] = None
    expires_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    is_private: Optional[bool] = None
    is_from_parent: Optional[bool] = False
    contacts: Optional[list[WHOISContact]] = None
    name_servers: Optional[list[str]] = None


class DNSValue(BaseModel):
    value: Any
    last_resolved_at: Optional[datetime]
    seen_from: Optional[list[str]] = None
    first_seen_at: Optional[datetime] = None


class DNSRecord(BaseModel):
    record_type: str
    value: Optional[list[DNSValue]]
    is_virtual: Optional[bool] = False

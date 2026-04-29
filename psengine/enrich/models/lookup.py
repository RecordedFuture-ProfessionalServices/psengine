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

from ...common_models import IdNameType, IdNameTypeDescription, RFBaseModel


###########################################################
# Enterprise Lists
###########################################################
class EnterpriseList(RFBaseModel):
    added: datetime | None
    list_: IdNameTypeDescription = Field(alias='list')


class RiskyCIDRPIP(RFBaseModel):
    score: int
    ip: IdNameType


class AIInsights(RFBaseModel):
    comment: str | None = None
    text: str | None = None
    number_of_references: int | None = Field(alias='numberOfReferences', default=None)


class EvidenceDetails(RFBaseModel):
    mitigation_string: str = Field(alias='mitigationString')
    evidence_string: str = Field(alias='evidenceString')
    rule: str
    criticality: int
    timestamp: datetime
    criticality_label: str = Field(alias='criticalityLabel')


class EntityRisk(RFBaseModel):
    criticality_label: str = Field(alias='criticalityLabel')
    risk_string: str = Field(alias='riskString')
    rules: int
    criticality: int
    risk_summary: str = Field(alias='riskSummary')
    score: int
    evidence_details: list[EvidenceDetails] = Field(alias='evidenceDetails')


class Sighting(RFBaseModel):
    source: str
    url: str
    published: datetime
    fragment: str
    title: str
    type_: str = Field(alias='type')


class RiskMappingCategory(RFBaseModel):
    framework: str
    name: str


class RiskMapping(RFBaseModel):
    rule: str
    categories: list[RiskMappingCategory] | None = None


class RelatedEntity(RFBaseModel):
    count: int
    entity: IdNameTypeDescription


class RelatedEntities(RFBaseModel):
    entities: list[RelatedEntity]
    type_: str = Field(alias='type')


class GeoLocation(RFBaseModel):
    continent: str | None = None
    country: str | None = None
    city: str | None = None


class IPLocation(RFBaseModel):
    organization: str | None
    cidr: IdNameType
    location: GeoLocation
    asn: str | None = None


class Timestamps(RFBaseModel):
    last_seen: datetime = Field(alias='lastSeen')
    first_seen: datetime = Field(alias='firstSeen')


class ReferenceCount(RFBaseModel):
    date: datetime
    count: int


class Metric(RFBaseModel):
    type_: str = Field(alias='type')
    value: int | float


###########################################################
# Links
###########################################################
class LinksCounts(RFBaseModel):
    count: int
    type_: IdNameTypeDescription = Field(alias='type')


class LinksList(RFBaseModel):
    entities: list[IdNameTypeDescription]
    total_count: int
    type_: IdNameTypeDescription = Field(alias='type')


class SectionHits(RFBaseModel):
    section_id: IdNameType
    total_count: int
    lists: list[LinksList] | None = None


class Hits(RFBaseModel):
    sections: list[SectionHits]
    start_date: datetime
    stop_date: datetime
    total_count: int
    sample_reference_ids: list[str]
    counts: list[LinksCounts]
    event_count: int


class MethodAggregate(RFBaseModel):
    count: int
    type_: str = Field(alias='type')


class Links(RFBaseModel):
    hits: list[Hits]
    method_aggregates: list[MethodAggregate]
    counts: list[LinksCounts]


###########################################################
# Linked Malware
###########################################################
class LinkedMalware(RFBaseModel):
    entities: list[IdNameType]
    total_count: int


###########################################################
# CVSS
###########################################################
class CVSS(RFBaseModel):
    access_vector: str | None = Field(alias='accessVector', default=None)
    last_modified: datetime | None = Field(alias='lastModified', default=None)
    published: datetime | None = None
    score: float | None = None
    availability: str | None = None
    authentication: str | None = None
    access_complexity: str | None = Field(alias='accessComplexity', default=None)
    integrity: str | None = None
    confidentiality: str | None = None
    version: str | None = None


class CVSSRating(RFBaseModel):
    score: float
    modified: datetime
    version: str
    type_: str = Field(alias='type')
    created: datetime


class CVSSV3(RFBaseModel):
    scope: str | None = None
    exploitability_score: float | None = Field(alias='exploitabilityScore', default=None)
    modified: datetime | None = None
    base_severity: str | None = Field(alias='baseSeverity', default=None)
    base_score: float | None = Field(alias='baseScore', default=None)
    privileges_required: str | None = Field(alias='privilegesRequired', default=None)
    user_interaction: str | None = Field(alias='userInteraction', default=None)
    impact_score: float | None = Field(alias='impactScore', default=None)
    attack_vector: str | None = Field(alias='attackVector', default=None)
    integrity_impact: str | None = Field(alias='integrityImpact', default=None)
    confidentiality_impact: str | None = Field(alias='confidentialityImpact', default=None)
    vector_string: str | None = Field(alias='vectorString', default=None)
    version: str | None = None
    attack_complexity: str | None = Field(alias='attackComplexity', default=None)
    created: datetime | None = None
    availability_impact: str | None = Field(alias='availabilityImpact', default=None)


class CVSSV4(RFBaseModel):
    subsequent_system_integrity: str | None = Field(alias='subsequentSystemIntegrity', default=None)
    provider_urgency: str | None = Field(alias='providerUrgency', default=None)
    attack_requirements: str | None = Field(alias='attackRequirements', default=None)
    vulnerable_system_confidentiality: str | None = Field(
        alias='vulnerableSystemConfidentiality', default=None
    )
    vulnerability_response_effort: str | None = Field(
        alias='vulnerabilityResponseEffort', default=None
    )
    threat_score: float | None = Field(alias='threatScore', default=None)
    subsequent_system_availability: str | None = Field(
        alias='subsequentSystemAvailability', default=None
    )
    base_severity: str | None = Field(alias='baseSeverity', default=None)
    base_score: float | None = Field(alias='baseScore', default=None)
    user_interaction: str | None = Field(alias='userInteraction', default=None)
    attack_vector: str | None = Field(alias='attackVector', default=None)
    source: str | None = None
    vulnerable_system_integrity: str | None = Field(alias='vulnerableSystemIntegrity', default=None)
    vulnerable_system_availability: str | None = Field(
        alias='vulnerableSystemAvailability', default=None
    )
    modified: datetime | None = None
    vector_string: str | None = Field(alias='vectorString', default=None)
    recovery: str | None = None
    version: str | None = None
    threat_severity: str | None = Field(alias='threatSeverity', default=None)
    privileges_required: str | None = Field(alias='privilegesRequired', default=None)
    exploit_maturity: str | None = Field(alias='exploitMaturity', default=None)
    safety: str | None = None
    subsequent_system_confidentiality: str | None = Field(
        alias='subsequentSystemConfidentiality', default=None
    )
    automatable: str | None = None
    value_density: str | None = Field(alias='valueDensity', default=None)
    attack_complexity: str | None = Field(alias='attackComplexity', default=None)
    created: datetime | None = None


###########################################################
# Raw Risk
###########################################################
class RawRisk(RFBaseModel):
    rule: str
    timestamp: datetime


###########################################################
# DNS Port Cert
###########################################################
class Validity(RFBaseModel):
    valid_from: datetime = Field(alias='validFrom')
    valid_to: datetime = Field(alias='validTo')


class Issuer(RFBaseModel):
    organization: str | None = None
    location: str | None = None


class Certificate(RFBaseModel):
    subject: str | None = None
    validity: Validity
    issuer: Issuer
    seen_on_port: list[int] = Field(alias='seenOnPort')


class ForwardDNS(RFBaseModel):
    hostname: str | None = None
    last_seen: datetime | None = Field(alias='lastSeen')
    first_seen: datetime | None = Field(alias='firstSeen')


class DNS(RFBaseModel):
    forward_dns: list[ForwardDNS] = Field(alias='forwardDns')
    reverse_dns: str | None = Field(alias='reverseDns', default=None)


class Port(RFBaseModel):
    name: str | None = None
    version: str | None
    port: int
    extra_info: str | None = Field(alias='extraInfo')
    protocol: str
    product: str | None


class DnsPortCert(RFBaseModel):
    certificates: list[Certificate] | None = None
    dns: DNS | None = None
    ports: list[Port] | None = None


###########################################################
# Scanner
###########################################################
class Tag(RFBaseModel):
    verdict_details: list[str] | None = Field(default=None, alias='verdictDetails')
    entity: list[IdNameType]


class Ports(RFBaseModel):
    tcp: list[int]


class Evidence(RFBaseModel):
    name: str = Field(alias='Name')
    mitigation_string: str = Field(default=None, alias='MitigationString')
    evidence_string: str = Field(alias='EvidenceString', default=None)
    rule: str = Field(alias='Rule')
    criticality: float = Field(alias='Criticality')
    timestamp: datetime = Field(alias='Timestamp')
    criticality_label: str = Field(alias='CriticalityLabel')
    sources_count: float = Field(alias='SourcesCount')
    sightings_count: float = Field(alias='SightingsCount')
    sources: list[str] = Field(alias='Sources')


class Scanner(RFBaseModel):
    last_seen: str = Field(alias='lastSeen')
    tags: Tag
    verdict: str
    scanned_ip_countries: list[str] = Field(alias='scannedIpCountries')
    rdns: list[str]
    scanner_country: str = Field(alias='scannerCountry')
    ports: Ports
    global_scanner: bool = Field(alias='globalScanner')
    user_agents: list[str] = Field(alias='userAgents', default=None)
    web_requests: list[str] = Field(alias='webRequests', default=None)
    evidence: list[Evidence] | None = []


###########################################################
# NVD
###########################################################
class NvdReference(RFBaseModel):
    url: str
    tags: list[str]

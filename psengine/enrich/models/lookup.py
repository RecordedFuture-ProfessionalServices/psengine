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
from typing import Optional, Union

from pydantic import Field

from ...common_models import IdNameType, IdNameTypeDescription, RFBaseModel


###########################################################
# Enterprise Lists
###########################################################
class EnterpriseList(RFBaseModel):
    added: Optional[datetime]
    list_: IdNameTypeDescription = Field(alias='list')


###########################################################
class RiskyCIDRPIP(RFBaseModel):
    score: int
    ip: IdNameType


class AIInsights(RFBaseModel):
    comment: Optional[str] = None
    text: Optional[str] = None
    number_of_references: Optional[int] = Field(alias='numberOfReferences', default=None)


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
    categories: Optional[list[RiskMappingCategory]] = None


class RelatedEntity(RFBaseModel):
    count: int
    entity: IdNameTypeDescription


class RelatedEntities(RFBaseModel):
    entities: list[RelatedEntity]
    type_: str = Field(alias='type')


class GeoLocation(RFBaseModel):
    continent: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None


class IPLocation(RFBaseModel):
    organization: Optional[str]
    cidr: IdNameType
    location: GeoLocation
    asn: Optional[str] = None


class Timestamps(RFBaseModel):
    last_seen: datetime = Field(alias='lastSeen')
    first_seen: datetime = Field(alias='firstSeen')


class ReferenceCount(RFBaseModel):
    date: datetime
    count: int


class Metric(RFBaseModel):
    type_: str = Field(alias='type')
    value: Union[int, float]


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
    lists: Optional[list[LinksList]] = None


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
    access_vector: Optional[str] = Field(alias='accessVector', default=None)
    last_modified: Optional[datetime] = Field(alias='lastModified', default=None)
    published: Optional[datetime] = None
    score: Optional[float] = None
    availability: Optional[str] = None
    authentication: Optional[str] = None
    access_complexity: Optional[str] = Field(alias='accessComplexity', default=None)
    integrity: Optional[str] = None
    confidentiality: Optional[str] = None
    version: Optional[str] = None


class CVSSRating(RFBaseModel):
    score: float
    modified: datetime
    version: str
    type_: str = Field(alias='type')
    created: datetime


class CVSSV3(RFBaseModel):
    scope: Optional[str] = None
    exploitability_score: Optional[float] = Field(alias='exploitabilityScore', default=None)
    modified: Optional[datetime] = None
    base_severity: Optional[str] = Field(alias='baseSeverity', default=None)
    base_score: Optional[float] = Field(alias='baseScore', default=None)
    privileges_required: Optional[str] = Field(alias='privilegesRequired', default=None)
    user_interaction: Optional[str] = Field(alias='userInteraction', default=None)
    impact_score: Optional[float] = Field(alias='impactScore', default=None)
    attack_vector: Optional[str] = Field(alias='attackVector', default=None)
    integrity_impact: Optional[str] = Field(alias='integrityImpact', default=None)
    confidentiality_impact: Optional[str] = Field(alias='confidentialityImpact', default=None)
    vector_string: Optional[str] = Field(alias='vectorString', default=None)
    version: Optional[str] = None
    attack_complexity: Optional[str] = Field(alias='attackComplexity', default=None)
    created: Optional[datetime] = None
    availability_impact: Optional[str] = Field(alias='availabilityImpact', default=None)


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
    organization: Optional[str] = None
    location: Optional[str] = None


class Certificate(RFBaseModel):
    subject: Optional[str] = None
    validity: Validity
    issuer: Issuer
    seen_on_port: list[int] = Field(alias='seenOnPort')


class ForwardDNS(RFBaseModel):
    hostname: Optional[str] = None
    last_seen: Union[datetime, None] = Field(alias='lastSeen')
    first_seen: Union[datetime, None] = Field(alias='firstSeen')


class DNS(RFBaseModel):
    forward_dns: list[ForwardDNS] = Field(alias='forwardDns')
    reverse_dns: Optional[str] = Field(alias='reverseDns', default=None)


class Port(RFBaseModel):
    name: str
    version: Union[str, None]
    port: int
    extra_info: Union[str, None] = Field(alias='extraInfo')
    protocol: str
    product: Union[str, None]


class DnsPortCert(RFBaseModel):
    certificates: Optional[list[Certificate]] = None
    dns: Optional[DNS] = None
    ports: Optional[list[Port]] = None


###########################################################
# NVD
###########################################################


class NvdReference(RFBaseModel):
    url: str
    tags: list[str]

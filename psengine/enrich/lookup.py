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
from functools import total_ordering

from pydantic import Field

from ..common_models import IdNameType, IdNameTypeDescription, RFBaseModel
from ..constants import TIMESTAMP_STR
from .models.base_enriched_entity import BaseEnrichedEntity
from .models.lookup import (
    CVSS,
    CVSSV3,
    CVSSV4,
    CVSSRating,
    DnsPortCert,
    EnterpriseList,
    EntityRisk,
    IPLocation,
    LinkedMalware,
    Links,
    NvdReference,
    RawRisk,
    RiskMapping,
    RiskyCIDRPIP,
    Scanner,
)


class EnrichedIP(BaseEnrichedEntity):
    """IP Enriched by `/v2/ip/{ip}` endpoint. Inherit behaviours from `BaseEnrichedEntity`."""

    risk: EntityRisk | None = None
    links: Links | None = None
    enterprise_lists: list[EnterpriseList] | None = Field(alias='enterpriseLists', default=None)
    threat_list: list[IdNameTypeDescription] | None = Field(alias='threatLists', default=None)
    risk_mapping: list[RiskMapping] | None = Field(alias='riskMapping', default=None)
    dns_port_cert: DnsPortCert | None = Field(alias='dnsPortCert', default=None)
    location: IPLocation | None = None
    risky_cidr_ips: list[RiskyCIDRPIP] | None = Field(alias='riskyCIDRIPs', default=None)
    scanner: Scanner | None = None


class EnrichedDomain(BaseEnrichedEntity):
    """Domain Enriched by `/v2/domain/{domain}` endpoint.
    Inherit behaviours from `BaseEnrichedEntity`.
    """

    risk: EntityRisk | None = None
    links: Links | None = None
    enterprise_lists: list[EnterpriseList] | None = Field(alias='enterpriseLists', default=None)
    threat_lists: list[IdNameTypeDescription] | None = Field(alias='threatLists', default=None)
    risk_mapping: list[RiskMapping] | None = Field(alias='riskMapping', default=None)


class EnrichedURL(BaseEnrichedEntity):
    """URL Enriched by `/v2/url/{url}` endpoint.
    Inherit behaviours from `BaseEnrichedEntity`.
    """

    risk: EntityRisk | None = None
    links: Links | None = None
    enterprise_lists: list[EnterpriseList] | None = Field(alias='enterpriseLists', default=None)
    risk_mapping: list[RiskMapping] | None = Field(alias='riskMapping', default=None)


class EnrichedHash(BaseEnrichedEntity):
    """Hash Enriched by `/v2/hash/{hash}` endpoint.
    Inherit behaviours from `BaseEnrichedEntity`.
    """

    risk: EntityRisk | None = None
    links: Links | None = None
    enterprise_lists: list[EnterpriseList] | None = Field(alias='enterpriseLists', default=None)
    threat_list: list[IdNameTypeDescription] | None = Field(alias='threatLists', default=None)
    risk_mapping: list[RiskMapping] | None = Field(alias='riskMapping', default=None)
    hash_algorithm: str | None = Field(alias='hashAlgorithm', default=None)
    file_hashes: list[str] | None = Field(alias='fileHashes', default=None)


class EnrichedVulnerability(BaseEnrichedEntity):
    """Vulnerability Enriched by `/v2/vulnerability/{cve}` endpoint.
    Inherit behaviours from `BaseEnrichedEntity`.
    """

    risk: EntityRisk | None = None
    links: Links | None = None
    enterprise_lists: list[EnterpriseList] | None = Field(alias='enterpriseLists', default=None)
    threat_list: list[IdNameTypeDescription] | None = Field(alias='threatLists', default=None)
    risk_mapping: list[RiskMapping] | None = Field(alias='riskMapping', default=None)
    common_names: list[str] | None = Field(alias='commonNames', default=None)
    lifecycle_stage: str | None = Field(alias='lifecycleStage', default=None)
    linked_malware: LinkedMalware | None = Field(alias='linkedMalware', default=None)
    cpe: list[str] | None = None
    cpe_22_uri: list[str] | None = Field(alias='cpe22uri', default=None)
    cvss: CVSS | None = None
    cvss_ratings: list[CVSSRating] = Field(alias='cvssRatings', default=None)
    cvssv3: CVSSV3 | None = None
    cvssv4: CVSSV4 | None = None
    nvd_description: str | None = Field(alias='nvdDescription', default=None)
    nvd_references: list[NvdReference] | None = Field(alias='nvdReferences', default=None)
    raw_risk: list[RawRisk] | None = Field(alias='rawrisk', default=None)
    related_links: list[str] | None = Field(alias='relatedLinks', default=None)


class EnrichedMalware(BaseEnrichedEntity):
    """Malware Enriched by `/v2/malware/{id}` endpoint.
    Inherit behaviours from `BaseEnrichedEntity`.
    """

    links: Links | None = None
    categories: list[IdNameType] | None = None


class EnrichedCompany(BaseEnrichedEntity):
    """Company Enriched by `/v2/company/{id}` and `/v2/company/by_domain/{domain}` endpoint.
    Inherit behaviours from `BaseEnrichedEntity`.
    """

    risk: EntityRisk | None = None
    curated: bool | None = None
    threat_list: list[IdNameTypeDescription] | None = Field(alias='threatLists', default=None)
    risk_mapping: list[RiskMapping] | None = Field(alias='riskMapping', default=None)


_EnrichmentObjectType = (
    EnrichedCompany
    | EnrichedDomain
    | EnrichedIP
    | EnrichedHash
    | EnrichedMalware
    | EnrichedURL
    | EnrichedVulnerability
)


@total_ordering
class EnrichmentData(RFBaseModel):
    """Model for the custom return of IOC lookups.

    This class supports hashing, equality comparison, string representation, and total
    ordering of `EnrichmentData` instances based on their `content`.

    Hashing:
        Returns a hash value based on the content's attributes.

        - If `content` is an instance of `EnrichedMalware`:
            The hash is calculated using the entity `id_` and the last seen timestamp.
        - Else:
            The hash includes the entity `id_`, risk score, and the last seen timestamp.

    Equality:
        Checks equality between two `EnrichmentData` instances based on their `content`.

        - If `content` is an instance of `EnrichedMalware`:
            Equality is determined by comparing the entity name and the last seen timestamp.
        - Else:
            Equality is determined by comparing the entity name, last seen timestamp, and
            risk score.

    Greater-than Comparison:
        Defines a greater-than comparison between `EnrichmentData` instances based on their
        `content`.

        - If `content` is an instance of `EnrichedMalware`:
            Comparison is based on the last seen timestamp and entity name.
        - Else:
            Comparison is based on the last seen timestamp, entity name, and risk score.

    String Representation:
        `__str__` and `__repr__` return a formatted string representation of the instance.

        - If `content` is an instance of `EnrichedMalware`:
            Includes class name, entity name, and last seen timestamp.
        - Else:
            Includes class name, entity name, risk score, and last seen timestamp.

        ```python
        >>> print(enrichment_data)
        EnrichedIP: 1.1.1.1, Risk Score: 85, Last Seen: 2024-05-21 01:30:00PM
        ```

    Total ordering:
        The ordering of `EnrichmentData` instances is determined by the content's last seen
        timestamp.

        - If `content` is an instance of `EnrichedMalware`:
            If two instances have the same last seen timestamp, their entity name is used as a
            secondary criterion.
        - Else:
            If two instances have the same last seen timestamp, their entity name and risk score are
            used as secondary criteria.
    """

    entity: str
    entity_type: str | None
    is_enriched: bool
    content: str | _EnrichmentObjectType

    def __hash__(self):
        if isinstance(self.content, EnrichedMalware):
            return hash(
                (
                    self.content.entity.id_,
                    self.content.timestamps.last_seen,
                )
            )
        if isinstance(self.content, str):
            return hash(self.entity)

        return hash(
            (
                self.content.entity.id_,
                self.content.risk.score,
                self.content.timestamps.last_seen,
            )
        )

    def __eq__(self, other: 'EnrichmentData'):
        if isinstance(self.content, EnrichedMalware):
            return (
                self.content.entity.name,
                self.content.timestamps.last_seen,
            ) == (
                other.content.entity.name,
                other.content.timestamps.last_seen,
            )
        if isinstance(self.content, str):
            return self.entity == other.entity
        return (
            self.content.risk.score,
            self.content.entity.name,
            self.content.timestamps.last_seen,
        ) == (
            other.content.risk.score,
            other.content.entity.name,
            other.content.timestamps.last_seen,
        )

    def __gt__(self, other: 'EnrichmentData'):
        if isinstance(self.content, EnrichedMalware):
            return (
                self.content.timestamps.last_seen,
                self.content.entity.name,
            ) > (
                other.content.timestamps.last_seen,
                other.content.entity.name,
            )
        if isinstance(self.content, str):
            return self.entity > other.entity
        return (
            self.content.risk.score,
            self.content.timestamps.last_seen,
            self.content.entity.name,
        ) > (
            other.content.risk.score,
            other.content.timestamps.last_seen,
            other.content.entity.name,
        )

    def __str__(self):
        if isinstance(self.content, EnrichedMalware):
            return (
                f'{self.content.__class__.__name__}: {self.content.entity.name}, '
                f'Last Seen: {self.content.timestamps.last_seen.strftime(TIMESTAMP_STR)}'
            )
        if isinstance(self.content, str):
            return f'{self.entity}: {self.content}'
        return (
            f'{self.content.__class__.__name__}: {self.content.entity.name}, '
            f'Risk Score: {self.content.risk.score}, '
            f'Last Seen: {self.content.timestamps.last_seen.strftime(TIMESTAMP_STR)}'
        )

    def __repr__(self):
        if isinstance(self.content, EnrichedMalware):
            return (
                f'{self.content.__class__.__name__}: {self.content.entity.name}, '
                f'Last Seen: {self.content.timestamps.last_seen.strftime(TIMESTAMP_STR)}'
            )
        if isinstance(self.content, str):
            return f'{self.entity}: {self.content}'
        return (
            f'{self.content.__class__.__name__}: {self.content.entity.name}, '
            f'Risk Score: {self.content.risk.score}, '
            f'Last Seen: {self.content.timestamps.last_seen.strftime(TIMESTAMP_STR)}'
        )

    def links(self, from_section: str, entity_type: str) -> list[str]:
        """Retrieve a list of entities from the links attribute of the specific type and section."""
        results = []
        if not hasattr(self.content, 'links'):
            return []

        results.extend(
            entity.name
            for hit in self.content.links.hits
            for section in hit.sections
            if section.section_id and section.section_id.name == from_section
            for lst in section.lists
            for entity in lst.entities
            if entity.type_ == entity_type
        )

        return results

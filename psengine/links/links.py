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


from collections import defaultdict

from ..common_models import IdNameType, RFBaseModel
from .models import EntityAttribute, EntitySearchError, LinksFilterObjects, LinksLimitsObjects

LINK_IOC_TYPE = [
    'type:InternetDomainName',
    'type:CyberVulnerability',
    'type:IpAddress',
    'type:Hash',
    'type:Url',
]


class LinkedIOC(IdNameType):
    """Return linked iocs entities."""

    risk_score: int
    source: str | None = None


class LinkedTTP(IdNameType):
    """Return linked TTPs entities."""

    display_name: str
    source: str | None = None


class LinkedTA(IdNameType):
    """Return linked threat actors entities."""

    source: str | None = None


class LinkedMalware(IdNameType):
    """Return linked malware entities."""

    source: str | None = None


class LinkedEntity(IdNameType):
    """An entity connected to the search target."""

    source: str | None = None
    section: str | None = None
    attributes: list[EntityAttribute] = []


class EntityLinks(RFBaseModel):
    """The result set for a single entity that was queried."""

    entity: IdNameType | None = None
    links: list[LinkedEntity] = []
    error: EntitySearchError | None = None

    def iocs(self) -> list[LinkedIOC]:
        """Return linked indicators of compromise grouped by IOC type."""
        iocs = defaultdict(list)
        for link in self.links:
            if link.type_ in LINK_IOC_TYPE:
                ioc_score = next(
                    (attr.value for attr in link.attributes if attr.id_ == 'risk_score'),
                    0,
                )
                iocs[link.type_].append(
                    LinkedIOC(
                        id=link.id_,
                        type=link.type_,
                        name=link.name,
                        risk_score=ioc_score,
                        source=link.source,
                    )
                )

        return iocs

    def ttps(self) -> list[LinkedTTP]:
        """Return linked MITRE ATT&CK techniques and their display names."""
        ttps = []
        for link in self.links:
            if link.type_ == 'type:MitreAttackIdentifier':
                display_name = next(
                    (attr.value for attr in link.attributes if attr.id_ == 'display_name'),
                    'N/A',
                )
                ttps.append(
                    LinkedTTP(
                        id=link.id_,
                        type=link.type_,
                        name=link.name,
                        display_name=display_name,
                        source=link.source,
                    )
                )

        return ttps

    def threat_actors(self) -> list[LinkedTA]:
        """Return linked organizations marked as threat actors."""
        tas = []
        for link in self.links:
            if link.type_ == 'type:Organization':
                is_threat_actor = next(
                    (attr.value for attr in link.attributes if attr.id_ == 'threat_actor'),
                    False,
                )
                if is_threat_actor:
                    tas.append(
                        LinkedTA(
                            id=link.id_,
                            type=link.type_,
                            name=link.name,
                            source=link.source,
                        )
                    )

        return tas

    def malwares(self) -> list[LinkedMalware]:
        """Return linked malware entities."""
        return [
            LinkedMalware(
                id=link.id_,
                type=link.type_,
                name=link.name,
                source=link.source,
            )
            for link in self.links
            if link.type_ == 'type:Malware'
        ]


class LinksSearchIn(RFBaseModel):
    """Model for payload sent to POST `/links/search` endpoint."""

    entities: list[str]
    filters: LinksFilterObjects | None = None
    limits: LinksLimitsObjects | None = None

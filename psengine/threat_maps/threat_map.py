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

from ..common_models import IdName, RFBaseModel
from .models import EntityAttributes, LogEntry, ThreatActorAttributes


class ThreatMapEntity(RFBaseModel):
    """Model to validate data received from the `threat/map/{type}` endpoint.

    This class supports string representation, equality comparison, and hashing of `ThreatMapEntity`
    instances.

    Hashing:
        Defines uniqueness of an `ThreatMapEntity` object by the entity ID.

    Equality:
        Validates equality between two `ThreatMapEntity` objects based on the entity ID.

    String Representation:
        Returns a string representation of the `ThreatMapEntity` instance including the
        entity match name, ID, opportunity, and intent or prevalence depending on category.

        ```python
        >>> print(entity)
        Entity Name: BlueDelta, ID: L37nw-, Opportunity: 65, Intent: 65'
        ```
    """

    id_: str = Field(alias='id')
    name: str
    alias: list[str]
    categories: list[IdName]
    intent: int | None = None
    prevalence: int | None = None
    opportunity: int
    log_entries: list[LogEntry]

    def __hash__(self):
        return hash(self.id_)

    def __eq__(self, other: 'ThreatMapEntity'):
        return self.id_ == other.id_

    def __str__(self):
        key = 'intent' if self.intent is not None else 'prevalence'
        score = getattr(self, key)
        return (
            f'Entity Name: {self.name}, ID: {self.id_}, '
            f'Opportunity: {self.opportunity}, {key.capitalize()}: {score}'
        )


class ThreatMap(RFBaseModel):
    """Model for payload received by POST `/threat/map/{type}` endpoint."""

    threat_map: list[ThreatMapEntity]
    date: datetime = Field(description='Threat map generation timestamp')

    def __str__(self):
        data = '\n'.join(str(entity) for entity in self.threat_map)
        return f'[{data}]'


class ThreatMapInfo(RFBaseModel):
    """Model for payload received by GET `/threat/maps` endpoint."""

    name: str
    type_: str = Field(alias='type')
    organization: IdName
    url: str


class EntityCategory(RFBaseModel):
    """Model for payload received by GET `threat/{type}/categories` endpoint."""

    id_: str = Field(alias='id')
    type_: str = Field(alias='type')
    attributes: EntityAttributes


class ThreatActorProfile(RFBaseModel):
    """Model for payload received by POST `threat/actor/search` endpoint."""

    id_: str = Field(alias='id')
    type_: str = Field(alias='type')
    attributes: ThreatActorAttributes


class ThreatActorSearchOut(RFBaseModel):
    """Model to validate `/threat/actor/search` endpoint payload sent."""

    name: str | None = None
    limit: int = Field(ge=1, le=10000, default=1000)
    offset: str | None = None


class ThreatMapFetchOut(RFBaseModel):
    """Model to validate `threat/map/{org}/{type}` endpoint payload sent."""

    malware: list[str] | None = None
    actors: list[str] | None = None
    categories: list[str] | None = None
    watchlists: list[str] | None = None

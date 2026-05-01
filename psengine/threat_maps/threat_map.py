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
from functools import total_ordering
from typing import Annotated

from pydantic import BeforeValidator, Field

from ..common_models import IdName, RFBaseModel
from ..helpers.helpers import Validators
from .models import EntityAttributes, LogEntry, ThreatActorAttributes


@total_ordering
class ThreatMapEntity(RFBaseModel):
    """Model to validate data received from the `threat/map/{type}` endpoint.

    This class supports string representation, equality comparison, and hashing of `ThreatMapEntity`
    instances.

    Hashing:
        Defines uniqueness of a `ThreatMapEntity` object by the entity ID.

    Equality:
        Validates equality between two `ThreatMapEntity` objects based on the entity ID.

    Greater-than Comparison:
        Defines a greater-than comparison between two `ThreatMapEntity` instances based on
        `opportunity`, `intent` and `prevalence`. Lastly on `id_`

    String Representation:
        Returns a string representation of the `ThreatMapEntity` instance including the
        entity match name, ID, opportunity, and intent or prevalence depending on category.

        ```python
        >>> print(entity)
        Entity Name: BlueDelta, ID: L37nw-, Opportunity: 65, Intent: 65'
        ```
    Ordering:
        The ordering of `ThreatMapEntity` instances is determined primarily by the `opportunity`
        score followed by the `intent` and `prevalence`.
        If two instances have the same scores, the `id_` is used as a last criterion.
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

    def __gt__(self, other: 'ThreatMapEntity'):
        return (self.opportunity, self.intent or 0, self.prevalence or 0, self.id_) > (
            other.opportunity or 0,
            other.intent or 0,
            other.prevalence or 0,
            other.id_,
        )

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
        return '\n'.join(str(entity) for entity in sorted(self.threat_map))


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

    def __str__(self):
        attr = self.attributes
        common = f', Common Names: {", ".join(attr.common_names)}' if attr.common_names else ''
        return f'ID: {self.id_} Name: {attr.name}' + common


class ThreatMapFetchIn(RFBaseModel):
    """Model to validate `threat/map/{org}/{type}` endpoint payload sent."""

    malware: Annotated[list[str] | None, BeforeValidator(Validators.convert_str_to_list)] = None
    actors: Annotated[list[str] | None, BeforeValidator(Validators.convert_str_to_list)] = None
    categories: Annotated[list[str] | None, BeforeValidator(Validators.convert_str_to_list)] = None
    watchlists: Annotated[list[str] | None, BeforeValidator(Validators.convert_str_to_list)] = None

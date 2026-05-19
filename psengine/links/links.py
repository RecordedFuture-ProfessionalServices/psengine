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

from typing import Annotated, Literal

from pydantic import AfterValidator

from ..common_models import IdNameType, RFBaseModel
from ..helpers import TimeHelpers
from .models import EntityAttribute, EntitySearchError


def _validate_rel_time(v: str | None) -> str | None:
    if v is not None and not TimeHelpers.is_rel_time_valid(v):
        raise ValueError(f'Invalid relative time: {v}')
    return v


class FilterTechnical(RFBaseModel):
    """Fields in the Technical Object of Filters."""

    timeframe: Annotated[str | None, AfterValidator(_validate_rel_time)] = None
    events: list[str] | None = None
    connected_entities: list[str] | None = None


class LinksFilterObjects(RFBaseModel):
    """Objects in the fields data parameter of links."""

    sections: list[str] | None = None
    entity_types: list[str] | None = None
    sources: list[Literal['technical', 'insikt']] | None = None
    technical: FilterTechnical | None = None


class LinksLimitsObjects(RFBaseModel):
    """Objects in the limits object fields."""

    search_scope: Literal['small', 'medium', 'large'] | None = None
    per_entity_type: int | None = None


class LinksSearchIn(RFBaseModel):
    """Model for payload sent to POST `/links/search` endpoint."""

    entities: list[str]
    filters: LinksFilterObjects | None = None
    limits: LinksLimitsObjects | None = None


class LinkedEntity(IdNameType):
    """An entity connected to the search target.

    Inherits id_ (alias 'id'), name, and type_ (alias 'type') from IdNameType.
    """

    source: str | None = None
    section: str | None = None
    attributes: list[EntityAttribute] = []


class SearchResultSet(RFBaseModel):
    """The result set for a single entity that was queried."""

    entity: IdNameType | None = None
    links: list[LinkedEntity] = []
    error: EntitySearchError | None = None


class LinksSearchResponse(RFBaseModel):
    """Response from POST `/links/search` endpoint."""

    data: list[SearchResultSet] = []

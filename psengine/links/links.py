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

from typing import Annotated, Literal, Optional

from pydantic import AfterValidator

from ..common_models import IdNameType, RFBaseModel
from ..helpers import TimeHelpers
from .models import EntityAttribute, EntitySearchError


def _validate_rel_time(v: Optional[str]) -> Optional[str]:
    if v is not None and not TimeHelpers.is_rel_time_valid(v):
        raise ValueError(f'Invalid relative time: {v}')
    return v


class FilterTechnical(RFBaseModel):
    """Fields in the Technical Object of Filters."""

    timeframe: Annotated[Optional[str], AfterValidator(_validate_rel_time)] = None
    events: Optional[list[str]] = None
    connected_entities: Optional[list[str]] = None


class LinksFilterObjects(RFBaseModel):
    """Objects in the fields data parameter of links."""

    sections: Optional[list[str]] = None
    entity_types: Optional[list[str]] = None
    sources: Optional[list[Literal['technical', 'insikt']]] = None
    technical: Optional[FilterTechnical] = None


class LinksLimitsObjects(RFBaseModel):
    """Objects in the limits object fields."""

    search_scope: Optional[Literal['small', 'medium', 'large']] = None
    per_entity_type: Optional[int] = None


class LinksSearchIn(RFBaseModel):
    """Model for payload sent to POST `/links/search` endpoint."""

    entities: list[str]
    filters: Optional[LinksFilterObjects] = None
    limits: Optional[LinksLimitsObjects] = None


class LinkedEntity(IdNameType):
    """An entity connected to the search target.

    Inherits id_ (alias 'id'), name, and type_ (alias 'type') from IdNameType.
    """

    source: Optional[str] = None
    section: Optional[str] = None
    attributes: list[EntityAttribute] = []


class SearchResultSet(RFBaseModel):
    """The result set for a single entity that was queried."""

    entity: Optional[IdNameType] = None
    links: list[LinkedEntity] = []
    error: Optional[EntitySearchError] = None


class LinksSearchResponse(RFBaseModel):
    """Response from POST `/links/search` endpoint."""

    data: list[SearchResultSet] = []

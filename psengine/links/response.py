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

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import Field

from ..common_models import IdName, IdNameType, RFBaseModel


###########################################################
# Metadata Response Models (For Metadata Endpoints)
###########################################################


class MetadataSection(IdName):
    """Represents a specific section from the Links Metadata API."""

    description: Optional[str] = Field(
        default=None,
        description="Includes an 'id' which is a filter value ID to use in the Links Search requests and a 'name' which is a human-readable name",
    )


class MetadataSectionsResponse(RFBaseModel):
    """Response wrapper for GET /links/metadata/sections."""

    data: list[MetadataSection] = Field(
        description="The response contains a small array of section objects, each with an id (used as filter value in Links: Search) and a human-readable name."
    )


class MetadataEvent(IdName):
    """Represents a specific event type from the Links Metadata API."""

    description: Optional[str] = Field(
        default=None,
        description="Includes an 'id' which is a filter value ID to use in the Links Search requests and a 'name' which is a human-readable name",
    )


class MetadataEventsResponse(RFBaseModel):
    """Response wrapper for GET /links/metadata/events."""

    data: list[MetadataEvent] = Field(
        description='Returns event type objects. Use the id field as the filter value in Links Search.'
    )


class MetadataEntityTypesResponse(RFBaseModel):
    """Response wrapper for GET /links/metadata/entities."""

    data: list[IdName] = Field(
        description='Returns the complete set of supported entity types. Use the id field as the filter value.'
    )


###########################################################
# Search Response Models (For POST /links/search)
###########################################################


class RiskAttribute(RFBaseModel):
    """An attribute describing a risk score or risk level."""

    id_: Literal['risk_score', 'risk_level'] = Field(
        alias='id', description='risk_score or risk_level'
    )
    value: Optional[Union[float, str]] = Field(default=None, description='Value 0 to 99 or level string')


class CriticalityAttribute(RFBaseModel):
    """An attribute describing a criticality level."""

    id_: Literal['criticality'] = Field(alias='id', description='criticality')
    value: Optional[str] = Field(default=None)


class MitreNameAttribute(RFBaseModel):
    """An attribute describing a MITRE technique name."""

    id_: Literal['display_name'] = Field(alias='id', description='display_name')
    value: Optional[str] = Field(default=None)


class ThreatActorAttribute(RFBaseModel):
    """An attribute describing a threat actor flag."""

    id_: Literal['threat_actor'] = Field(alias='id', description='threat_actor')
    value: Optional[bool] = Field(default=None)


class GenericAttribute(RFBaseModel):
    """Fallback for any unknown attributes returned by the API."""

    id_: str = Field(alias='id')
    value: Any


# This is the Union that handles the 'attributes' array.
# Pydantic will match the specific models based on the Literal 'id' values.
# If no Literal matches, it falls back to GenericAttribute.
EntityAttribute = Union[
    RiskAttribute,
    CriticalityAttribute,
    MitreNameAttribute,
    ThreatActorAttribute,
    GenericAttribute,
]


class LinkedEntity(IdNameType):
    """
    An entity connected to the search target.
    Inherits id_ (alias 'id'), name, and type_ (alias 'type') from IdNameType.
    """

    source: Optional[str] = Field(
        default=None, description="Link source: 'technical' or 'insikt'."
    )
    section: Optional[str] = Field(default=None, description='The Link category section ID.')
    attributes: list[EntityAttribute] = Field(
        default_factory=list, description='Array of entity-specific risk and context attributes.'
    )


class EntitySearchError(RFBaseModel):
    """Error details for a specific entity failure within a batch search."""

    message: str = Field(description='Error message describing why the search failed.')
    status_code: int = Field(description='The HTTP status code associated with the failure.')


class SearchResultSet(RFBaseModel):
    """The result set for a single entity that was queried."""

    entity: Optional[IdNameType] = Field(
        default=None, description='The original entity for which the search was performed.'
    )
    links: list[LinkedEntity] = Field(
        default_factory=list, description='An array of entities connected to the target entity.'
    )
    error: Optional[EntitySearchError] = Field(
        default=None, description='Present only if the search for this specific entity failed.'
    )


class LinksSearchResponse(RFBaseModel):
    """The root response object returned by the Links Search API."""

    data: list[SearchResultSet] = Field(
        default_factory=list,
        description='An array where each element represents a result set for a queried entity.',
    )

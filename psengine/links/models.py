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

from typing import Any, Literal

from pydantic import Field

from ..common_models import IdName, RFBaseModel


class MetadataSection(IdName):
    description: str | None = None


class MetadataSectionsResponse(RFBaseModel):
    """Response from GET `/links/metadata/sections` endpoint."""

    data: list[MetadataSection]


class MetadataEvent(IdName):
    description: str | None = None


class MetadataEventsResponse(RFBaseModel):
    """Response from GET `/links/metadata/events` endpoint."""

    data: list[MetadataEvent]


class MetadataEntityTypesResponse(RFBaseModel):
    """Response from GET `/links/metadata/entities` endpoint."""

    data: list[IdName]


class RiskAttribute(RFBaseModel):
    id_: Literal['risk_score', 'risk_level'] = Field(alias='id')
    value: float | str | None = None


class CriticalityAttribute(RFBaseModel):
    id_: Literal['criticality'] = Field(alias='id')
    value: str | None = None


class MitreNameAttribute(RFBaseModel):
    id_: Literal['display_name'] = Field(alias='id')
    value: str | None = None


class ThreatActorAttribute(RFBaseModel):
    id_: Literal['threat_actor'] = Field(alias='id')
    value: bool | None = None


class GenericAttribute(RFBaseModel):
    id_: str = Field(alias='id')
    value: Any


# Discriminated union for the 'attributes' array. Pydantic matches on the
# Literal 'id' values; unknown ids fall back to GenericAttribute.
EntityAttribute = (
    RiskAttribute
    | CriticalityAttribute
    | MitreNameAttribute
    | ThreatActorAttribute
    | GenericAttribute
)


class EntitySearchError(RFBaseModel):
    message: str
    status_code: int

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

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BeforeValidator, Field

from ..common_models import RFBaseModel
from ..helpers.helpers import Validators


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


class LinkSource(Enum):
    """RF Links API source filter."""

    technical = 'technical'
    insikt = 'insikt'


class SearchScope(Enum):
    """RF Links API search scope."""

    small = 'small'
    medium = 'medium'
    large = 'large'


class FilterTechnical(RFBaseModel):
    """Fields in the Technical Object of Filters."""

    timeframe: Annotated[str | None, AfterValidator(Validators.is_rel_time_valid)] = None
    events: Annotated[list[str] | None, BeforeValidator(Validators.convert_str_to_list)] = None
    connected_entities: Annotated[
        list[str] | None, BeforeValidator(Validators.convert_str_to_list)
    ] = None


class LinksFilterObjects(RFBaseModel):
    """Objects in the fields data parameter of links."""

    sections: Annotated[list[str] | None, BeforeValidator(Validators.convert_str_to_list)] = None
    entity_types: Annotated[list[str] | None, BeforeValidator(Validators.convert_str_to_list)] = (
        None
    )
    sources: list[LinkSource] | None = None
    technical: FilterTechnical | None = None


class LinksLimitsObjects(RFBaseModel):
    """Objects in the limits object fields."""

    search_scope: SearchScope | None = None
    per_entity_type: int | None = None

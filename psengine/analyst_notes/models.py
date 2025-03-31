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

import logging
from datetime import datetime
from typing import Any, Optional, Union

from pydantic import Field, ValidationError, field_validator, model_validator

from ..common_models import IdNameType, IdNameTypeDescription, RFBaseModel


class DiamondModel(RFBaseModel):
    start: Optional[datetime] = None
    stop: Optional[datetime] = None
    malicious_infrastructure: Optional[list[IdNameTypeDescription]] = []
    capabilities: Optional[list[IdNameTypeDescription]] = []
    adversary: Optional[list[IdNameTypeDescription]] = []
    target: Optional[list[IdNameTypeDescription]] = []


class Query(RFBaseModel):
    title: str
    url: Optional[IdNameTypeDescription] = None


class Position(RFBaseModel):
    longitude: float
    latitude: float


class PositionEvent(RFBaseModel):
    start: datetime
    stop: datetime
    location: Optional[list[IdNameTypeDescription]] = []
    event_positions: Optional[list[Position]] = []


class CyberAttackEvent(RFBaseModel):
    start: datetime
    stop: datetime
    adversary: Optional[list[IdNameTypeDescription]] = []
    target: Optional[list[IdNameTypeDescription]] = []
    capabilities: list[IdNameTypeDescription] = []
    malicious_infrastructure: Optional[list[IdNameTypeDescription]] = []
    operation: Optional[list[IdNameTypeDescription]] = []


class ArmedConflictEvent(PositionEvent):
    attacker: Optional[list[IdNameTypeDescription]] = []
    target: Optional[list[IdNameTypeDescription]] = []


class ArmsPurchaseSaleEvent(RFBaseModel):
    start: datetime
    stop: datetime
    arms_seller: Optional[list[IdNameTypeDescription]] = []
    arms_purchaser: Optional[list[IdNameTypeDescription]] = []


class DiseaseOutbreakEvent(PositionEvent):
    disease: Optional[list[IdNameTypeDescription]] = []
    facility: Optional[list[IdNameTypeDescription]] = []


class EnvironmentalIssueEvent(PositionEvent):
    environmental_issue: list[str]


class ManMadeDisasterEvent(PositionEvent):
    facility: list[IdNameTypeDescription]
    manmade_disaster: Union[list[IdNameTypeDescription], list[str]]


class MilitaryManeuverEvent(PositionEvent):
    actors: Optional[list[IdNameTypeDescription]] = []


class NaturalDisasterEvent(PositionEvent):
    natural_disaster: list[IdNameTypeDescription]


class NuclearMaterialTransactionEvent(PositionEvent):
    material: list[str]
    location_origin: Optional[list[str]] = []
    location_destination: Optional[list[str]] = []


class PersonThreatEvent(RFBaseModel):
    start: datetime
    stop: datetime
    threatened: list[IdNameTypeDescription]
    actor: Optional[list[IdNameTypeDescription]] = []


class ProtestEvent(RFBaseModel):
    protest_target: Optional[list[IdNameTypeDescription]] = []


class MalwareAnalysisEvent(RFBaseModel):
    start: datetime
    stop: datetime
    malware: list[IdNameTypeDescription]
    attacker: Optional[list[IdNameTypeDescription]] = []
    malicious_infrastructure: Optional[list[IdNameTypeDescription]] = []
    ttp: Optional[list[IdNameTypeDescription]] = []
    target: Optional[list[IdNameTypeDescription]] = []
    exploit: Optional[list[IdNameTypeDescription]] = []
    hash_: Optional[list[IdNameTypeDescription]] = Field(alias='hash', default=[])


ATTRIBUTES_MAPPING = {
    'ArmedConflict': ArmedConflictEvent,
    'ArmsPurchaseSale': ArmsPurchaseSaleEvent,
    'Coup': PositionEvent,
    'CyberAttack': CyberAttackEvent,
    'DiseaseOutbreak': DiseaseOutbreakEvent,
    'Election': PositionEvent,
    'EnvironmentalIssue': EnvironmentalIssueEvent,
    'MalwareAnalysis': MalwareAnalysisEvent,
    'ManMadeDisaster': ManMadeDisasterEvent,
    'MilitaryManeuver': MilitaryManeuverEvent,
    'NaturalDisaster': NaturalDisasterEvent,
    'NuclearMaterialTransaction': NuclearMaterialTransactionEvent,
    'PersonThreat': PersonThreatEvent,
    'PoliticalEvent': PositionEvent,
    'PublicSafetyWarning': PositionEvent,
    'RFEVEArmedAssault': PositionEvent,
    'RFEVEProtest': ProtestEvent,
    'TerrorIncident': PositionEvent,
}


class NoteEvent(RFBaseModel):
    type_: Optional[str] = Field(alias='type', default=None)
    attributes: Optional[Any] = None

    @model_validator(mode='before')
    @classmethod
    def validate_attribute(cls, values):
        """Validate note event attributes."""
        if not values.get('type') or not values.get('attributes'):
            raise ValueError('Missing type or attributes from note event')

        type_ = values['type']
        validator = ATTRIBUTES_MAPPING.get(type_)
        if not validator:
            log = logging.getLogger(__name__)
            log.warning(f'Unknown validator for Analyst Note with event type {type_}')
            return {}

        try:
            attributes = validator.model_validate(values['attributes'])
        except ValidationError as e:
            log = logging.getLogger(__name__)
            log.warning(f'Failed to validate note event of type {type_}. Error {e}')
            log.warning(values)
            return {}

        return {'type': type_, 'attributes': attributes}


class Attributes(RFBaseModel):
    title: str
    text: str
    published: datetime
    attachment: Optional[str] = None
    events: Optional[list[NoteEvent]] = []
    validated_on: Optional[datetime] = None
    note_entities: Optional[list[IdNameTypeDescription]] = []
    context_entities: Optional[list[IdNameTypeDescription]] = []
    topic: Optional[Union[list[IdNameTypeDescription], IdNameTypeDescription]] = []
    labels: Optional[list[IdNameTypeDescription]] = []
    validation_urls: Optional[list[IdNameTypeDescription]] = []
    diamond_model: Optional[list[DiamondModel]] = []
    recommended_queries: Optional[list[Query]] = []
    header_image: Optional[IdNameType] = None

    @field_validator('events', mode='after')
    @classmethod
    def remove_empty_events(cls, values):
        """Remove empty events when ``NoteEvent`` skip the validation."""
        return [v for v in values if v.type_ and v.attributes]


class PreviewAttributesIn(RFBaseModel):
    title: str
    text: str
    note_entities: Optional[list[str]] = []
    context_entities: Optional[list[str]] = []
    topic: Union[list[str], str, None] = []
    labels: Optional[list[str]] = []
    validation_urls: Optional[list[str]] = []


class PreviewAttributesOut(RFBaseModel):
    title: str
    text: str
    note_entities: Optional[list[IdNameTypeDescription]] = []
    context_entities: Optional[list[IdNameTypeDescription]] = []
    topic: Optional[list[IdNameTypeDescription]] = []
    labels: Optional[list[IdNameTypeDescription]] = []
    validation_urls: Optional[list[IdNameTypeDescription]] = []


class RequestAttachment(RFBaseModel):
    content_type: str
    encoding: str
    content: str

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
from typing import Annotated, Any

from pydantic import BeforeValidator, Field, ValidationError, field_validator, model_validator

from ..common_models import IdNameType, IdNameTypeDescription, RFBaseModel
from ..helpers import Validators


class NoteEntity(IdNameTypeDescription):
    is_threat_actor: bool | None = None


class DiamondModel(RFBaseModel):
    start: datetime | None = None
    stop: datetime | None = None
    malicious_infrastructure: list[NoteEntity] | None = []
    capabilities: list[NoteEntity] | None = []
    adversary: list[NoteEntity] | None = []
    target: list[NoteEntity] | None = []


class Query(RFBaseModel):
    title: str
    url: NoteEntity | None = None


class Position(RFBaseModel):
    longitude: float
    latitude: float


class PositionEvent(RFBaseModel):
    start: datetime
    stop: datetime
    location: list[NoteEntity] | None = []
    event_positions: list[Position] | None = []


class CyberAttackEvent(RFBaseModel):
    start: datetime
    stop: datetime
    adversary: list[NoteEntity] | None = []
    target: list[NoteEntity] | None = []
    capabilities: list[NoteEntity] = []
    malicious_infrastructure: list[NoteEntity] | None = []
    operation: list[NoteEntity] | None = []


class ArmedConflictEvent(PositionEvent):
    attacker: list[NoteEntity] | None = []
    target: list[NoteEntity] | None = []


class ArmsPurchaseSaleEvent(RFBaseModel):
    start: datetime
    stop: datetime
    arms_seller: list[NoteEntity] | None = []
    arms_purchaser: list[NoteEntity] | None = []


class DiseaseOutbreakEvent(PositionEvent):
    disease: list[NoteEntity] | None = []
    facility: list[NoteEntity] | None = []


class EnvironmentalIssueEvent(PositionEvent):
    environmental_issue: list[str]


class ManMadeDisasterEvent(PositionEvent):
    facility: list[NoteEntity]
    manmade_disaster: list[NoteEntity] | list[str]


class MilitaryManeuverEvent(PositionEvent):
    actors: list[NoteEntity] | None = []


class NaturalDisasterEvent(PositionEvent):
    natural_disaster: list[NoteEntity]


class NuclearMaterialTransactionEvent(PositionEvent):
    material: list[str]
    location_origin: list[str] | None = []
    location_destination: list[str] | None = []


class PersonThreatEvent(RFBaseModel):
    start: datetime
    stop: datetime
    threatened: list[NoteEntity]
    actor: list[NoteEntity] | None = []


class ProtestEvent(RFBaseModel):
    protest_target: list[NoteEntity] | None = []


class MalwareAnalysisEvent(RFBaseModel):
    start: datetime
    stop: datetime
    malware: list[NoteEntity]
    attacker: list[NoteEntity] | None = []
    malicious_infrastructure: list[NoteEntity] | None = []
    ttp: list[NoteEntity] | None = []
    target: list[NoteEntity] | None = []
    exploit: list[NoteEntity] | None = []
    hash_: list[NoteEntity] | None = Field(alias='hash', default=[])


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
    type_: str | None = Field(alias='type', default=None)
    attributes: Any | None = None

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
    attachment: str | None = None
    events: list[NoteEvent] | None = []
    validated_on: datetime | None = None
    note_entities: list[NoteEntity] | None = []
    context_entities: list[NoteEntity] | None = []
    topic: list[NoteEntity] | NoteEntity | None = []
    labels: list[NoteEntity] | None = []
    validation_urls: list[NoteEntity] | None = []
    diamond_model: list[DiamondModel] | None = []
    recommended_queries: list[Query] | None = []
    header_image: IdNameType | None = None

    @field_validator('events', mode='after')
    @classmethod
    def remove_empty_events(cls, values):
        """Remove empty events when `NoteEvent` skip the validation."""
        return [v for v in values if v.type_ and v.attributes]


class PreviewAttributesIn(RFBaseModel):
    title: str
    text: str
    note_entities: list[str] | None = []
    context_entities: list[str] | None = []
    topic: Annotated[
        list[str] | str | None,
        BeforeValidator(Validators.convert_str_to_list),
    ] = []
    labels: list[str] | None = []
    validation_urls: list[str] | None = []


class PreviewAttributesOut(RFBaseModel):
    title: str
    text: str
    note_entities: list[NoteEntity] | None = []
    context_entities: list[NoteEntity] | None = []
    topic: list[NoteEntity] | None = []
    labels: list[NoteEntity] | None = []
    validation_urls: list[NoteEntity] | None = []


class RequestAttachment(RFBaseModel):
    content_type: str
    encoding: str
    content: str

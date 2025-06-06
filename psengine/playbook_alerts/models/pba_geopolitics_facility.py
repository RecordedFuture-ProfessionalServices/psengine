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
from typing import Optional

from pydantic import Field, HttpUrl

from ...common_models import RFBaseModel
from ..models.panel_status import PanelStatus


class Assessment(RFBaseModel):
    name: str
    criticality: str


class Event(RFBaseModel):
    text: str = None
    source: str = None
    url: HttpUrl = None
    assessments: list[Assessment] = []
    document_id: str = None
    time: datetime = None
    images: Optional[list[str]] = []


class GeopolPanelEvidence(RFBaseModel):
    assessments: list[Assessment] = []
    events: list[Event] = []


class LocationDistance(RFBaseModel):
    number: int = None
    unit: str = None
    facility_name: str = None


class LocationData(RFBaseModel):
    latitude: float = None
    longitude: float = None


class GeopolPanelOverview(RFBaseModel):
    event_type: str = None
    location_distance: LocationDistance = Field(default_factory=LocationDistance)
    event_time: datetime = None
    source: str = None
    ai_insights: str = None
    most_recent_event: Event = None
    facility_name: str = None
    facility_id: str = None
    location_data: LocationData = Field(default_factory=LocationData)
    event_document_id: str = None
    watchlist_comment: str = None


class GeopolPanelStatus(PanelStatus):
    risk_score: Optional[int] = None
    entity_criticality: Optional[str] = None


class GeopolEvent(RFBaseModel):
    translated_text: str = None
    translated_title: str = None
    source: str = None
    url: str = None
    document_id: str = None
    time: datetime = None
    assessments: list[Assessment] = []
    images: Optional[list[str]] = None


class GeopolPanelEvents(RFBaseModel):
    events: list[GeopolEvent] = []
    assessments: list[Assessment] = []

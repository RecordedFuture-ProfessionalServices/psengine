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

from pydantic import Field, HttpUrl

from ..common_models import IdName, IdNameType, IdNameTypeDescription, RFBaseModel


class AlertReview(RFBaseModel):
    assignee: str | None = None
    note: str | None = None
    status_in_portal: str
    status: str | None = None


class Organisation(RFBaseModel):
    organisation_id: str
    organisation_name: str


class OwnerOrganisationDetails(RFBaseModel):
    organisations: list[Organisation] | None = []
    enterprise_id: str | None = None
    enterprise_name: str | None = None
    owner_id: str | None = None
    owner_name: str | None = None


class AlertURL(RFBaseModel):
    api: HttpUrl
    portal: HttpUrl


class AlertAnalystNote(RFBaseModel):
    id_: str = Field(alias='id')
    url: AlertURL


class PortalURL(RFBaseModel):
    portal: HttpUrl


class AlertDeprecation(RFBaseModel):
    use_case_deprecation: str | None = None
    name: str
    id_: str = Field(alias='id')
    url: PortalURL


class AlertDocument(RFBaseModel):
    source: IdNameType | None = None
    title: str | None = None
    url: str | None = None
    authors: list[IdNameType]


class AlertAiInsight(RFBaseModel):
    comment: str | None = None
    text: str | None = None


class AlertLog(RFBaseModel):
    note_author: str | None = None
    note_date: datetime | None = None
    status_date: datetime | None = None
    triggered: datetime
    status_change_by: str | None = None


class AlertSummary(RFBaseModel):
    id_: str = Field(alias='id')
    title: str
    triggered: datetime
    url: HttpUrl
    type_: str = Field(alias='type')


class AlertCounts(RFBaseModel):
    returned: int
    total: int


class NotificationSettings(RFBaseModel):
    email_subscribers: list[IdName]
    mobile_subscribers: list[IdName] | None = None


class Evidence(RFBaseModel):
    timestamp: datetime
    mitigation_string: str
    criticality_label: str
    rule: str
    evidence_string: str
    criticality: int


class EntityCriticality(RFBaseModel):
    name: str
    score: int | None = None
    last_triggered: datetime
    triggered: datetime
    level: int


class ClassicAlertHit(RFBaseModel):
    """Validate data received from `/v3/alerts/hits`, `/v3/alert/search`, `/v3/alert/{id}`."""

    entities: list[IdNameTypeDescription]
    document: AlertDocument
    fragment: str | None = None
    id_: str = Field(alias='id')
    language: str | None = None
    primary_entity: IdNameTypeDescription | None = None
    analyst_note: AlertAnalystNote | None = None
    alert_id: str | None = None
    index: int | None = None


class EnrichedEntity(RFBaseModel):
    evidence: list[Evidence]
    references: list[ClassicAlertHit]
    criticality: EntityCriticality
    entity: IdNameType


class TriggeredBy(RFBaseModel):
    reference_id: str
    triggered_by_strings: list[str] | None = None

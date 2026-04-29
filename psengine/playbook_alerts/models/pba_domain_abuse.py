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

from pydantic import Field

from ...common_models import IdNameType, RFBaseModel
from ..models.panel_status import PanelStatus


class Context(RFBaseModel):
    context: str


class DomainAbusePanelStatus(PanelStatus):
    entity_criticality: str | None = None
    risk_score: int | None = None
    context_list: list[Context] | None = []
    targets: list[str] | None = []


class ResolvedRecord(RFBaseModel):
    entity: str | None = None
    record: str | None = None
    risk_score: int | None = None
    criticality: str | None = None
    record_type: str | None = None
    context_list: list[Context] | None = []


class Reregistration(RFBaseModel):
    registrar: str | None = None
    registrar_name: str | None = None
    expiration: datetime | None = None


class MentionedEntity(RFBaseModel):
    entity: IdNameType | None = Field(default_factory=IdNameType)
    reference: str
    fragment: str


class MentionedKeyword(RFBaseModel):
    entity: IdNameType | None = Field(default_factory=IdNameType)
    reference: str
    fragment: str
    keyword: str


class ScreenshotMention(RFBaseModel):
    url: str | None = None
    screenshot: str | None = None
    document: str | None = None
    analyzed: str | None = None
    mentioned_entities: list[MentionedEntity] | None = []
    mentioned_custom_keywords: list[MentionedKeyword] | None = []


class KeywordInDomain(RFBaseModel):
    word: str | None = None
    domain: str | None = None


class Keywords(RFBaseModel):
    security_keywords_in_domain_name: list[KeywordInDomain] | None = []
    payment_keywords_in_domain_name: list[KeywordInDomain] | None = []


class Screenshot(RFBaseModel):
    description: str
    image_id: str
    created: datetime
    tag: str | None = None


class DomainAbusePanelEvidenceSummary(RFBaseModel):
    explanation: str | None = None
    resolved_record_list: list[ResolvedRecord] | None = []
    screenshots: list[Screenshot] | None = []
    reregistration: Reregistration | None = Field(default_factory=Reregistration)
    screenshot_mentions: list[ScreenshotMention] | None = []
    keywords_in_domain_name: Keywords | None = Field(default_factory=Keywords)


class DomainAbusePanelEvidenceDns(RFBaseModel):
    ip_list: list[ResolvedRecord] | None = []
    mx_list: list[ResolvedRecord] | None = []
    ns_list: list[ResolvedRecord] | None = []


class ValueServer(RFBaseModel):
    status: str | None = None
    registrar_name: str | None = Field(alias='registrarName', default=None)
    private_registration: bool | None = Field(alias='privateRegistration', default=None)
    name_servers: list[str] | None = Field(alias='nameServers', default=[])
    contact_email: str | None = Field(alias='contactEmail', default=None)
    created_date: datetime | None = Field(alias='createdDate', default=None)
    updated_date: datetime | None = Field(alias='updatedDate', default=None)
    expires_date: datetime | None = Field(alias='expiresDate', default=None)


class ValueLocation(RFBaseModel):
    type_: str = Field(alias='type', default=None)
    telephone: str | None = None
    street1: str | None = None
    state: str | None = None
    postal_code: str | None = Field(alias='postalCode', default=None)
    organization: str | None = None
    name: str | None = None
    fax: str | None = None
    email: str | None = None
    country_code: str | None = Field(alias='countryCode', default=None)
    country: str | None = None
    city: str | None = None


class WhoisAttribute(RFBaseModel):
    provider: str
    entity: str
    attribute: str
    value: ValueServer | ValueLocation
    added: datetime = None
    removed: datetime | None = None


class DomainAbusePanelEvidenceWhois(RFBaseModel):
    body: list[WhoisAttribute] | None = []

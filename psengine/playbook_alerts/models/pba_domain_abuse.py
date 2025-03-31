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
from typing import Optional, Union

from pydantic import Field

from ...common_models import IdNameType, RFBaseModel
from ..models.panel_status import PanelStatus


class Context(RFBaseModel):
    context: str


class DomainAbusePanelStatus(PanelStatus):
    entity_criticality: Optional[str] = None
    risk_score: Optional[int] = None
    context_list: Optional[list[Context]] = []
    targets: Optional[list[str]] = []


class ResolvedRecord(RFBaseModel):
    entity: Optional[str] = None
    record: Optional[str] = None
    risk_score: Optional[int] = None
    criticality: Optional[str] = None
    record_type: Optional[str] = None
    context_list: Optional[list[Context]] = []


class Reregistration(RFBaseModel):
    registrar: Optional[str] = None
    registrar_name: Optional[str] = None
    expiration: Optional[datetime] = None


class MentionedEntity(RFBaseModel):
    entity: Optional[IdNameType] = Field(default_factory=IdNameType)
    reference: str
    fragment: str


class MentionedKeyword(RFBaseModel):
    entity: Optional[IdNameType] = Field(default_factory=IdNameType)
    reference: str
    fragment: str
    keyword: str


class ScreenshotMention(RFBaseModel):
    url: Optional[str] = None
    screenshot: Optional[str] = None
    document: Optional[str] = None
    analyzed: Optional[str] = None
    mentioned_entities: Optional[list[MentionedEntity]] = []
    mentioned_custom_keywords: Optional[list[MentionedKeyword]] = []


class KeywordInDomain(RFBaseModel):
    word: Optional[str] = None
    domain: Optional[str] = None


class Keywords(RFBaseModel):
    security_keywords_in_domain_name: Optional[list[KeywordInDomain]] = []
    payment_keywords_in_domain_name: Optional[list[KeywordInDomain]] = []


class Screenshot(RFBaseModel):
    description: str
    image_id: str
    created: datetime
    tag: Optional[str] = None


class DomainAbuseEvidenceSummary(RFBaseModel):
    explanation: Optional[str] = None
    resolved_record_list: Optional[list[ResolvedRecord]] = []
    screenshots: Optional[list[Screenshot]] = []
    reregistration: Optional[Reregistration] = Field(default_factory=Reregistration)
    screenshot_mentions: Optional[list[ScreenshotMention]] = []
    keywords_in_domain_name: Optional[Keywords] = Field(default_factory=Keywords)


class DomainAbuseEvidenceDns(RFBaseModel):
    ip_list: Optional[list[ResolvedRecord]] = []
    mx_list: Optional[list[ResolvedRecord]] = []
    ns_list: Optional[list[ResolvedRecord]] = []


class ValueServer(RFBaseModel):
    status: Optional[str] = None
    registrar_name: Optional[str] = Field(alias='registrarName', default=None)
    private_registration: Optional[bool] = Field(alias='privateRegistration', default=None)
    name_servers: Optional[list[str]] = Field(alias='nameServers', default=[])
    contact_email: Optional[str] = Field(alias='contactEmail', default=None)
    created_date: Optional[datetime] = Field(alias='createdDate', default=None)
    updated_date: Optional[datetime] = Field(alias='updatedDate', default=None)
    expires_date: Optional[datetime] = Field(alias='expiresDate', default=None)


class ValueLocation(RFBaseModel):
    type_: str = Field(alias='type', default=None)
    telephone: Optional[str] = None
    street1: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = Field(alias='postalCode', default=None)
    organization: Optional[str] = None
    name: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    country_code: Optional[str] = Field(alias='countryCode', default=None)
    country: Optional[str] = None
    city: Optional[str] = None


class WhoisAttribute(RFBaseModel):
    provider: str
    entity: str
    attribute: str
    value: Union[ValueServer, ValueLocation]
    added: datetime = None
    removed: Optional[datetime] = None


class DomainAbuseEvidenceWhois(RFBaseModel):
    body: Optional[list[WhoisAttribute]] = []

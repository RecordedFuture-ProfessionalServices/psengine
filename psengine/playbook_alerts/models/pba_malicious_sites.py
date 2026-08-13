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


class Assessment(RFBaseModel):
    name: str | None = None
    priority: str | None = None


class ResolvedRecord(RFBaseModel):
    entity: str | None = None
    risk_score: int | None = None
    criticality: str | None = None
    record_type: str | None = None
    assessments: list[Assessment] | None = []


class Reregistration(RFBaseModel):
    registrar: str | None = None
    registrar_name: str | None = None
    iana_id: int | None = None
    expiration: datetime | None = None


class SuggestedTakedown(RFBaseModel):
    has_phishing_verdict: bool | None = None
    has_high_interest_logo: bool | None = None
    has_login_form: bool | None = None
    screenshot: str | None = None


class Term(RFBaseModel):
    text: str | None = None
    position: str | None = None
    entity_type_id: str | None = None


class Asset(RFBaseModel):
    """Attacker asset. `type_` discriminates which of the optional fields are populated.

    Observed types: `client_domain`, `similar_domain_term`, `screenshot_ocr_keyword`,
    `code_repo_keyword`, `logotype`, `image_hash`, `company`, `organization`, `product`,
    `executive`.
    """

    type_: str | None = Field(alias='type', default=None)
    domain_id: str | None = None
    term: Term | None = None
    logotype_id: str | None = None
    hash_id: str | None = None
    company_id: str | None = None
    organization_id: str | None = None
    product_id: str | None = None
    executive_id: str | None = None


class Region(RFBaseModel):
    min_x: int | None = None
    min_y: int | None = None
    max_x: int | None = None
    max_y: int | None = None


class Logotype(RFBaseModel):
    logotype_id: str | None = None
    screenshot_id: str | None = None
    url: str | None = None
    screenshot_width: int | None = None
    screenshot_height: int | None = None
    region: Region | None = None
    is_high_interest: bool | None = None


class MaliciousDnsRecord(RFBaseModel):
    id_: str | None = Field(alias='id', default=None)
    assessments: list[Assessment] | None = []
    date: datetime | None = None


class Screenshot(RFBaseModel):
    description: str | None = None
    image_id: str | None = None
    created: datetime | None = None
    availability: str | None = None
    tag: str | None = None
    logotypes: list[Logotype] | None = []


class MentionedEntity(RFBaseModel):
    entity: IdNameType | None = Field(default_factory=IdNameType)
    reference: str | None = None
    fragment: str | None = None


class MentionedCustomKeyword(RFBaseModel):
    keyword: str | None = None
    reference: str | None = None
    fragment: str | None = None


class ScreenshotMention(RFBaseModel):
    url: str | None = None
    screenshot: str | None = None
    document: str | None = None
    analyzed: datetime | None = None
    mentioned_entities: list[MentionedEntity] | None = []
    mentioned_custom_keywords: list[MentionedCustomKeyword] | None = []


class BrandMention(RFBaseModel):
    source: str | None = None
    value: str | None = None


class Brand(RFBaseModel):
    brand: str | None = None
    mentions: list[BrandMention] | None = []


class PhishingVerdict(RFBaseModel):
    url: str | None = None
    source: str | None = None
    risk_rule_id: str | None = None
    risk_rule_description: str | None = None
    severity: str | None = None
    brands: list[Brand] | None = []
    last_seen: datetime | None = None
    ttps: list[str] | None = []


class Attacker(RFBaseModel):
    attacker: str | None = None
    targets: list[str] | None = []
    assets: list[Asset] | None = []
    cause: str | None = None
    malicious_dns_records: list[MaliciousDnsRecord] | None = []
    logotypes: list[Logotype] | None = []
    screenshots: list[Screenshot] | None = []
    reregistration: Reregistration | None = None
    screenshot_mentions: list[ScreenshotMention] | None = []
    suggested_takedown: SuggestedTakedown | None = None
    phishing_verdicts: list[PhishingVerdict] | None = []
    priority: str | None = None
    created_at: datetime | None = None
    assessments: list[Assessment] | None = []


class MaliciousSitesPanelStatus(PanelStatus):
    entity_criticality: str | None = None
    risk_score: int | None = None
    assessments: list[Assessment] | None = []
    attackers: list[str] | None = []


class MaliciousSitesPanelEvidenceSummary(RFBaseModel):
    explanation: str | None = None
    cause: str | None = None
    resolved_record_list: list[ResolvedRecord] | None = []
    reregistration: Reregistration | None = Field(default_factory=Reregistration)
    suggested_takedown: SuggestedTakedown | None = None
    attackers: list[Attacker] | None = []
    assessments: list[Assessment] | None = []


class MaliciousSitesPanelEvidenceDns(RFBaseModel):
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
    type_: str | None = Field(alias='type', default=None)
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
    provider: str | None = None
    entity: str | None = None
    attribute: str | None = None
    value: ValueServer | ValueLocation | None = None
    added: datetime | None = None
    removed: datetime | None = None


class MaliciousSitesPanelEvidenceWhois(RFBaseModel):
    body: list[WhoisAttribute] | None = []

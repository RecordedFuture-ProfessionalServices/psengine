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
from typing import Annotated, Literal

from pydantic import Field, HttpUrl

from ...common_models import RFBaseModel


class Assessment(RFBaseModel):
    name: str | None = None
    criticality: str | None = None


class Entity(RFBaseModel):
    entity_id: str
    name: str | None = None


class DarkWebPanelCachedContent(RFBaseModel):
    title: str
    downloaded: str
    original_url: str | None = None
    content: str


class DarkWebPanelTriage(RFBaseModel):
    rationale: str | None = None
    assessment: Assessment | None = Field(default_factory=Assessment)


class DarkWebPanelAnalysisReport(RFBaseModel):
    title: str | None = None
    source: Entity | None = None
    created: datetime | None = None
    content: str | None = None


class DarkWebMatchedAssets(RFBaseModel):
    type: str
    entity_id: str
    name: str | None = None


class DarkWebBrandRansomwareDetails(RFBaseModel):
    type: Literal['ransomware_extortion_site']
    ransomware_group: Entity
    source: Entity
    incident_url: str | None = None
    post_details: str | None = None
    post_date: datetime


class DarkWebTelegramDetails(RFBaseModel):
    type: Literal['telegram_mention']
    telegram_channel_title: str
    source: Entity
    message_url: HttpUrl
    post: str | None = None
    publish_date: datetime


class DarkWebForumMentionDetails(RFBaseModel):
    type: Literal['dark_web_forum_mention']
    source: Entity
    post_title: str
    post: str | None = None
    post_date: datetime
    post_url: str | None = None


class DarkWebMarketDetails(RFBaseModel):
    type: Literal['dark_web_market_mention']
    source: Entity
    market_url: str
    listing_title: str
    listing_content: str | None = None
    post_date: datetime
    post_url: HttpUrl | None = None


class DarkWebPanelEvidenceSummary(RFBaseModel):
    matched_assets: list[DarkWebMatchedAssets]
    assessments: list[Assessment]
    screenshot_ids: list[str]
    details: Annotated[
        DarkWebBrandRansomwareDetails
        | DarkWebTelegramDetails
        | DarkWebForumMentionDetails
        | DarkWebMarketDetails,
        Field(discriminator='type'),
    ]

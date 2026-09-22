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

from ...common_models import RFBaseModel


class SocialMediaMatchedAssets(RFBaseModel):
    type: str
    entity_id: str
    name: str | None = None


class Assessment(RFBaseModel):
    name: str
    criticality: str


class SocialMediaImpersonationPanelEvidenceSummary(RFBaseModel):
    matched_assets: list[SocialMediaMatchedAssets]
    assessments: list[Assessment]
    profile_url_id: str
    platform_id: str
    user_name: str | None = Field(alias='username', default=None)
    user_handel: str | None = None
    description: str | None = None
    created_date: datetime | None = None
    number_of_posts: int | None = None
    number_of_followers: int | None = None
    private_profile: bool | None = None

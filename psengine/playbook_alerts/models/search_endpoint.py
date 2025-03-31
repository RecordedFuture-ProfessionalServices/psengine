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

import contextlib
from datetime import datetime
from typing import Optional

from pydantic import Field, model_validator

from ...common_models import RFBaseModel
from ..models.panel_status import OwnerOrganisationDetails


class DatetimeRange(RFBaseModel):
    from_: Optional[datetime] = Field(alias='from', default=None)
    until: Optional[datetime] = None


class SearchStatus(RFBaseModel):
    status_code: str
    status_message: str


class SearchData(RFBaseModel):
    playbook_alert_id: str
    status: str
    priority: str
    reopen: Optional[str] = None
    created: datetime
    updated: datetime
    category: str
    title: str
    assignee_name: Optional[str] = None
    assignee_id: Optional[str] = None
    owner_organisation_details: Optional[OwnerOrganisationDetails] = None
    actions_taken: list[str]

    @model_validator(mode='before')
    @classmethod
    def rm_deprecated(cls, data):
        """Remove deprecated fields."""
        for key in ('owner_id', 'owner_name', 'organisation_id', 'organisation_name'):
            with contextlib.suppress(KeyError):
                del data[key]
        return data


class SearchCounts(RFBaseModel):
    returned: int
    total: int


class SearchResponse(RFBaseModel):
    """Model for payload received by /search endpoint."""

    status: SearchStatus
    data: list[SearchData]
    counts: SearchCounts

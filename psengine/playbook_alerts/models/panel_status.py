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
from typing import Optional, Union

from pydantic import model_validator

from ...common_models import RFBaseModel
from ..models.common_models import ResolvedEntity


class Organisation(RFBaseModel):
    organisation_id: str
    organisation_name: str


class OwnerOrganisationDetails(RFBaseModel):
    organisations: list[Organisation]
    enterprise_id: str
    enterprise_name: str


class PanelStatus(RFBaseModel):
    status: str
    priority: str
    reopen: Optional[str] = None
    assignee_name: Optional[str] = None
    assignee_id: Optional[str] = None
    created: datetime
    updated: datetime
    case_rule_id: Optional[str] = None
    case_rule_label: Optional[str] = None
    creator_name: Optional[str] = None
    creator_id: Optional[str] = None
    owner_organisation_details: Optional[OwnerOrganisationDetails] = None
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    actions_taken: list[str]
    targets: Optional[list[Union[ResolvedEntity, str]]] = []

    @model_validator(mode='before')
    @classmethod
    def rm_deprecated(cls, data):
        """Remove deprecated fields."""
        for key in ('owner_id', 'owner_name', 'organisation_id', 'organisation_name'):
            with contextlib.suppress(KeyError):
                del data[key]
        return data


class PanelAction(RFBaseModel):
    action: Optional[str] = None
    updated: Optional[datetime] = None
    assignee_name: Optional[str] = None
    assignee_id: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    link: Optional[str] = None

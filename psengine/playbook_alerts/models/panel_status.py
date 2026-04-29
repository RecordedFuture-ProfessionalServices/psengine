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

from pydantic import model_validator

from ...common_models import RFBaseModel
from ..models.common_models import ResolvedEntity
from .common_models import AlertRule


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
    reopen: str | None = None
    assignee_name: str | None = None
    assignee_id: str | None = None
    created: datetime
    updated: datetime
    case_rule_id: str | None = None
    case_rule_label: str | None = None
    alert_rule: AlertRule
    creator_name: str | None = None
    creator_id: str | None = None
    owner_organisation_details: OwnerOrganisationDetails | None = None
    entity_id: str | None = None
    entity_name: str | None = None
    actions_taken: list[str]
    targets: list[ResolvedEntity | str] | None = []

    @model_validator(mode='before')
    @classmethod
    def rm_deprecated(cls, data):
        """Remove deprecated fields."""
        for key in ('owner_id', 'owner_name', 'organisation_id', 'organisation_name'):
            with contextlib.suppress(KeyError):
                del data[key]
        return data


class PanelAction(RFBaseModel):
    action: str | None = None
    updated: datetime | None = None
    assignee_name: str | None = None
    assignee_id: str | None = None
    status: str | None = None
    description: str | None = None
    link: str | None = None

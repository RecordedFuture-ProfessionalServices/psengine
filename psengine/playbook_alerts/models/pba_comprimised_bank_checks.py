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
from .common_models import AlertRule
from ..models.panel_status import PanelStatus


class Assessments(RFBaseModel):
    name: str
    criticality: str


class CompromisedBankCheckPanelStatus(PanelStatus):
    alert_rule: AlertRule | None = None


class CompromisedBankCheckPanelEvidenceSummary(RFBaseModel):
    assessments: list[Assessments] | None = []
    check_id: str | None = None
    collected_date: datetime | None = None
    posted_date: datetime | None = None
    multiple_checks: bool | None = None
    previously_seen: bool | None = None
    seen_ids: list[str] | None = []
    seen_source_ids: list[str] | None = []
    seen_dates: list[datetime] | None = []
    source_id: str | None = None
    source_type: str | None = None
    post_url: str | None = None
    actor: str | None = None
    actor_id: str | None = None
    actor_url: str | None = None
    check_date: datetime | None = None
    expired: bool | None = None
    expired_at: datetime | None = None
    amount: float | None = None
    check_number: str | None = None
    fraction_number: str | None = None
    bank: str | None
    bank_routing_number: str | None = None
    identity_1: str | None = Field(alias='identity1', default=None)
    address_1: str | None = Field(alias='address1', default=None)
    city_1: str | None = Field(alias='city1', default=None)
    state_1: str | None = Field(alias='state1', default=None)
    zip_1: str | None = Field(alias='zip1', default=None)
    identity_2: str | None = Field(alias='identity2', default=None)
    address_2: str | None = Field(alias='address2', default=None)
    city_2: str | None = Field(alias='city2', default=None)
    state_2: str | None = Field(alias='state2', default=None)
    zip_2: str | None = Field(alias='zip2', default=None)
    info: str | None = None

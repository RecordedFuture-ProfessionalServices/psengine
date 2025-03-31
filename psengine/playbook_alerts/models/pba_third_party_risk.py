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
from typing import Optional

from pydantic import Field, model_validator

from ...common_models import RFBaseModel
from ..models.common_models import ResolvedEntity
from ..models.panel_status import PanelStatus


class TPRPanelStatus(PanelStatus):
    risk_score: Optional[int] = None
    entity_criticality: Optional[str] = None
    targets: Optional[list[ResolvedEntity]] = []


class InsiktNote(RFBaseModel):
    id_: str = Field(alias='id')
    title: Optional[str] = None
    published: Optional[datetime] = None
    topic: Optional[str] = None
    fragment: Optional[str] = None


class ObservedNetworkTraffic(RFBaseModel):
    recent_timestamp: datetime
    malware_family: Optional[str] = None
    client_ip_address: Optional[str] = None
    malware_ip_address: Optional[str] = None


class SummaryString(RFBaseModel):
    data: list
    summary: str


class Reference(RFBaseModel):
    title: Optional[str] = None
    fragment: Optional[str] = None
    published: datetime
    document_url: Optional[str] = None
    source: Optional[str] = None


class IpRule(RFBaseModel):
    name: str
    criticality: int
    number_of_ip_addresses: int


class CyberTrend(RFBaseModel):
    date: datetime
    criticality: int
    number_of_references: int


class Evidence(RFBaseModel):
    summary: str
    type_: str = Field(alias='type')
    data: list

    @model_validator(mode='after')
    @classmethod
    def check_data_type(cls, evidence: 'Evidence'):
        """Check if evidence type is supported and validate it."""
        type_mapping = {
            'ip_rule': IpRule,
            'cyber_trend': CyberTrend,
            'insikt_note': InsiktNote,
            'reference': Reference,
            'hosts_communication': ObservedNetworkTraffic,
            'summary_string': SummaryString,
        }
        evidence.data = [
            model.model_validate(obj)
            for obj in evidence.data
            if (model := type_mapping.get(evidence.type_))
        ]
        return evidence


class Assessment(RFBaseModel):
    risk_rule: str
    level: int
    added: datetime
    evidence: Evidence


class TPREvidencePanel(RFBaseModel):
    assessments: Optional[list[Assessment]] = []

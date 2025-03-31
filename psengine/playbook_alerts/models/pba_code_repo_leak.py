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

from pydantic import Field, HttpUrl

from ...common_models import RFBaseModel
from ..models.common_models import ResolvedEntity
from ..models.panel_status import PanelStatus


class CodeRepoPanelStatus(PanelStatus):
    risk_score: Optional[int] = None
    entity_criticality: Optional[str] = None
    targets: Optional[list[ResolvedEntity]] = []


class Repository(RFBaseModel):
    id_: str = Field(alias='id', default=None)
    name: Optional[str] = None
    owner: Optional[ResolvedEntity] = None


class Assessment(RFBaseModel):
    id_: str = Field(alias='id')
    title: Optional[str] = None
    value: Optional[str] = None


class Evidence(RFBaseModel):
    assessments: list[Assessment]
    targets: list[ResolvedEntity]
    url: Optional[HttpUrl] = None
    content: str
    published: datetime


class CodeRepoEvidencePanel(RFBaseModel):
    repository: Optional[Repository] = Field(default_factory=Repository)
    evidence: Optional[list[Evidence]] = []

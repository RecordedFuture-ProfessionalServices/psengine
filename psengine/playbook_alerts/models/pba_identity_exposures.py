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

from pydantic import Field, IPvAnyAddress

from ...common_models import RFBaseModel
from ..models.common_models import ResolvedEntity
from ..models.panel_status import PanelStatus


class Assessment(RFBaseModel):
    name: str
    criticality: str


class PasswordDetails(RFBaseModel):
    properties: Optional[list[str]] = []
    rank: Optional[list[str]] = []
    clear_text_value: Optional[str] = None
    clear_text_hint: Optional[str] = None


class PasswordHash(RFBaseModel):
    algorithm: str
    hash_: Optional[str] = Field(alias='hash', default=None)
    hash_prefix: Optional[str] = None


class ExposedSecret(RFBaseModel):
    type_: str = Field(alias='type', default=None)
    effectively_clear: Optional[bool] = None
    hashes: Optional[list[PasswordHash]] = []
    details: Optional[PasswordDetails] = Field(default_factory=PasswordDetails)


class Dump(RFBaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class MalwareFamily(RFBaseModel):
    id_: str = Field(alias='id', default=None)
    name: Optional[str] = None


class Infrastructure(RFBaseModel):
    ip: Optional[IPvAnyAddress] = None


class Technology(RFBaseModel):
    name: str
    id_: Optional[str] = Field(alias='id', default=None)
    category: Optional[str] = None


class CompromisedHost(RFBaseModel):
    exfiltration_date: Optional[datetime] = None
    os: Optional[str] = None
    os_username: Optional[str] = None
    malware_file: Optional[str] = None
    timezone: Optional[str] = None
    computer_name: Optional[str] = None
    uac: Optional[str] = None
    antivirus: Optional[list[str]] = []


class IdentityPanelStatus(PanelStatus):
    targets: Optional[list[ResolvedEntity]] = []


class IdentityEvidencePanel(RFBaseModel):
    assessments: Optional[list[Assessment]] = []
    subject: Optional[str] = None
    exposed_secret: Optional[ExposedSecret] = Field(default_factory=ExposedSecret)
    dump: Optional[Dump] = Field(default_factory=Dump)
    authorization_url: Optional[str] = None
    compromised_host: Optional[CompromisedHost] = Field(default_factory=CompromisedHost)
    malware_family: Optional[MalwareFamily] = Field(default_factory=MalwareFamily)
    infrastructure: Optional[Infrastructure] = Field(default_factory=Infrastructure)
    technologies: Optional[list[Technology]] = []

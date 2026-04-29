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

from pydantic import Field, IPvAnyAddress

from ...common_models import RFBaseModel
from ..models.common_models import ResolvedEntity
from ..models.panel_status import PanelStatus


class Assessment(RFBaseModel):
    name: str
    criticality: str


class PasswordDetails(RFBaseModel):
    properties: list[str] | None = []
    rank: list[str] | None = []
    clear_text_value: str | None = None
    clear_text_hint: str | None = None


class PasswordHash(RFBaseModel):
    algorithm: str
    hash_: str | None = Field(alias='hash', default=None)
    hash_prefix: str | None = None


class ExposedSecret(RFBaseModel):
    type_: str = Field(alias='type', default=None)
    effectively_clear: bool | None = None
    hashes: list[PasswordHash] | None = []
    details: PasswordDetails | None = Field(default_factory=PasswordDetails)


class Dump(RFBaseModel):
    name: str | None = None
    description: str | None = None


class MalwareFamily(RFBaseModel):
    id_: str = Field(alias='id', default=None)
    name: str | None = None


class Infrastructure(RFBaseModel):
    ip: IPvAnyAddress | None = None


class Technology(RFBaseModel):
    name: str
    id_: str | None = Field(alias='id', default=None)
    category: str | None = None


class CompromisedHost(RFBaseModel):
    exfiltration_date: datetime | None = None
    os: str | None = None
    os_username: str | None = None
    malware_file: str | None = None
    timezone: str | None = None
    computer_name: str | None = None
    uac: str | None = None
    antivirus: list[str] | None = []


class IdentityPanelStatus(PanelStatus):
    targets: list[ResolvedEntity] | None = []


class IdentityPanelEvidence(RFBaseModel):
    assessments: list[Assessment] | None = []
    subject: str | None = None
    exposed_secret: ExposedSecret | None = Field(default_factory=ExposedSecret)
    dump: Dump | None = Field(default_factory=Dump)
    authorization_url: str | None = None
    compromised_host: CompromisedHost | None = Field(default_factory=CompromisedHost)
    malware_family: MalwareFamily | None = Field(default_factory=MalwareFamily)
    infrastructure: Infrastructure | None = Field(default_factory=Infrastructure)
    technologies: list[Technology] | None = []

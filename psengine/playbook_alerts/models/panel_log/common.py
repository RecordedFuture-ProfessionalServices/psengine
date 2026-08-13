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

from ....common_models import IdOptionalNameType, RFBaseModel


class ChangeType(RFBaseModel):
    type_: str = Field(alias='type')


class Assignee(RFBaseModel):
    id_: str = Field(alias='id')
    name: str


class DnsRecord(RFBaseModel):
    type_: str | None = Field(alias='type', default=None)
    entity: IdOptionalNameType | None = None


class WhoisRecord(RFBaseModel):
    status: str | None = None
    registrar_name: str | None = None
    private_registration: bool | None = None
    name_servers: list[str] | None = []
    contact_email: str | None = None
    created: datetime | None = None


class WhoisContactRecord(ChangeType):
    telephone: str | None = None
    street1: str | None = None
    state: str | None = None
    postal_code: str | None = None
    organization: str | None = None
    name: str | None = None
    fax: str | None = None
    email: str | None = None
    country_code: str | None = None
    country: str | None = None
    city: str | None = None
    created: datetime | None = None


class ReregistrationRecord(RFBaseModel):
    registrar: str | None = None
    registrar_name: str | None = None
    iana_id: int | str | None = None
    expiration: datetime | None = None


class MaliciousAssessment(RFBaseModel):
    id_: str = Field(alias='id')
    level: int
    title: str | None = None


class MaliciousDnsRecord(RFBaseModel):
    id_: str | None = Field(alias='id', default=None)
    assessments: list[MaliciousAssessment]


class Source(RFBaseModel):
    id_: str = Field(alias='id')
    name: str


class UrlAssessment(MaliciousAssessment):
    source: Source


class MaliciousUrlRecord(RFBaseModel):
    url: str | None = None
    assessments: list[UrlAssessment]


class _DnsChangeShape(ChangeType):
    domain: str
    removed: list[DnsRecord]
    added: list[DnsRecord]


class _MaliciousDnsChangeShape(ChangeType):
    domain: str
    removed: list[MaliciousDnsRecord] | None = []
    added: list[MaliciousDnsRecord] | None = []


class _MaliciousUrlChangeShape(ChangeType):
    domain: str
    removed: list[MaliciousUrlRecord] | None = []
    added: list[MaliciousUrlRecord] | None = []


class _UrlImageChange(ChangeType):
    url: str | None = None
    image: str | None = None

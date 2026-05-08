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

from typing import Optional

from pydantic import AnyUrl, Field, IPvAnyAddress

from ...common_models import ClearTextPassword, RFBaseModel
from .common_models import (
    PasswordHash,
    Technology,
)


class AuthorizationService(RFBaseModel):
    url: AnyUrl
    domain: str
    fqdn: str
    technology: list[Technology]
    protocols: list[str]


class ExposedSecretDetails(RFBaseModel):
    properties: list[str]
    rank: Optional[str] = None
    clear_text_value: Optional[ClearTextPassword] = None
    clear_text_hint: Optional[str] = None


class SecretDetails(RFBaseModel):
    type_: str = Field(alias='type')
    hashes: list[PasswordHash]
    details: ExposedSecretDetails
    effectively_clear: bool


class IdentityDetails(RFBaseModel):
    subjects: list[str]


class IPRange(RFBaseModel):
    gte: Optional[IPvAnyAddress] = None
    gt: Optional[IPvAnyAddress] = None
    lte: Optional[IPvAnyAddress] = None
    lt: Optional[IPvAnyAddress] = None

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
from typing import Annotated

from pydantic import BeforeValidator, Field

from ...common_models import RFBaseModel
from ...helpers import Validators
from .common_models import (
    DetectionType,
    PasswordHash,
    Technology,
)


class DetectionsCreated(RFBaseModel):
    gte: Annotated[datetime | None, BeforeValidator(Validators.convert_relative_time)] = None
    lt: Annotated[datetime | None, BeforeValidator(Validators.convert_relative_time)] = None


class AuthorizationService(RFBaseModel):
    url: str | None = None
    domain: str | None = None
    fqdn: str | None = None
    technology: list[Technology] | None = None
    protocols: list[str] | None = None


class Password(RFBaseModel):
    type_: str | None = Field(default=None, alias='type')
    hashes: list[PasswordHash] | None = None
    properties: list[str] | None = None
    cleartext_hint: str | None = None
    cleartext: str | None = None


class DetectionsFilterIn(RFBaseModel):
    novel_only: bool | None = None
    cookies: str | None = None
    domains: Annotated[list[str] | None, BeforeValidator(Validators.convert_str_to_list)] = []
    detection_type: DetectionType | None = None
    created: DetectionsCreated | None = None

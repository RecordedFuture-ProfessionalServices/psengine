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
from typing import Annotated, Optional

from pydantic import BeforeValidator, Field

from ...common_models import RFBaseModel
from ...helpers import Validators
from .common_models import (
    DetectionType,
    PasswordHash,
    Technology,
)


class DetectionsCreated(RFBaseModel):
    gte: Annotated[Optional[datetime], BeforeValidator(Validators.convert_relative_time)] = None
    lt: Annotated[Optional[datetime], BeforeValidator(Validators.convert_relative_time)] = None


class AuthorizationService(RFBaseModel):
    url: Optional[str] = None
    domain: Optional[str] = None
    fqdn: Optional[str] = None
    technology: Optional[list[Technology]] = None
    protocols: Optional[list[str]] = None


class Password(RFBaseModel):
    type_: Optional[str] = Field(default=None, alias='type')
    hashes: Optional[list[PasswordHash]] = None
    properties: Optional[list[str]] = None
    cleartext_hint: Optional[str] = None
    cleartext: Optional[str] = None


class DetectionsFilterIn(RFBaseModel):
    novel_only: Optional[bool] = None
    cookies: Optional[str] = None
    domains: Annotated[Optional[list[str]], BeforeValidator(Validators.convert_str_to_list)] = []
    detection_type: Optional[DetectionType] = None
    created: Optional[DetectionsCreated] = None

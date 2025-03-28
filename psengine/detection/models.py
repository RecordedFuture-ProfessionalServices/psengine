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

from pydantic import Field

from ..common_models import DetectionRuleType, RFBaseModel


class Entity(RFBaseModel):
    id_: str = Field(alias='id', default=None)
    name: Optional[str] = None
    type_: str = Field(alias='type', default=None)

    display_name: Optional[str] = None


class RuleContext(RFBaseModel):
    entities: list[Entity]
    content: str
    file_name: Optional[str] = None


class TimeRange(RFBaseModel):
    after: Optional[datetime] = None
    before: Optional[datetime] = None


class SearchFilter(RFBaseModel):
    types: Optional[list[DetectionRuleType]] = None
    entities: Optional[list[str]] = None
    created: Optional[TimeRange] = None
    updated: Optional[TimeRange] = None
    doc_id: Optional[str] = None
    title: Optional[str] = None

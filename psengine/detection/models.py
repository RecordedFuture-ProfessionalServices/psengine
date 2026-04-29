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

from ..common_models import DetectionRuleType, RFBaseModel
from ..helpers import Validators


class Entity(RFBaseModel):
    id_: str = Field(alias='id', default=None)
    name: str | None = None
    type_: str = Field(alias='type', default=None)

    display_name: str | None = None


class RuleContext(RFBaseModel):
    entities: list[Entity]
    content: str
    file_name: str | None = None


class TimeRange(RFBaseModel):
    after: Annotated[datetime | None, BeforeValidator(Validators.convert_relative_time)] = None
    before: Annotated[datetime | None, BeforeValidator(Validators.convert_relative_time)] = None


class SearchFilter(RFBaseModel):
    types: Annotated[
        list[DetectionRuleType] | None, BeforeValidator(Validators.convert_str_to_list)
    ] = None
    entities: list[str] | None = None
    created: TimeRange | None = None
    updated: TimeRange | None = None
    doc_id: str | None = None
    title: str | None = None

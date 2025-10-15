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

from ..common_models import RFBaseModel
from ..helpers.helpers import Validators


class RiskScoreHistory(RFBaseModel):
    score: int
    added: Optional[datetime] = None
    removed: Optional[datetime] = None


class RiskLevelHistory(RFBaseModel):
    criticality: int
    added: Optional[datetime] = None
    removed: Optional[datetime] = None


class RiskRuleHistory(RFBaseModel):
    risk_id: Optional[str] = None
    risk_name: str
    criticality: int
    evidence: str
    added: Optional[datetime] = None
    removed: Optional[datetime] = None


class Entity(RFBaseModel):
    id: str
    provided_id: Optional[str] = None
    type: str
    name: str


class RiskHistory(RFBaseModel):
    entity: Optional[Entity] = None
    scores: Optional[list[RiskScoreHistory]] = None
    levels: Optional[list[RiskLevelHistory]] = None
    risk_rules: Optional[list[RiskRuleHistory]] = None

    def __str__(self) -> str:
        return 'Entity {}: Risk Score Changes: {}, Risk Rule Changes: {}'.format(  # noqa: UP032
            self.entity.name, len(self.scores), len(self.risk_rules)
        )


class RiskHistoryIn(RFBaseModel):
    entities: Annotated[list[str], BeforeValidator(Validators.convert_str_to_list)]
    from_: Annotated[Optional[datetime], BeforeValidator(Validators.convert_relative_time)] = Field(
        None, alias='from'
    )
    to: Annotated[Optional[datetime], BeforeValidator(Validators.convert_relative_time)] = None

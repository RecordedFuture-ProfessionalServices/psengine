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

import json
from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator

from ..common_models import RFBaseModel


class EvidenceDetail(RFBaseModel):
    name: str = Field(alias='Name')
    evidence_string: str = Field(alias='EvidenceString')
    criticality_label: str = Field(alias='CriticalityLabel')
    mitigation_string: str = Field(alias='MitigationString')
    sightings_count: float = Field(alias='SightingsCount')
    criticality: int = Field(alias='Criticality')
    rule: str = Field(alias='Rule')
    source_count: Optional[int] = Field(alias='SourceCount', default=None)
    sources: list[str] = Field(alias='Sources')
    timestamp: datetime = Field(alias='Timestamp')

    def __str__(self):
        return f'Evidence Details: {self.name}, {self.timestamp}'

    def __repr__(self):
        return f'Evidence Details: {self.name}, {self.timestamp}'


class DefaultRiskList(RFBaseModel):
    ioc: str = Field(validation_alias='Name')
    algorithm: Optional[str] = Field(validation_alias='Algorithm', default=None)
    risk_score: int = Field(validation_alias='Risk')
    risk_string: str = Field(validation_alias='RiskString')
    evidence_details: list[EvidenceDetail] = Field(validation_alias='EvidenceDetails')

    @field_validator('evidence_details', mode='before')
    @classmethod
    def evidence_to_dict(cls, v):
        """Dump the EvidenceDetails block to dict, if possible."""
        if isinstance(v, str):
            try:
                return json.loads(v)['EvidenceDetails']
            except (json.JSONDecodeError, KeyError) as err:
                raise ValueError(
                    'Evidence details cannot be converted to json or key not found'
                ) from err

    def __str__(self):
        return f'{self.ioc}: {self.risk_score} {self.evidence_details}'

    def __repr__(self):
        return f'{self.ioc}: {self.risk_score} {self.evidence_details}'

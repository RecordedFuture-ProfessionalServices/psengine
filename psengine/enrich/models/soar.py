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

from pydantic import Field, model_validator

from ...common_models import RFBaseModel


class ScoreCount(RFBaseModel):
    count: Optional[int] = None
    max_count: int = Field(alias='maxCount')


class ScoreRule(RFBaseModel):
    score: int
    rule: ScoreCount


class Public(ScoreRule):
    summary: list
    most_critical_rule: str = Field(alias='mostCriticalRule')


class Evidence(RFBaseModel):
    count: int
    timestamp: datetime
    description: str
    rule: str
    # TODO - temp fix until API team fixes/confirms behaviour of sightings
    sightings: int = 0
    mitigation: str
    level: int
    type_: str = Field(alias='type')


class RiskRule(ScoreCount):
    score: Optional[int] = None
    summary: list
    most_critical: str = Field(alias='mostCritical')
    evidence: Optional[list[Evidence]] = None

    @model_validator(mode='before')
    @classmethod
    def evidence_transform(cls, data: dict) -> dict:
        """Transforms the evidence field into a list of dicts, each with a 'type' key.

        From:

        .. code-block::

            "evidence": {
                "recentValidatedCnc": {
                    "count": 1,
                    "timestamp": "2024-03-25T07:18:35.000Z",
                    "description": "xyz",
                    "rule": "Validated C&C Server",
                    "sightings": 41,
                    "mitigation": "",
                    "level": 4
                },
                "recentSuspectedCnc": {
                    "count": 1,
                    "timestamp": "2024-03-24T16:05:31.634Z",
                    "description": "xyz",
                    "rule": "Recent Suspected C&C Server",
                    "sightings": 5,
                    "mitigation": "",
                    "level": 2
                }
            }

        To:

        .. code-block::

            "evidence": [
                {
                    "count": 1,
                    "timestamp": "2023-12-11T19:25:25.892000Z",
                    "description": "xyz",
                    "sightings": 1,
                    "mitigation": "",
                    "level": 3,
                    "type": "recentReportedCnc"
                },
                {
                    "count": 2,
                    "timestamp": "2023-12-25T22:09:55.398000Z",
                    "description": "xyz",
                    "rule": "Historical Suspected C&C Server",
                    "sightings": 2,
                    "mitigation": "",
                    "level": 1,
                    "type": "suspectedCnc"
                }
            ]

        Args:
            data (dict): The data to be validated.

        Returns:
            dict: The transformed data.
        """
        if 'evidence' not in data:
            return data

        evidence = data.pop('evidence')

        data['evidence'] = [{**ev, 'type': key} for key, ev in evidence.items()]

        return data


class Context(RFBaseModel):
    phishing: Optional[ScoreRule] = None
    public: Optional[Public] = None
    c2: Optional[ScoreRule] = None
    malware: Optional[ScoreRule] = None


class Risk(RFBaseModel):
    score: int
    level: int
    context: Context
    rule: RiskRule

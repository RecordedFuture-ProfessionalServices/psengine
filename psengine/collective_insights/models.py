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

from enum import Enum
from typing import Optional

from pydantic import Field, model_validator

from ..common_models import DetectionRuleType, IOCType, RFBaseModel


class DetectionType(Enum):
    detection_rule = 'detection_rule'
    correlation = 'correlation'
    playbook = 'playbook'
    sandbox = 'sandbox'


class SummaryProcessed(RFBaseModel):
    ip: int
    domain: int
    hash_: int = Field(alias='hash')
    vulnerability: int
    url: int


class ResponseSummary(RFBaseModel):
    processed: SummaryProcessed


class RequestOptions(RFBaseModel):
    debug: bool = False
    summary: bool = True


class RequestIOC(RFBaseModel):
    type_: IOCType = Field(alias='type')
    value: str
    source_type: Optional[str] = None
    field: Optional[str] = None


class RequestDetection(RFBaseModel):
    id_: Optional[str] = Field(alias='id', default=None)
    name: Optional[str] = None
    type_: DetectionType = Field(alias='type')
    sub_type: Optional[DetectionRuleType] = None

    @model_validator(mode='before')
    @classmethod
    def validate_detection_rule(cls, data):
        """Validate detection rule scenario.

        - id must be present.
        - sub_type must be present and should be one of DetectionRuleType
        """
        try:
            detection_type = data['type']
        except KeyError as e:
            raise ValueError('type field is mandatory') from e

        if detection_type == 'detection_rule' and not (data.get('id') and data.get('sub_type')):
            raise ValueError(f'With {detection_type} the id and sub_type fields are mandatory')

        return data


class SubmissionResult(RFBaseModel):
    status: str
    debug: bool
    summary: Optional[ResponseSummary] = None

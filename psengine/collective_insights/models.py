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
from enum import Enum
from functools import total_ordering
from typing import Annotated, Literal

from pydantic import AfterValidator, BeforeValidator, Field, model_validator

from ..common_models import DetectionRuleType, IOCType, RFBaseModel
from ..constants import TIMESTAMP_STR
from ..helpers.helpers import Validators


def _to_list_or_presence(value):
    """Coerce a scalar to a list; pass `present`/`absent` sentinels and `None` through."""
    if value is None or value in ('present', 'absent'):
        return value
    return Validators.convert_str_to_list(value)


def _prune_none(data):
    """Recursively drop keys with `None` or empty-container values from a dict."""
    if not isinstance(data, dict):
        return data
    pruned = {}
    for key, value in data.items():
        cleaned = _prune_none(value)
        if cleaned is None:
            continue
        if isinstance(cleaned, (dict, list)) and not cleaned:
            continue
        pruned[key] = cleaned
    return pruned


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
    source_type: str | None = None
    field: str | None = None


class RequestDetection(RFBaseModel):
    id_: str | None = Field(alias='id', default=None)
    name: str | None = None
    type_: DetectionType = Field(alias='type')
    sub_type: DetectionRuleType | None = None

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
    summary: ResponseSummary | None = None


class SearchDetectionType(Enum):
    correlation = 'correlation'
    playbook = 'playbook'
    detection_rule = 'detection_rule'
    sandbox = 'sandbox'
    threat_hunt = 'threat_hunt'
    vulnerability_scan = 'vulnerability_scan'


class SubmissionMethod(Enum):
    api = 'api'
    integration = 'integration'
    sandbox = 'sandbox'


class ATOPUseCase(Enum):
    hunting = 'hunting'
    detection = 'detection'
    prevention = 'prevention'


Presence = Literal['present', 'absent']


class IdFilter(RFBaseModel):
    """Filter by a list of IDs or a `present`/`absent` sentinel.

    Also accepts a bare value (str, list, `present`, `absent`) which is auto-wrapped
    into `{'id': value}`.
    """

    id_: Annotated[
        list[str] | Presence | None, BeforeValidator(_to_list_or_presence),
    ] = Field(alias='id', default=None)

    @model_validator(mode='before')
    @classmethod
    def _wrap_bare_value(cls, data):
        if data is None or isinstance(data, dict):
            return data
        return {'id': data}


class DetectionTimeFilter(RFBaseModel):
    from_: datetime | None = Field(alias='from', default=None)
    to: datetime | None = None


class AssociatedThreatsFilter(RFBaseModel):
    malware: IdFilter | None = None
    mitre_code: IdFilter | None = None
    threat_actor: IdFilter | None = None


class ATOPFilter(RFBaseModel):
    use_case: Annotated[
        list[ATOPUseCase] | Presence | None, BeforeValidator(_to_list_or_presence),
    ] = None
    profile: IdFilter | None = None
    job: IdFilter | None = None


class RiskScoreRange(RFBaseModel):
    gte: int | None = None
    gt: int | None = None
    lte: int | None = None
    lt: int | None = None


class IndicatorRiskScoreFilter(RFBaseModel):
    at_detection: RiskScoreRange | Presence | None = None


class IndicatorRiskFilter(RFBaseModel):
    score: IndicatorRiskScoreFilter | None = None


class IndicatorFilter(RFBaseModel):
    risk: IndicatorRiskFilter | None = None


class SearchFilters(RFBaseModel):
    organizations: Annotated[
        list[str] | None,
        BeforeValidator(Validators.convert_str_to_list),
        AfterValidator(Validators.check_uhash_prefix),
    ] = None
    indicator_type: Annotated[
        list[IOCType] | Presence | None, BeforeValidator(_to_list_or_presence),
    ] = None
    detection_rule: IdFilter | None = None
    detection_type: Annotated[
        list[SearchDetectionType] | Presence | None, BeforeValidator(_to_list_or_presence),
    ] = None
    submission_method: Annotated[
        list[SubmissionMethod] | Presence | None, BeforeValidator(_to_list_or_presence),
    ] = None
    detection_time: DetectionTimeFilter | None = None
    associated_threats: AssociatedThreatsFilter | None = None
    autonomous_threat_operations: ATOPFilter | None = None
    integration_type: IdFilter | None = None
    indicator: IndicatorFilter | None = None

    @model_validator(mode='before')
    @classmethod
    def _prune_input(cls, data):
        """Recursively drop `None` values and empty containers from filter input."""
        return _prune_none(data) if isinstance(data, dict) else data


class Entity(RFBaseModel):
    id_: str = Field(alias='id')
    type_: str | None = Field(alias='type', default=None)
    name: str | None = None
    display_name: str | None = Field(alias='displayName', default=None)


class IntegrationType(RFBaseModel):
    id_: str = Field(alias='id')
    name: str | None = None
    display_name: str | None = Field(alias='displayName', default=None)


class ATOPProfile(RFBaseModel):
    id_: str | None = Field(alias='id', default=None)


class ATOPJob(RFBaseModel):
    id_: str | None = Field(alias='id', default=None)


class ATOPResult(RFBaseModel):
    use_case: str | None = None
    profile: ATOPProfile | None = None
    job: ATOPJob | None = None


class IndicatorRiskScore(RFBaseModel):
    at_detection: int | None = None


class IndicatorRisk(RFBaseModel):
    score: IndicatorRiskScore | None = None


class SearchIndicator(RFBaseModel):
    type_: IOCType = Field(alias='type')
    value: str
    field: str | None = None
    risk: IndicatorRisk | None = None


class SearchDetectionRule(RFBaseModel):
    id_: str = Field(alias='id')


class SearchIncident(RFBaseModel):
    id_: str | None = Field(alias='id', default=None)
    name: str | None = None
    type_: str | None = Field(alias='type', default=None)


class SearchAssociatedThreats(RFBaseModel):
    threat_actors: list[Entity] | None = None
    malware: list[Entity] | None = None
    mitre_codes: list[Entity] | None = None


@total_ordering
class SearchEntry(RFBaseModel):
    """A single enriched Collective Insights event returned by `/search`.

    This class supports hashing, equality comparison, string representation, and total ordering
    of `SearchEntry` instances.

    Hashing:
        Returns a hash value based on the event `id_` and `detection_time`.

    Equality:
        Checks equality between two `SearchEntry` instances based on `id_` and `detection_time`.

    Greater-than Comparison:
        Defines a greater-than comparison between two `SearchEntry` instances based on the
        `detection_time` and the `id_`.

    String Representation:
        Returns a string representation of the `SearchEntry` instance including the `id_`,
        the IOC value, the detection time, and the detection type.

        ```python
        >>> print(entry)
        Event ID: 16046941d44a85e4748a9e9a, IOC: 1.2.3.4, Detection Time: 2025-12-15 13:05:23, Detection Type: sandbox
        ```

    Ordering:
        The ordering of `SearchEntry` instances is determined primarily by `detection_time`.
        If two instances have the same `detection_time`, the event `id_` is used as a secondary
        criterion.
    """

    id_: str = Field(alias='id')
    organizations: list[str] | None = None
    integration_type: IntegrationType | None = None
    submission_method: str | None = None
    detection_type: str | None = None
    autonomous_threat_operations: ATOPResult | None = None
    detection_time: datetime | None = None
    indicator: SearchIndicator | None = None
    action: str | None = None
    action_category: str | None = None
    detection_rules: list[SearchDetectionRule] | None = None
    incident: SearchIncident | None = None
    associated_threats: SearchAssociatedThreats | None = None
    context: dict | None = None

    def __hash__(self):
        return hash((self.id_, self.detection_time))

    def __eq__(self, other: 'SearchEntry'):
        return (self.id_, self.detection_time) == (other.id_, other.detection_time)

    def __gt__(self, other: 'SearchEntry'):
        return (self.detection_time, self.id_) > (other.detection_time, other.id_)

    def __str__(self):
        ioc = self.indicator.value if self.indicator else 'N/A'
        detection_time = (
            self.detection_time.strftime(TIMESTAMP_STR) if self.detection_time else 'N/A'
        )
        return (
            f'Event ID: {self.id_}, IOC: {ioc}, Detection Time: {detection_time}, '
            f'Detection Type: {self.detection_type or "N/A"}'
        )


class SearchCounts(RFBaseModel):
    returned: int | None = None
    total: int | None = None

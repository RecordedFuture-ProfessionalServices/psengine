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

from functools import total_ordering
from typing import Any

from pydantic import Field

from ..common_models import RFBaseModel
from .models import RiskRuleCategory


@total_ordering
class RiskRule(RFBaseModel):
    """Validate data received from the `/v2/{entity_type}/riskrules` endpoint.

    A Recorded Future risk rule is a scoring rule that contributes to the overall risk score of an
    entity of a given IOC type (ip, domain, hash, url, vulnerability). Each rule has a criticality
    level (1-3), a human readable label, a description of what it detects, and a count of entities
    currently matching the rule.

    This class supports hashing, equality comparison, string representation, and total ordering
    of `RiskRule` instances.

    Hashing:
        Returns a hash value based on the tuple `(name, criticality)`.

    Equality:
        Two `RiskRule` instances are equal if they share the same `name` and `criticality`.

    Greater-than Comparison:
        A rule is "greater" than another if its `criticality` is higher. When two rules share the
        same criticality, the one whose `name` sorts later alphabetically is considered greater.
        Combined with `@total_ordering`, this yields most-critical-first when using `sorted()` in
        reverse (or `sorted(rules, reverse=True)`).

    String Representation:
        Returns a compact one-line summary of the rule.

        ```python
        >>> print(risk_rule)
        Risk Rule: bogusBgp, Criticality: 1 (Unusual), Count: 24590
        ```
    """

    name: str
    description: str
    criticality: int
    criticality_label: str = Field(alias='criticalityLabel')
    count: int
    categories: list[RiskRuleCategory] = []
    related_entities: list[Any] = Field(alias='relatedEntities', default=[])

    def __hash__(self):
        return hash((self.name, self.criticality))

    def __eq__(self, other: 'RiskRule'):
        return (self.name, self.criticality) == (other.name, other.criticality)

    def __gt__(self, other: 'RiskRule'):
        return (self.criticality, self.name) > (other.criticality, other.name)

    def __str__(self):
        return (
            f'Risk Rule: {self.name}, '
            f'Criticality: {self.criticality} ({self.criticality_label}), '
            f'Count: {self.count}'
        )

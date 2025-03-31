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
from functools import total_ordering
from typing import Optional

from pydantic import Field

from ..common_models import RFBaseModel
from ..constants import TIMESTAMP_STR
from .models import DetectionRuleType, RuleContext, SearchFilter


@total_ordering
class DetectionRule(RFBaseModel):
    """Detection rule model to validate output of the ``/search`` endpoint.

    Methods:
        __hash__:
            Returns a hash value based on ``id_`` and updated timestamp.

        __eq__:
            Checks equality between two DetectionRule instances based on ``id_`` and updated time.

        __gt__:
            Defines a greater-than comparison between two DetectionRule instances based on
            updated timestamp and ``id_``.

        __str__:
            Returns a string representation of the DetectionRule instance with:
            ``id_``, created timestamp, updated timestamp, and title.

            .. code-block:: python

                >>> print(detection_rule)
                ID: rule123, Created: 2024-05-21 10:42:30AM, Updated: 2024-05-21 10:42:30AM,
                Title: Example Rule

    Total Ordering:
        The ordering of DetectionRule instances is determined primarily by the updated timestamp.
        If two instances have the same updated timestamp, ``id_`` is used as a secondary criterion.
    """

    id_: str = Field(alias='id')
    type_: DetectionRuleType = Field(alias='type')
    title: str
    description: str
    created: datetime
    updated: datetime
    rules: list[RuleContext]

    def __hash__(self):
        return hash((self.id_, self.updated))

    def __eq__(self, other: 'DetectionRule'):
        return (self.id_, self.updated) == (other.id_, other.updated)

    def __gt__(self, other: 'DetectionRule'):
        return (self.updated, self.id_) > (other.updated, other.id_)

    def __str__(self):
        return (
            f'ID: {self.id_}, Created: {self.created.strftime(TIMESTAMP_STR)}, '
            f'Updated: {self.updated.strftime(TIMESTAMP_STR)}, Title: {self.title}'
        )


class DetectionRuleSearchOut(RFBaseModel):
    """Model to validate ``/search`` endpoint payload sent."""

    filter_: Optional[SearchFilter] = Field(alias='filter', default={})
    tagged_entities: Optional[bool] = False
    limit: Optional[int] = None
    offset: Optional[str] = None

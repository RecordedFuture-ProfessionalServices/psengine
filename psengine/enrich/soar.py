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
from typing import Optional

from pydantic import Field

from ..common_models import IdNameTypeDescription, RFBaseModel
from .models.soar import Risk


@total_ordering
class SOAREnrichedEntity(RFBaseModel):
    """Model used for validating returned data from SOAR enrichment endpoint for bulk enrichment.

    Methods:
        __hash__:
            Returns a hash value based on the entity ``id_`` and the risk score.

        __eq__:
            Checks equality between two ``SOAREnrichedEntity`` instances based on their entity name
            and the risk score.

        __gt__:
            Defines a greater-than comparison between two ``SOAREnrichedEntity`` instances based on
            their risk score and entity name.

        __str__:
            Returns a string representation of the ``SOAREnrichedEntity`` instance with:
            enriched entity name, risk score, and most critical rule.

            .. code-block:: python

                >>> print(soar_enriched_entity)
                Enriched Entity: 1.1.1.1, Risk Score: 95, Most Critical Rule: C&C Server

    Total Ordering:
        The ordering of ``SOAREnrichedEntity`` instances is determined primarily by the risk score.
        If two instances have the same risk score, their entity name is used as a secondary
        criterion for ordering.
    """

    risk: Risk
    entity: IdNameTypeDescription

    def __hash__(self):
        return hash((self.entity.id_, self.risk.score))

    def __eq__(self, other: 'SOAREnrichedEntity'):
        return (self.entity.name, self.risk.score) == (other.entity.name, other.risk.score)

    def __gt__(self, other: 'SOAREnrichedEntity'):
        return (self.risk.score, self.entity.name) > (other.risk.score, other.entity.name)

    def __str__(self):
        return (
            f'Enriched Entity: {self.entity.name}, Risk Score: {self.risk.score}, '
            f'Most Critical Rule: {self.risk.rule.most_critical}'
        )


class SOAREnrichIn(RFBaseModel):
    """Model used to validate payload sent to SOAR enrichment endpoint."""

    ip: Optional[list[str]] = None
    domain: Optional[list[str]] = None
    url: Optional[list[str]] = None
    hash_: Optional[list[str]] = Field(alias='hash', default=None)
    vulnerability: Optional[list[str]] = None
    companybydomain: Optional[list[str]] = None


class SOAREnrichOut(RFBaseModel):
    """Model used for collecting all the data returned in a SOAR call."""

    entity: str
    is_enriched: bool
    content: Optional[SOAREnrichedEntity] = None

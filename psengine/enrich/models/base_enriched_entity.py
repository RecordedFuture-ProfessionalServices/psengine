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

from typing import Optional

from pydantic import Field

from ...analyst_notes.note import AnalystNote
from ...common_models import IdNameTypeDescription, RFBaseModel
from ..models.lookup import (
    AIInsights,
    Metric,
    ReferenceCount,
    RelatedEntities,
    Sighting,
    Timestamps,
)


class BaseEnrichedEntity(RFBaseModel):
    """Base Model for Enrichment.
    This model is intended to be inherited and should not be used on its own.
    """

    ai_insights: Optional[AIInsights] = Field(alias='aiInsights', default=None)
    analyst_notes: Optional[list[AnalystNote]] = Field(alias='analystNotes', default=[])
    counts: Optional[list[ReferenceCount]] = []
    entity: Optional[IdNameTypeDescription] = None
    intel_card: Optional[str] = Field(alias='intelCard', default=None)
    metrics: Optional[list[Metric]] = []
    related_entities: Optional[list[RelatedEntities]] = Field(alias='relatedEntities', default=[])
    sightings: Optional[list[Sighting]] = []
    timestamps: Optional[Timestamps] = None

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

    ai_insights: AIInsights | None = Field(alias='aiInsights', default=None)
    analyst_notes: list[AnalystNote] | None = Field(alias='analystNotes', default=[])
    counts: list[ReferenceCount] | None = []
    entity: IdNameTypeDescription | None = None
    intel_card: str | None = Field(alias='intelCard', default=None)
    metrics: list[Metric] | None = []
    related_entities: list[RelatedEntities] | None = Field(alias='relatedEntities', default=[])
    sightings: list[Sighting] | None = []
    timestamps: Timestamps | None = None

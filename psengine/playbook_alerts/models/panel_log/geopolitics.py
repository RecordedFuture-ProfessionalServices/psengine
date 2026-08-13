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

from ....common_models import RFBaseModel
from .common import ChangeType


class EventAssessment(RFBaseModel):
    name: str | None = None
    criticality: str | None = None


class MainEvent(RFBaseModel):
    event_id: str | None = None
    assessments: list[EventAssessment] | None = []
    type_: str | None = Field(alias='type', default=None)


class EventCluster(RFBaseModel):
    cluster_id: str | None = None
    main_event: MainEvent | None = None
    type_: str | None = Field(alias='type', default=None)
    other_event_ids: list[str] | None = []


class EvidenceClusterChanges(ChangeType):
    """`evidence_changes` (note the plural, distinct from `evidence_change`)."""

    added: list[EventCluster] | None = []


class ClusterChangeAdded(ChangeType):
    cluster_id: str | None = None
    main_event: MainEvent | None = None
    other_event_ids: list[str] | None = []

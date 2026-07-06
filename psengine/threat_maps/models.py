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

from ..common_models import IdName, RFBaseModel


class ThreatMapAxis(Enum):
    opportunity = 'opportunity'
    intent = 'intent'


class ThreatMapType(Enum):
    actors = 'actors'
    malware = 'malware'

    @property
    def category_slug(self) -> str:
        """Return the URL slug used by the categories endpoint.

        The map endpoint uses `actors`/`malware` (this enum's value), but the
        categories endpoint uses the singular `actor`/`malware` — see api.md.
        """
        return 'actor' if self is ThreatMapType.actors else 'malware'


class LogEntry(RFBaseModel):
    watchlist: IdName | None = None
    entity: IdName
    severity: int
    axis: str
    date: datetime


class EntityAttributes(RFBaseModel):
    name: str
    alias: list[str] = []


class ThreatActorAttributes(RFBaseModel):
    name: str
    common_names: list[str] = []
    alias: list[str] = []
    categories: list[IdName] = []

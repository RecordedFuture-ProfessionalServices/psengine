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

import datetime
from typing import Optional
from uuid import UUID

from ...common_models import RFBaseModel

from .api import ApiMeta


class Project(RFBaseModel):
    id: UUID
    title: str
    scanning_enabled: Optional[bool] = None
    last_scanned_at: Optional[datetime.datetime] = None
    inserted_at: Optional[datetime.datetime] = None
    max_exposure_score: Optional[int] = None

    def __str__(self) -> str:
        msg = 'Name: {}, Id: {}, Enabled: {}'
        return msg.format(
            self.title,
            self.id,
            self.scanning_enabled or 'False',
        )

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: 'Project'):
        return self.id == other.id

    def __gt__(self, other: 'Project'):
        return self.title == other.title


class ProjectListOut(RFBaseModel):
    content: list[Project]
    meta: ApiMeta

    def __str__(self) -> str:
        return '\n'.join(str(c) for c in sorted(self.content))

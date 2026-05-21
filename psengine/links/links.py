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


from ..common_models import IdNameType, RFBaseModel
from .models import EntityAttribute, EntitySearchError


class LinkedEntity(IdNameType):
    """An entity connected to the search target."""

    source: str | None = None
    section: str | None = None
    attributes: list[EntityAttribute] = []


class Link(RFBaseModel):
    """The result set for a single entity that was queried."""

    entity: IdNameType | None = None
    links: list[LinkedEntity] = []
    error: EntitySearchError | None = None


class LinksSearchResponseOut(RFBaseModel):
    """Response from POST `/links/search` endpoint."""

    data: list[Link] = []

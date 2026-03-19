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

from ...common_models import RFBaseModel


class PaginationResponse(RFBaseModel):
    next_cursor: Optional[str] = None
    limit: Optional[int] = 50
    total: Optional[int] = None
    sort: Optional[list[list[str]]] = None


class ApiCount(RFBaseModel):
    returned: int
    total: Optional[int] = None


class ApiMeta(RFBaseModel):
    counts: Optional[ApiCount] = None
    pagination: Optional[PaginationResponse] = None
    request_id: Optional[str] = None


class Pagination(RFBaseModel):
    next_cursor: Optional[str] = None
    limit: Optional[int] = 50

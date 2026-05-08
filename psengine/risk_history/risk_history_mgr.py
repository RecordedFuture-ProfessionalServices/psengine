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

import logging
from typing import Annotated, Optional, Union

from pydantic import validate_call
from typing_extensions import Doc

from ..endpoints import EP_RISK_HISTORY
from ..helpers import debug_call
from ..helpers.helpers import connection_exceptions
from ..rf_client import RFClient
from .errors import RiskHistoryError
from .models import RiskHistory, RiskHistoryIn


class RiskHistoryMgr:
    """Manages requests for Recorded Future Risk History information."""

    def __init__(self, rf_token: str = None):
        """Initializes the `RiskHistoryMgr` object.

        Args:
            rf_token (str, optional): Recorded Future API token.
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=RiskHistoryError)
    def search(
        self,
        entities: Annotated[Union[str, list[str]], Doc('Entities to search.')],
        from_: Annotated[Optional[str], Doc('ISO8691 date or relative date like -1d')] = None,
        to: Annotated[Optional[str], Doc('ISO8691 date or relative date like -1d')] = None,
    ) -> Annotated[list[RiskHistory], Doc('A list of history information.')]:
        """Search for the risk history of one or more entities.

        Endpoint:
            `/risk/history`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            RIskHistoryError: If API error occurs.
        """
        data = RiskHistoryIn.model_validate({'entities': entities, 'from': from_, 'to': to})
        attrs = self.rf_client.request('post', EP_RISK_HISTORY, data=data.json()).json()['data']

        return [RiskHistory.model_validate(attr) for attr in attrs]

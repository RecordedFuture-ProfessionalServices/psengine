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
from typing import Annotated

from pydantic import validate_call
from typing_extensions import Doc

from ..endpoints import EP_RISK_RULES
from ..helpers import debug_call
from ..helpers.helpers import connection_exceptions
from ..rf_client import RFClient
from .errors import RiskRuleFetchError
from .models import RiskRuleEntityType
from .risk_rule import RiskRule


class RiskRuleMgr:
    """Manages requests for Recorded Future risk rules."""

    def __init__(
        self,
        rf_token: Annotated[str | None, Doc('Recorded Future API token.')] = None,
    ):
        """Initializes the `RiskRuleMgr` object."""
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=RiskRuleFetchError)
    def fetch(
        self,
        entity_type: Annotated[
            RiskRuleEntityType,
            Doc('The IOC type to fetch risk rules for: ip, domain, hash, vulnerability, or url.'),
        ],
    ) -> Annotated[list[RiskRule], Doc('The list of risk rules for the given IOC type.')]:
        """Fetch every risk rule defined for the given IOC type.

        Endpoint:
            `/v2/{entity_type}/riskrules`

        Raises:
            ValidationError: If `entity_type` is not one of the supported IOC types.
            RiskRuleFetchError: If an API error occurs while fetching risk rules.
        """
        url = EP_RISK_RULES.format(entity_type.value)
        self.log.info(f'Fetching risk rules for entity type: {entity_type.value}')
        response = self.rf_client.request('get', url).json()
        results = response['data']['results']
        return [RiskRule.model_validate(r) for r in results]

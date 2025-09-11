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

from ..constants import DEFAULT_LIMIT
from ..endpoints import EP_DETECTION_RULES
from ..helpers import debug_call
from ..helpers.helpers import connection_exceptions
from ..rf_client import RFClient
from .detection_rule import DetectionRule, DetectionRuleSearchOut
from .errors import DetectionRuleFetchError, DetectionRuleSearchError

SEARCH_LIMIT = 100


class DetectionMgr:
    """Class to manage DetectionRules and interaction with the Detection API."""

    def __init__(
        self,
        rf_token: Annotated[Optional[str], Doc('Recorded Future API token.')] = None,
    ):
        """Initialize the `DetectionMgr` object."""
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=DetectionRuleSearchError)
    def search(
        self,
        detection_rule: Annotated[
            Union[str, list[str], None], Doc('Types of detection rules to search for.')
        ] = None,
        entities: Annotated[
            Optional[list[str]], Doc('List of entities to filter the search.')
        ] = None,
        created_before: Annotated[
            Optional[str], Doc('Filter for rules created before this date or relative date.')
        ] = None,
        created_after: Annotated[
            Optional[str], Doc('Filter for rules created after this date or relative date.')
        ] = None,
        updated_before: Annotated[
            Optional[str], Doc('Filter for rules updated before this date or relative date.')
        ] = None,
        updated_after: Annotated[
            Optional[str], Doc('Filter for rules updated after this date or relative date.')
        ] = None,
        doc_id: Annotated[Optional[str], Doc('Filter by document ID.')] = None,
        title: Annotated[Optional[str], Doc('Filter by title.')] = None,
        tagged_entities: Annotated[
            Optional[bool], Doc('Whether to filter by tagged entities.')
        ] = None,
        max_results: Annotated[
            Optional[int], Doc('Limit the total number of results returned.')
        ] = DEFAULT_LIMIT,
    ) -> Annotated[
        list[DetectionRule], Doc('A list of detection rules matching the search criteria.')
    ]:
        """Search for detection rules based on various filter criteria.

        Endpoint:
            `detection-rule/search`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            DetectionRuleSearchError: If connection error occurs.
        """
        filters = {
            'types': detection_rule,
            'entities': entities,
            'created': {'before': created_before, 'after': created_after},
            'updated': {'before': updated_before, 'after': updated_after},
            'doc_id': doc_id,
            'title': title,
        }
        data = {
            'filter': filters,
            'tagged_entities': tagged_entities,
            'limit': SEARCH_LIMIT,
        }

        data = DetectionRuleSearchOut.model_validate(data)
        results = self.rf_client.request_paged(
            'post',
            EP_DETECTION_RULES,
            data=data.json(),
            results_path='result',
            offset_key='offset',
            max_results=max_results,
        )

        results = results if isinstance(results, list) else results.json().get('result', [])
        return [DetectionRule.model_validate(data) for data in results]

    @debug_call
    @validate_call
    def fetch(
        self,
        doc_id: Annotated[str, Doc('Detection rule ID to look up.')],
    ) -> Annotated[Optional[DetectionRule], Doc('The detection rule found for the given ID.')]:
        """Fetch a detection rule based on its ID.

        Endpoint:
            `detection-rule/search`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            DetectionRuleLookupError: If no rule is found for the given ID.
        """
        try:
            result = self.search(doc_id=doc_id)
        except DetectionRuleSearchError as e:
            raise DetectionRuleFetchError(f'Error in fething of {doc_id}') from e

        if result:
            return result[0]

        self.log.info(f'No rule found for id {doc_id}')
        return None

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
from typing import Optional, Union

from pydantic import validate_call

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

    def __init__(self, rf_token: str = None):
        """Initializes the DetectionMgr object.

        Args:
            rf_token (str, optional): Recorded Future API token. Defaults to None
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=DetectionRuleSearchError)
    def search(
        self,
        detection_rule: Union[list[str], str, None] = None,
        entities: Optional[list[str]] = None,
        created_before: Optional[str] = None,
        created_after: Optional[str] = None,
        updated_before: Optional[str] = None,
        updated_after: Optional[str] = None,
        doc_id: Optional[str] = None,
        title: Optional[str] = None,
        tagged_entities: Optional[bool] = None,
        max_results: Optional[int] = DEFAULT_LIMIT,
    ) -> list[DetectionRule]:
        """Search for detection rules based on various filter criteria.

        Endpoint:
            ``detection-rule/search``

        Args:
            detection_rule: Types of detection rules to search for. Defaults to None.
            entities: List of entities to filter the search. Defaults to None.
            created_before: Filter for rules created before this date. Defaults to None.
            created_after: Filter for rules created after this date. Defaults to None.
            updated_before: Filter for rules updated before this date. Defaults to None.
            updated_after: Filter for rules updated after this date. Defaults to None.
            doc_id: Filter by document ID. Defaults to None.
            title: Filter by title. Defaults to None.
            tagged_entities: Whether to filter by tagged entities. Defaults to None.
            max_results: Limit the total number of results returned. Defaults to 10.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            DetectionRuleSearchError: if connection error occurs.

        Returns:
            List[DetectionRule]: A list of detection rules matching the search criteria.
        """
        detection_rule = [detection_rule] if isinstance(detection_rule, str) else detection_rule
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
    def fetch(self, doc_id: str) -> Optional[DetectionRule]:
        """Fetch of a detection rule based on rule id.

        Endpoint:
            ``detection-rule/search``

        Args:
            doc_id (str): Detection rule id to lookup.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            DetectionRuleLookupError: If no rule is found for the given id.

        Returns:
            Optional[DetectionRule]: The detection rule found for the given id.
        """
        try:
            result = self.search(doc_id=doc_id)
        except DetectionRuleSearchError as e:
            raise DetectionRuleFetchError(f'Error in fething of {doc_id}') from e

        if result:
            return result[0]
        self.log.info(f'No rule found for id {doc_id}')

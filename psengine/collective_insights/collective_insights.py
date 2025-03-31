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

import json
import logging
from typing import Union

from pydantic import validate_call

from ..endpoints import EP_COLLECTIVE_INSIGHTS_DETECTIONS
from ..helpers import connection_exceptions, debug_call
from ..rf_client import RFClient
from .constants import SUMMARY_DEFAULT
from .errors import CollectiveInsightsError
from .insight import Insight, InsightsIn, InsightsOut


class CollectiveInsights:
    """Class for interacting with the Recorded Future Collective Insights API."""

    def __init__(self, rf_token: str = None):
        """Initializes the CollectiveInsights object.

        Args:
            rf_token (str, optional): Recorded Future API token. Defaults to None
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @validate_call
    @debug_call
    def create(
        self,
        ioc_value: str,
        ioc_type: str,
        timestamp: str,
        detection_type: str,
        detection_sub_type: str = None,
        detection_id: str = None,
        detection_name: str = None,
        ioc_field: str = None,
        ioc_source_type: str = None,
        incident_id: str = None,
        incident_name: str = None,
        incident_type: str = None,
        mitre_codes: Union[list[str], str] = None,
        malwares: Union[list[str], str] = None,
        **kwargs,
    ) -> Insight:
        """Create a new Insight object.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.

        Returns:
            Insight object.
        """
        malwares = malwares if isinstance(malwares, list) else [malwares] if malwares else None
        mitre_codes = (
            mitre_codes if isinstance(mitre_codes, list) else [mitre_codes] if mitre_codes else None
        )

        incident = {'id': incident_id, 'type': incident_type, 'name': incident_name}
        detection = {
            'id': detection_id,
            'name': detection_name,
            'type': detection_type,
            'sub_type': detection_sub_type,
        }
        ioc = {
            'type': ioc_type,
            'value': ioc_value,
            'source_type': ioc_source_type,
            'field': ioc_field,
        }
        data = {
            'timestamp': timestamp,
            'ioc': ioc,
            'incident': incident,
            'detection': detection,
            'mitre_codes': mitre_codes,
            'malwares': malwares,
        }
        data['incident'] = (
            None
            if isinstance(data['incident'], dict)
            and all(sub_v is None for sub_v in data['incident'].values())
            else data['incident']
        )
        if kwargs:
            data.update(kwargs)

        return Insight.model_validate(data)

    @validate_call
    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=CollectiveInsightsError)
    def submit(
        self,
        insight: Union[Insight, list[Insight]],
        debug: bool = True,
        organization_ids: list = None,
    ) -> InsightsIn:
        """Submit a detection or insight to Recorded Future Collective Insights API.

        Endpoint:
            ``collective-insights/detections``

        Args:
            insight (list[Insight] or Insight): A detection/insight
            debug (bool, optional): Determines if submission will show in SecOPS dashboard.
            organization_ids (list, optional): Org ID. Defaults to None.

        Raises:
            CollectiveInsightsError: if connection error occurs.
            ValidationError if any supplied parameter is of incorrect type.

        Returns:
            InsightsIn: response from Recorded Future API
        """
        if not insight:
            raise ValueError('Insight cannot be empty')

        insight = insight if isinstance(insight, list) else [insight]

        ci_data = self._prepare_ci_request(insight, debug, organization_ids)
        response = self.rf_client.request(
            'post',
            url=EP_COLLECTIVE_INSIGHTS_DETECTIONS,
            data=ci_data.json(),
        )

        return InsightsIn.model_validate(response.json())

    def _prepare_ci_request(
        self,
        insight: list[Insight],
        debug: bool = True,
        organization_ids: list = None,
    ) -> InsightsOut:
        params = {'options': {}}

        params['data'] = [ins.json() for ins in insight]

        if organization_ids is not None and len(organization_ids):
            params['organization_ids'] = organization_ids
        params['options']['debug'] = debug

        # We always have summary of the submission
        params['options']['summary'] = SUMMARY_DEFAULT

        self.log.debug(f'Params for submission: \n{json.dumps(params, indent=2)}')

        return InsightsOut.model_validate(params)

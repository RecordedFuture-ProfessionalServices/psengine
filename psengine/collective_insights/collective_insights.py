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
from typing import Annotated, Optional, Union

from pydantic import validate_call
from typing_extensions import Doc

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
            rf_token (str, optional): Recorded Future API token.
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @validate_call
    @debug_call
    def create(
        self,
        ioc_value: Annotated[str, Doc('The value of the IOC.')],
        ioc_type: Annotated[str, Doc('The type of the IOC.')],
        timestamp: Annotated[str, Doc('The timestamp associated with the detection as ISO 8601.')],
        detection_type: Annotated[str, Doc('The type of the detection.')],
        detection_sub_type: Annotated[Optional[str], Doc('The subtype of the detection.')] = None,
        detection_id: Annotated[Optional[str], Doc('The ID of the detection.')] = None,
        detection_name: Annotated[Optional[str], Doc('The name of the detection.')] = None,
        ioc_field: Annotated[Optional[str], Doc('The field in which the IOC was detected.')] = None,
        ioc_source_type: Annotated[Optional[str], Doc('The source type of the IOC.')] = None,
        incident_id: Annotated[Optional[str], Doc('The ID of the incident.')] = None,
        incident_name: Annotated[Optional[str], Doc('The name of the incident.')] = None,
        incident_type: Annotated[Optional[str], Doc('The type of the incident.')] = None,
        mitre_codes: Annotated[
            Union[list[str], str, None], Doc('MITRE ATT&CK technique or tactic codes.')
        ] = None,
        malwares: Annotated[
            Union[list[str], str, None], Doc('Associated malware family or names.')
        ] = None,
        **kwargs,
    ) -> Annotated[Insight, Doc('The created Insight object.')]:
        """Create a new Insight object.

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
        """
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
        insight: Annotated[
            Union[Insight, list[Insight]], Doc('A detection or list of detections to submit.')
        ],
        debug: Annotated[
            bool, Doc('Whether the submission should appear in the SecOPS dashboard.')
        ] = True,
        organization_ids: Annotated[Optional[list], Doc('List of organization IDs.')] = None,
    ) -> Annotated[InsightsIn, Doc('Response from the Recorded Future API.')]:
        """Submit a detection or insight to the Recorded Future Collective Insights API.

        Endpoint:
            `collective-insights/detections`

        Raises:
            CollectiveInsightsError: If connection error occurs.
            ValidationError: If any supplied parameter is of incorrect type.
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

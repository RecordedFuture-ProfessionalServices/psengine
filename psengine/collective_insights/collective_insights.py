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
from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, validate_call
from typing_extensions import Doc

from ..constants import DEFAULT_LIMIT
from ..endpoints import EP_COLLECTIVE_INSIGHTS_DETECTIONS, EP_COLLECTIVE_INSIGHTS_SEARCH
from ..helpers import connection_exceptions, debug_call
from ..rf_client import RFClient
from .constants import SEARCH_MAX_LIMIT, SEARCH_PAGE_SIZE, SUMMARY_DEFAULT
from .errors import CollectiveInsightsError, CollectiveInsightsSearchError
from .insight import Insight, InsightsIn, InsightsOut, SearchIn
from .models import Presence, SearchEntry


class CollectiveInsights:
    """Class for interacting with the Recorded Future Collective Insights API."""

    def __init__(
        self,
        rf_token: Annotated[str | None, Doc('Recorded Future API token.')] = None,
    ):
        """Initializes the CollectiveInsights object."""
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
        detection_sub_type: Annotated[str | None, Doc('The subtype of the detection.')] = None,
        detection_id: Annotated[str | None, Doc('The ID of the detection.')] = None,
        detection_name: Annotated[str | None, Doc('The name of the detection.')] = None,
        ioc_field: Annotated[str | None, Doc('The field in which the IOC was detected.')] = None,
        ioc_source_type: Annotated[str | None, Doc('The source type of the IOC.')] = None,
        incident_id: Annotated[str | None, Doc('The ID of the incident.')] = None,
        incident_name: Annotated[str | None, Doc('The name of the incident.')] = None,
        incident_type: Annotated[str | None, Doc('The type of the incident.')] = None,
        mitre_codes: Annotated[
            list[str] | str | None, Doc('MITRE ATT&CK technique or tactic codes.')
        ] = None,
        malwares: Annotated[
            list[str] | str | None, Doc('Associated malware family or names.')
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
            Insight | list[Insight], Doc('A detection or list of detections to submit.')
        ],
        debug: Annotated[
            bool, Doc('Whether the submission should appear in the SecOPS dashboard.')
        ] = True,
        organization_ids: Annotated[list | None, Doc('List of organization IDs.')] = None,
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

    @validate_call
    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=CollectiveInsightsSearchError)
    def search(
        self,
        indicator_type: Annotated[
            list[str] | str | Presence | None,
            Doc('IOC type filter (`ip`, `domain`, `hash`, `url`, `vulnerability`).'),
        ] = None,
        detection_type: Annotated[
            list[str] | str | Presence | None,
            Doc(
                'Detection method filter (`correlation`, `playbook`, `detection_rule`, '
                '`sandbox`, `threat_hunt`, `vulnerability_scan`).',
            ),
        ] = None,
        submission_method: Annotated[
            list[str] | str | Presence | None,
            Doc('Submission method filter (`api`, `integration`, `sandbox`).'),
        ] = None,
        organizations: Annotated[
            list[str] | str | None, Doc('Filter by organization IDs (uhash).')
        ] = None,
        detection_rule_id: Annotated[
            list[str] | str | Presence | None, Doc('Filter by associated detection rule IDs.')
        ] = None,
        detection_time_from: Annotated[
            str | datetime | None, Doc('Start of the detection time range (inclusive).')
        ] = None,
        detection_time_to: Annotated[
            str | datetime | None, Doc('End of the detection time range (inclusive).')
        ] = None,
        malware_id: Annotated[
            list[str] | str | Presence | None,
            Doc('Filter by associated malware entity IDs.'),
        ] = None,
        mitre_code_id: Annotated[
            list[str] | str | Presence | None,
            Doc('Filter by associated MITRE ATT&CK IDs (prefixed with `mitre:`).'),
        ] = None,
        threat_actor_id: Annotated[
            list[str] | str | Presence | None,
            Doc('Filter by associated threat actor entity IDs.'),
        ] = None,
        atop_use_case: Annotated[
            list[str] | str | Presence | None,
            Doc(
                'Filter by Autonomous Threat Operations use case '
                '(`hunting`, `detection`, `prevention`).',
            ),
        ] = None,
        atop_profile_id: Annotated[
            list[str] | str | Presence | None,
            Doc('Filter by Autonomous Threat Operations profile ID.'),
        ] = None,
        atop_job_id: Annotated[
            list[str] | str | Presence | None,
            Doc('Filter by Autonomous Threat Operations job ID.'),
        ] = None,
        integration_type_id: Annotated[
            list[str] | str | Presence | None, Doc('Filter by integration type entity IDs.')
        ] = None,
        indicator_risk_score: Annotated[
            dict | Literal['present', 'absent'] | None,
            Doc(
                'Filter by indicator risk score at detection time. Pass `present`/`absent` '
                'or a range dict such as `{"gte": 50, "lt": 90}`.',
            ),
        ] = None,
        max_results: Annotated[int, Doc('Maximum number of events to return.')] = Field(
            ge=1, default=DEFAULT_LIMIT
        ),
        page_size: Annotated[int, Doc('Number of events per page (max 1000).')] = Field(
            ge=1, le=SEARCH_MAX_LIMIT, default=SEARCH_PAGE_SIZE
        ),
    ) -> Annotated[
        list[SearchEntry],
        Doc('Enriched events matching the search criteria.'),
    ]:
        """Search enriched Collective Insights events.

        Endpoint:
            `collective-insights/search`

        Raises:
            CollectiveInsightsSearchError: If connection error occurs.
            ValidationError: If any supplied parameter is of incorrect type.
        """
        data = {
            'filters': {
                'organizations': organizations,
                'indicator_type': indicator_type,
                'detection_rule': detection_rule_id,
                'detection_type': detection_type,
                'submission_method': submission_method,
                'detection_time': {'from': detection_time_from, 'to': detection_time_to},
                'associated_threats': {
                    'malware': malware_id,
                    'mitre_code': mitre_code_id,
                    'threat_actor': threat_actor_id,
                },
                'autonomous_threat_operations': {
                    'use_case': atop_use_case,
                    'profile': atop_profile_id,
                    'job': atop_job_id,
                },
                'integration_type': integration_type_id,
                'indicator': {'risk': {'score': {'at_detection': indicator_risk_score}}},
            },
            'limit': min(page_size, max_results),
        }
        search_data = SearchIn.model_validate(data)
        self.log.info(f'Searching Collective Insights events with query: {search_data.json()}')

        results = self.rf_client.request_paged(
            method='post',
            url=EP_COLLECTIVE_INSIGHTS_SEARCH,
            data=search_data.json(),
            results_path='data',
            offset_key='offset',
            max_results=max_results,
        )

        return [SearchEntry.model_validate(r) for r in results]

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

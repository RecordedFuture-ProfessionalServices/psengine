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
from itertools import chain
from typing import Annotated, Optional, Union

from pydantic import Field, validate_call
from typing_extensions import Doc

from ..constants import DEFAULT_LIMIT
from ..endpoints import (
    EP_CLASSIC_ALERTS_HITS,
    EP_CLASSIC_ALERTS_ID,
    EP_CLASSIC_ALERTS_IMAGE,
    EP_CLASSIC_ALERTS_RULES,
    EP_CLASSIC_ALERTS_SEARCH,
    EP_CLASSIC_ALERTS_UPDATE,
)
from ..helpers import MultiThreadingHelper, connection_exceptions, debug_call
from ..rf_client import RFClient
from .classic_alert import AlertRuleOut, ClassicAlert, ClassicAlertHit
from .constants import ALERTS_PER_PAGE, ALL_CA_FIELDS, REQUIRED_CA_FIELDS
from .errors import (
    AlertFetchError,
    AlertImageFetchError,
    AlertSearchError,
    AlertUpdateError,
    NoRulesFoundError,
)


class ClassicAlertMgr:
    """Alert Manager for Classic Alert (v3) API."""

    def __init__(self, rf_token: str = None):
        """Initializes the ClassicAlertMgr object.

        Args:
            rf_token (str, optional): Recorded Future API token.
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=AlertSearchError)
    def search(
        self,
        triggered: Annotated[
            Optional[str], Doc('Filter on triggered time. Format: -1d or [2017-07-30,2017-07-31].')
        ] = None,
        status: Annotated[
            Optional[str],
            Doc('Filter on status, such as: `New`, `Resolved`, `Pending`, `Dismissed`.'),
        ] = None,
        rule_id: Annotated[
            Union[str, list[str], None], Doc('Filter by a specific Alert Rule ID.')
        ] = None,
        freetext: Annotated[Optional[str], Doc('Filter by a freetext search.')] = None,
        tagged_text: Annotated[
            Optional[bool], Doc('Entities in the alert title and message body will be marked up.')
        ] = None,
        order_by: Annotated[
            Optional[str], Doc('Sort by a specific field, such as: `triggered`.')
        ] = None,
        direction: Annotated[
            Optional[str], Doc('Sort direction, such as: `asc` or `desc`.')
        ] = None,
        fields: Annotated[
            Optional[list[str]],
            Doc(
                """
                Fields to include in the search result.

                **Note:**
                Defaults fields are `id`, `log`, `title`, `rule` which are always retrieved.
                Any provided fields are added to these."
                """
            ),
        ] = REQUIRED_CA_FIELDS,
        max_results: Annotated[
            Optional[int], Doc('Maximum number of records to return. Maximum 1000.')
        ] = Field(ge=1, le=1000, default=DEFAULT_LIMIT),
        max_workers: Annotated[
            Optional[int],
            Doc(
                """
                Number of workers to use for concurrent fetches.
                Applied only when multiple `rule_id` values are provided.
                """
            ),
        ] = Field(ge=0, le=50, default=0),
        alerts_per_page: Annotated[
            Optional[int], Doc('Number of items to retrieve per page.')
        ] = Field(ge=1, le=1000, default=ALERTS_PER_PAGE),
    ) -> Annotated[list[ClassicAlert], Doc('List of ClassicAlert models.')]:
        """Search for triggered alerts.

        Does pagination requests on batches of `alerts_per_page` up to `max_results`.

        Warning:
            Paginating with a high number of items per page may lead to timeout errors from the API.

        Endpoint:
            `v3/alerts/`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            AlertSearchError: If connection error occurs.
        """
        rule_id = None if rule_id == [] else rule_id
        params = {
            'triggered': triggered,
            'status': status,
            'freetext': freetext,
            'tagged_text': tagged_text,
            'order_by': order_by,
            'direction': direction,
            'fields': fields,
            'max_results': DEFAULT_LIMIT if max_results is None else max_results,
            'alerts_per_page': alerts_per_page,
        }
        if isinstance(rule_id, list) and max_workers:
            return list(
                chain.from_iterable(
                    MultiThreadingHelper.multithread_it(
                        max_workers, self._search, iterator=rule_id, **params
                    )
                )
            )

        if isinstance(rule_id, list):
            return list(chain.from_iterable(self._search(rule, **params) for rule in rule_id))

        if isinstance(rule_id, str):
            return self._search(rule_id, **params)
        return self._search(**params)

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=AlertFetchError)
    def fetch(
        self,
        id_: Annotated[str, Doc('The alert ID to be fetched.')] = Field(min_length=4),
        fields: Annotated[
            Optional[list[str]],
            Doc(
                """
                Fields to include in the fetch result.

                **Note:**
                All fields are collected by default. Specify the fields needed, however the fields
                `id`, `log`, `title`, `rule` are always retrieved.
                Any provided fields are added to these."
                """
            ),
        ] = ALL_CA_FIELDS,
        tagged_text: Annotated[
            Optional[bool],
            Doc('Entities in the alert title and message body will be marked up with entity IDs.'),
        ] = None,
    ) -> Annotated[ClassicAlert, Doc('ClassicAlert model.')]:
        """Fetch a specific alert.

        The alert can be saved to a file as shown below:

        Example:
            ```python
            from pathlib import Path
            from json import dumps
            from psengine.classic_alerts import ClassicAlertMgr

            mgr = ClassicAlertMgr()
            alert = mgr.fetch('zVEe6k')
            OUTPUT_DIR = Path('your' / 'path')
            OUTPUT_DIR.mkdir(exist_ok=True)
            (OUTPUT_DIR / f'{alert.id_}.json').write_text(dumps(alert.json(), indent=2))
            ```

        Endpoint:
            `v3/alerts/{id_}`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            AlertFetchError: If a fetch of the alert via the API fails.
        """
        params = {}
        params['fields'] = set((fields or []) + REQUIRED_CA_FIELDS)
        params['fields'] = ','.join(params['fields'])

        if tagged_text:
            params['taggedText'] = tagged_text

        self.log.info(f'Fetching alert: {id_}')
        response = self.rf_client.request(
            'get', url=EP_CLASSIC_ALERTS_ID.format(id_), params=params
        ).json()
        return ClassicAlert.model_validate(response.get('data'))

    @debug_call
    @validate_call
    def fetch_bulk(
        self,
        ids: Annotated[list[str], Doc('Alert IDs that should be fetched.')],
        fields: Annotated[
            Optional[list[str]],
            Doc(
                """
                Fields to include in the fetch result.

                **Note:**
                All fields are collected by default. Specify the fields needed, however the fields
                `id`, `log`, `title`, `rule` are always retrieved.
                Any provided fields are added to these."
                """
            ),
        ] = ALL_CA_FIELDS,
        tagged_text: Annotated[
            Optional[bool],
            Doc('Entities in the alert title and message body will be marked up with entity IDs.'),
        ] = None,
        max_workers: Annotated[
            Optional[int], Doc('Number of workers to multithread requests.')
        ] = 0,
    ) -> Annotated[list[ClassicAlert], Doc('List of ClassicAlert models.')]:
        """Fetch multiple alerts.

        Example:
            ```python
            from json import dumps
            from pathlib import Path
            from psengine.classic_alerts import ClassicAlertMgr

            mgr = ClassicAlertMgr()
            alerts = mgr.fetch_bulk(ids=['zVEe6k', 'zVHPXX'])
            OUTPUT_DIR = Path('your/path')
            OUTPUT_DIR.mkdir(exist_ok=True)
            for i, alert in enumerate(alerts):
                (OUTPUT_DIR / f'filename_{i}.json').write_text(dumps(alert.json(), indent=2))
            ```

            Alternatively, save all alerts to a single file:

            ```python
            from json import dump
            from pathlib import Path
            from psengine.classic_alerts import ClassicAlertMgr

            mgr = ClassicAlertMgr()
            OUTPUT_FILE = Path('your/path/file')
            alerts = mgr.fetch_bulk(ids=['zVEe6k', 'zVHPXX'])
            with OUTPUT_FILE.open('w') as f:
                dump([alert.json() for alert in alerts], f, indent=2)
            ```

        Endpoint:
            `v3/alerts/{id_}`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            AlertFetchError: If a fetch of the alert via the API fails.
        """
        self.log.info(f'Fetching alerts: {ids}')
        results = []
        if max_workers:
            results = MultiThreadingHelper.multithread_it(
                max_workers,
                self.fetch,
                iterator=ids,
                fields=fields,
                tagged_text=tagged_text,
            )
        else:
            results = [self.fetch(id_, fields, tagged_text) for id_ in ids]

        return results

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=AlertFetchError)
    def fetch_hits(
        self,
        ids: Annotated[Union[str, list[str]], Doc('One or more alert IDs to fetch.')],
        tagged_text: Annotated[
            Optional[bool],
            Doc('Entities in the alert title and message body will be marked up with entity IDs.'),
        ] = None,
    ) -> Annotated[list[ClassicAlertHit], Doc('List of ClassicAlertHit models.')]:
        """Fetch a list of all the data that caused the alert to trigger (hits).

        Endpoint:
            `v3/alerts/hits`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            AlertFetchError: If a fetch of the alert hit via the API fails.
        """
        data = {}

        if isinstance(ids, list):
            ids = ','.join(ids)

        data['ids'] = ids

        if tagged_text:
            data['taggedText'] = tagged_text

        self.log.info(f'Fetching hits for alerts: {ids}')
        response = self.rf_client.request('get', url=EP_CLASSIC_ALERTS_HITS, params=data).json()
        return [ClassicAlertHit.model_validate(hit) for hit in response.get('data', [])]

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=AlertImageFetchError)
    def fetch_image(
        self,
        id_: Annotated[
            str, Doc('Image ID to fetch, for example: img:d4620c6a-c789-48aa-b652-b47e0d06d91a')
        ],
    ) -> Annotated[bytes, Doc('Image content.')]:
        """Fetch an image.

        Endpoint:
            `v3/alerts/image`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            AlertImageFetchError: If a fetch of the alert image via the API fails.
        """
        self.log.info(f'Fetching image: {id_}')
        response = self.rf_client.request('get', url=EP_CLASSIC_ALERTS_IMAGE, params={'id': id_})
        return response.content

    @debug_call
    @validate_call
    def fetch_all_images(
        self,
        alert: Annotated[ClassicAlert, Doc('Alert to fetch images from.')],
    ) -> None:
        """Fetch all images from an alert and store them in the alert object under `@images`.

        Endpoint:
            `v3/alerts/image`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
        """
        for hit in alert.hits:
            for entity in hit.entities:
                if entity.type_ == 'Image':
                    alert.store_image(entity.id_, self.fetch_image(entity.id_))

    @debug_call
    @validate_call
    def fetch_rules(
        self,
        freetext: Annotated[
            Union[str, list[str], None], Doc('Filter by a freetext search.')
        ] = None,
        max_results: Annotated[
            int, Doc('Maximum number of rules to return. Maximum 1000.')
        ] = Field(default=DEFAULT_LIMIT, ge=1, le=1000),
    ) -> Annotated[list[AlertRuleOut], Doc('List of AlertRule models.')]:
        """Search for alerting rules.

        Endpoint:
            `v2/alert/rules`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type or value.
            NoRulesFoundError: If a rule has not been found.
        """
        if not freetext:
            return self._fetch_rules(max_results=max_results)

        if isinstance(freetext, str):
            return self._fetch_rules(freetext, max_results)

        rules = []
        for text in freetext:
            rules += self._fetch_rules(text, max_results - len(rules))
        return rules

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=AlertUpdateError)
    def update(
        self,
        updates: Annotated[list[dict], Doc('List of updates to perform.')],
    ):
        """Update one or more alerts.

        It is possible to update the assignee, `statusInPortal`, and a note tied to the alert.

        Example:
            ```python
            [
                {
                    "id": "string",
                    "assignee": "string",
                    "status": "unassigned",
                    "note": "string",
                    "statusInPortal": "New"
                }
            ]
            ```

        Endpoint:
            `v2/alert/update`
        """
        self.log.info(f'Updating alerts: {updates}')
        return self.rf_client.request('post', url=EP_CLASSIC_ALERTS_UPDATE, data=updates).json()

    @debug_call
    @validate_call
    def update_status(
        self,
        ids: Annotated[Union[str, list[str]], Doc('One or more alert IDs.')],
        status: Annotated[str, Doc('Status to update to.')],
    ):
        """Update the status of one or several alerts.

        Endpoint:
            `v2/alert/update`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            AlertUpdateError: If connection error occurs.
        """
        ids = ids if isinstance(ids, list) else ids.split(',')
        payload = [{'id': alert_id, 'statusInPortal': status} for alert_id in ids]
        return self.update(payload)

    @connection_exceptions(ignore_status_code=[], exception_to_raise=NoRulesFoundError)
    def _fetch_rules(
        self,
        freetext: Optional[str] = None,
        max_results: Optional[int] = Field(default=DEFAULT_LIMIT, ge=1, le=1000),
    ) -> list[AlertRuleOut]:
        data = {}

        if freetext:
            data['freetext'] = freetext

        data['limit'] = max_results or DEFAULT_LIMIT

        self.log.info(f'Fetching alert rules. Params: {data}')
        response = self.rf_client.request('get', url=EP_CLASSIC_ALERTS_RULES, params=data).json()

        return [
            AlertRuleOut.model_validate(rule)
            for rule in response.get('data', {}).get('results', [])
        ]

    def _search(
        self,
        rule_id: Optional[str] = None,
        *,
        triggered,
        status,
        freetext,
        tagged_text,
        order_by,
        direction,
        fields,
        max_results,
        alerts_per_page,
        **kwargs,  # noqa: ARG002
    ) -> list[ClassicAlert]:
        """rule_id is not a list anymore. We always receive a string. Kwargs is discarded."""
        params = {
            'triggered': triggered,
            'statusInPortal': status,
            'alertRule': rule_id,
            'freetext': freetext,
            'taggedText': tagged_text,
            'orderBy': order_by,
            'direction': direction,
            'fields': ','.join(set(fields + REQUIRED_CA_FIELDS)),
            'limit': min(max_results, alerts_per_page),
        }

        params = {k: v for k, v in params.items() if v}

        self.log.info(f'Searching for classic alerts. Params: {params}')
        search_results = self.rf_client.request_paged(
            method='get',
            url=EP_CLASSIC_ALERTS_SEARCH,
            params=params,
            offset_key='from',
            results_path='data',
            max_results=max_results,
        )
        return [ClassicAlert.model_validate(alert) for alert in search_results]

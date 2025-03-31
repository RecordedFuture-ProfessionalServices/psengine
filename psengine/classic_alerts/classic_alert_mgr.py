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
from typing import Optional, Union

from pydantic import Field, validate_call

from ..constants import DEFAULT_LIMIT
from ..endpoints import (
    EP_CLASSIC_ALERTS_HITS,
    EP_CLASSIC_ALERTS_ID,
    EP_CLASSIC_ALERTS_IMAGE,
    EP_CLASSIC_ALERTS_RULES,
    EP_CLASSIC_ALERTS_SEARCH,
    EP_CLASSIC_ALERTS_UPDATE,
)
from ..helpers import MultiThreadingHelper, debug_call
from ..helpers.helpers import connection_exceptions
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
            rf_token (str, optional): Recorded Future API token. Defaults to None
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=AlertSearchError)
    def search(
        self,
        triggered: Optional[str] = None,
        status: Optional[str] = None,
        rule_id: Union[str, list[str], None] = None,
        freetext: Optional[str] = None,
        tagged_text: Optional[bool] = None,
        order_by: Optional[str] = None,
        direction: Optional[str] = None,
        fields: Optional[list[str]] = REQUIRED_CA_FIELDS,
        max_results: Optional[int] = Field(ge=1, le=1000, default=DEFAULT_LIMIT),
        max_workers: Optional[int] = Field(ge=0, le=50, default=0),
        alerts_per_page: Optional[int] = Field(ge=1, le=1000, default=ALERTS_PER_PAGE),
    ) -> list[ClassicAlert]:
        """Search for triggered alerts.

        Does pagination requests on batches of ``alerts_per_page`` up to ``max_results``.

        Note, paginating for a high number of items per page, might lead to timeout errors from the
        API.

        The fields 'id', 'log', 'title', 'rule' are always retrieved.

        Endpoint:
            ``v3/alerts/``

        Args:
            triggered (str): filter on triggered time. Format: -1d or [2017-07-30,2017-07-31]
            status (str): filter on status, such as: 'New', 'Resolved', 'Pending', 'Dismissed'
            rule_id (str, list[str]): filter by a specific Alert Rule ID
            freetext (str): filter by a freetext search
            max_results (int): maximum number of records to return. Default 10, Maximum 1000
            tagged_text (bool): entities in the alert title and message body will be marked up
            order_by (str): sort by a specific field, such as: 'triggered'
            direction (str): sort direction, such as: 'asc' or 'desc'
            fields (List[str]): By default the search will fetch only these fields:
                'id', 'log', 'title', 'rule'. If a user specifies a list of fields, the search
                will use the specified fields + the default fields.
            max_workers (int, Optional): Number of workers to use for concurrent fetches. Only
                applied when more ``rule_id`` are provided.
            alerts_per_page (int, Optional): Number of items to retrieve in for each page.
                Defaults to 50.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            AlertSearchError: if connection error occurs.

        Returns:
             List[ClassicAlert]: List of ClassicAlert models
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

        elif isinstance(rule_id, list):
            return list(chain.from_iterable(self._search(rule, **params) for rule in rule_id))

        elif isinstance(rule_id, str):
            return self._search(rule_id, **params)
        else:
            return self._search(**params)

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=AlertFetchError)
    def fetch(
        self,
        id_: str,
        fields: Optional[list[str]] = ALL_CA_FIELDS,
        tagged_text: Optional[bool] = None,
    ) -> ClassicAlert:
        """Fetch a specific alert.

        The alert can be saved on file as shown below:

            .. code-block:: python
                :linenos:

                from pathlib import Path
                from json import dumps
                from psengine.classic_alerts import ClassicAlertMgr

                mgr = ClassicAlertMgr()
                alert = mgr.fetch('zVEe6k')
                OUTPUT_DIR = Path('your' / 'path')
                OUTPUT_DIR.mkdir(exists_ok=True)
                (OUTPUT_DIR / f'{alert.id_}.json').write_text(dumps(alert.json(), indent=2))

        Endpoint:
            ``v3/alerts/{id_}``

        Args:
            id_ (str): alertID that should be fetched
            fields (List[str]): by default, all fields are returned; but if only a subset of
                the alert details needed, this parameter can be used to limit which sections
                of the alert details are returned in the API response. If a user specifies a list
                of fields, the fetch will use the specified fields + the default fields required
                by the ADT ['id', 'log', 'title', 'rule'].
            tagged_text (bool): entities in the alert title and message body will be marked up
                with Recorded Future entity IDs

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            AlertFetchError: if a fetch of the alert via API function fails.

        Returns:
            ClassicAlert: ClassicAlert model
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
        ids: list[str],
        fields: Optional[list[str]] = ALL_CA_FIELDS,
        tagged_text: Optional[bool] = None,
        max_workers: Optional[int] = 0,
    ) -> list[ClassicAlert]:
        """Fetch multiple alerts.

        Example:
            Each alert can be saved on file as shown below:

            .. code-block:: python
                :linenos:

                from json import dumps
                from pathlib import Path
                from ..helpers import dump_models
                from psengine.classic_alerts import ClassicAlertMgr

                mgr = ClassicAlertMgr()
                alerts = mgr.fetch_bulk(ids=['zVEe6k', 'zVHPXX'])
                OUTPUT_DIR = Path('your/path')
                OUTPUT_DIR.mkdir(exists_ok=True)
                for i, alert in enumerate(alerts):
                    (OUTPUT_DIR / f'filename_{i}.json').write_text(dumps(alert.json(), indent=2))

            Alternatively all alerts can be saved on a single file:

            .. code-block:: python
                :linenos:

                from json import dump
                from pathlib import Path
                from psengine.classic_alerts import ClassicAlertMgr
                from ..helpers import dump_models

                mgr = ClassicAlertMgr()
                OUTPUT_FILE = Path('your/path/file')
                alerts = mgr.fetch_bulk(ids=['zVEe6k', 'zVHPXX'])
                with OUTPUT_FILE.open('w') as f:
                    dump([alert.json() for alert in alerts], f, indent=2)

        Endpoint:
            ``v3/alerts/{id_}``

        Args:
            ids (List[str]): alert IDs that should be fetched
            fields (List[str]): by default, all fields are returned; but if only a subset of
                the alert details needed, this parameter can be used to limit which sections
                of the alert details are returned in the API response
            tagged_text (bool): entities in the alert title and message body will be marked up
                with Recorded Future entity IDs
            max_workers (int, optional): number of workers to multithread requests.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            AlertFetchError: if a fetch of the alert via API function fails.

        Returns:
            List[ClassicAlert]: List of ClassicAlert model
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
        self, ids: Union[str, list[str]], tagged_text: Optional[bool] = None
    ) -> list[ClassicAlertHit]:
        """Fetch only a list of all the data that caused the alert to trigger (hits).

        Endpoint:
            ``v3/alerts/hits``

        Args:
            ids (Union[str, List[str]]): one or more alert ids to fetch
            tagged_text (bool): entities in the alert title and message body will be marked up
                with Recorded Future entity IDs

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            AlertFetchError: if a fetch of the alert hit via API function fails.

        Returns:
            List[ClassicAlertHit]: List of ClassicAlertHit models
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
    def fetch_image(self, id_: str) -> bytes:
        """Fetch an image.

        Endpoint:
            ``v3/alerts/image``

        Args:
            id_ (str): image id to fetch, for example: img:d4620c6a-c789-48aa-b652-b47e0d06d91a

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            AlertImageFetchError: if a fetch of the alert image via API function fails.

        Returns:
            bytes: image content
        """
        self.log.info(f'Fetching image: {id_}')
        response = self.rf_client.request('get', url=EP_CLASSIC_ALERTS_IMAGE, params={'id': id_})
        return response.content

    @debug_call
    @validate_call
    def fetch_all_images(self, alert: ClassicAlert) -> None:
        """Fetch all images from an alert and stores them in the alert object under ``@images``.

        Endpoint:
            ``v3/alerts/image``

        Args:
            alert (ClassicAlert): alert to fetch images from

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
        """
        for hit in alert.hits:
            for entity in hit.entities:
                if entity.type_ == 'Image':
                    alert.store_image(entity.id_, self.fetch_image(entity.id_))

    @debug_call
    @validate_call
    def fetch_rules(
        self,
        freetext: Union[str, list[str], None] = None,
        max_results: int = Field(default=DEFAULT_LIMIT, ge=1, le=1000),
    ) -> list[AlertRuleOut]:
        """Search for alerting rules.

        Endpoint:
            ``v2/alert/rules``

        Args:
            freetext (Union[str, list[str]], optional): filter by a freetext search, can be a
                a freetext string or a list of strings. Default None (will return all rules)
            max_results (int): maximum number of rules to return. Default 10, maximum 1000

        Raises:
            ValidationError if any supplied parameter is of incorrect type or value
            NoRulesFoundError: if rule has not been found.

        Returns:
            List[AlertRule]: List of AlertRule models
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
    def update(self, updates: list[dict]):
        """Updates one or more alerts. It's possible to update assignee, ``statusInPortal`` and a
        note tied to the triggered alert.

        Example:
            updates argument:

            .. code-block:: python

                [
                    {
                        "id": "string",
                        "assignee": "string",
                        "status": "unassigned",
                        "note": "string",
                        "statusInPortal": "New"
                    }
                ]

        Endpoint:
            ``v2/alert/update``

        Args:
            updates (List[dict]): list of updates to perform

        Returns:
            JSON response
        """
        self.log.info(f'Updating alerts: {updates}')
        response = self.rf_client.request('post', url=EP_CLASSIC_ALERTS_UPDATE, data=updates).json()
        return response

    @debug_call
    @validate_call
    def update_status(self, ids: Union[str, list[str]], status: str):
        """Update the status of one or several alerts.

        Endpoint:
            ``v2/alert/update``

        Args:
            ids (Union[str, List[str]]): one or more alert ids
            status (str): status to update to

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            AlertUpdateError: if connection error occurs.

        Returns:
            JSON response
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

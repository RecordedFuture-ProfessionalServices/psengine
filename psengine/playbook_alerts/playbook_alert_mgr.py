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

import pydantic
import requests
from more_itertools import batched
from pydantic import Field, validate_call

from ..constants import DEFAULT_LIMIT
from ..endpoints import (
    EP_PLAYBOOK_ALERT,
    EP_PLAYBOOK_ALERT_COMMON,
    EP_PLAYBOOK_ALERT_SEARCH,
)
from ..helpers import TimeHelpers, connection_exceptions, debug_call
from ..rf_client import RFClient
from .constants import (
    ALERTS_PER_PAGE,
    BULK_LOOKUP_BATCH_SIZE,
    PBA_WITH_IMAGES_INST,
    PBA_WITH_IMAGES_TYPE,
    PBA_WITH_IMAGES_VALIDATOR,
    PLAYBOOK_ALERT_INST,
    PLAYBOOK_ALERT_TYPE,
    STATUS_PANEL_NAME,
)
from .errors import (
    PlaybookAlertBulkFetchError,
    PlaybookAlertFetchError,
    PlaybookAlertRetrieveImageError,
    PlaybookAlertSearchError,
    PlaybookAlertUpdateError,
)
from .mappings import CATEGORY_ENDPOINTS, CATEGORY_TO_OBJECT_MAP
from .models import SearchResponse
from .pa_category import PACategory
from .playbook_alerts import (
    PreviewAlertOut,
    SearchIn,
    UpdateAlertIn,
)


class PlaybookAlertMgr:
    """Manages requests for Recorded Future playbook alerts."""

    def __init__(self, rf_token: str = None):
        """Initializes the PlaybookAlertMgr object.

        Args:
            rf_token (str, optional): Recorded Future API token. Defaults to None
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token is not None else RFClient()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=PlaybookAlertFetchError)
    def fetch(
        self,
        alert_id: str,
        category: Optional[PACategory] = None,
        panels: Optional[list[str]] = None,
        fetch_images: Optional[bool] = True,
    ) -> PLAYBOOK_ALERT_TYPE:
        """Fetch an individual Playbook Alert.

        Endpoints:
            - ``playbook-alert/{category}``
            - ``playbook-alert/common/{alert_id}``

        Args:
            alert_id (str): Alert ID to fetch.
            category (Optional[PACategory]): Category to fetch. When this is not supplied,
                fetch uses ``playbook-alert/common`` to find the alert category. Defaults to None.
            panels (Optional[List[str]]): Panels to fetch. The ``status`` panel is always fetched,
                to correctly initialize ADTs. Defaults to None (all).
            fetch_images (Optional[bool]): Fetch images for Domain Abuse & Geopol alerts.
                Defaults to True.

        Raises:
            ValidationError: If any parameter is of incorrect type.
            PlaybookAlertFetchError: If an API-related error occurs.

        Returns:
            PBA ADT (PLAYBOOK_ALERT_TYPE): Any one of the playbook alert ADTs
        """
        if category is None:
            category = self._fetch_alert_category(alert_id)

        category = category.lower()

        data = {}
        if panels:
            # We must always fetch status panel for ADT initialization
            if STATUS_PANEL_NAME not in panels:
                panels.append(STATUS_PANEL_NAME)
            data = {'panels': panels}

        url = f'{CATEGORY_ENDPOINTS[category]}/{alert_id}'
        self.log.info(f'Fetching playbook alert: {alert_id}, category: {category}')

        response = self.rf_client.request('post', url=url, data=data)
        p_alert = self._playbook_alert_factory(category, response.json()['data'])

        if isinstance(p_alert, PBA_WITH_IMAGES_INST) and fetch_images:
            self.fetch_images(p_alert)

        return p_alert

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=PlaybookAlertFetchError)
    def fetch_bulk(
        self,
        alerts: Optional[list[tuple[str, PACategory]]] = None,
        panels: Optional[list[str]] = None,
        fetch_images: Optional[bool] = False,
        alerts_per_page: Optional[int] = Field(ge=1, le=10000, default=ALERTS_PER_PAGE),
        max_results: Optional[int] = DEFAULT_LIMIT,
        order_by: Optional[str] = None,
        direction: Optional[str] = None,
        entity: Union[str, list, None] = None,
        statuses: Union[str, list, None] = None,
        priority: Union[str, list, None] = None,
        category: Union[PACategory, list[PACategory], None] = None,
        assignee: Union[str, list, None] = None,
        created_from: Optional[str] = None,
        created_until: Optional[str] = None,
        updated_from: Optional[str] = None,
        updated_until: Optional[str] = None,
    ) -> list[PLAYBOOK_ALERT_TYPE]:
        """Fetch multiple playbook alerts in bulk, either by search query or by specifying alert IDs
        and categories.

        Endpoints:
            - ``playbook-alert/search``
            - ``playbook-alert/{category}/{alert_id}``

        Args:
            alerts (Optional[list[tuple[str, str]]]): List of (alert_id, category) tuples to fetch
                directly. If provided, all other search parameters are ignored. Defaults to None.
            panels (Optional[list[str]]): List of panels to fetch for each alert. The ``status``
                panel is always fetched. Defaults to None (fetches all panels).
            fetch_images (Optional[bool]): Whether to fetch images for supported alert types.
                Defaults to False.
            alerts_per_page (Optional[int]): Number of alerts to retrieve per page (pagination).
                Defaults to 50.
            max_results (Optional[int]): Maximum total number of alerts to fetch. Defaults to 10.
            order_by (Optional[str]): Field to order alerts by, e.g. ``created`` or ``updated``.
            direction (Optional[str]): Sort direction, either ``asc`` or ``desc``.
            entity (Union[str, list, None]): Entity or list of entities to filter alerts by.
            statuses (Union[str, list, None]): Status or list of statuses to filter alerts by,
                e.g. ``['New', 'InProgress']``.
            priority (Union[str, list, None]): Priority or list of priorities to filter alerts
                by, e.g. ``['High', 'Informational']``.
            category (Union[PACategory, list[PACategory], None]): Category or list of
                categories to filter alerts by.
            assignee (Union[str, list, None]): Assignee or list of assignee uhashes to filter
                alerts by.
            created_from (Optional[str]): Start of created date range (ISO or relative,
                e.g. ``-3d`` or ``2023-07-21T17:32:28Z``).
            created_until (Optional[str]): End of created date range (ISO or relative).
            updated_from (Optional[str]): Start of updated date range (ISO or relative).
            updated_until (Optional[str]): End of updated date range (ISO or relative).

        Raises:
            ValidationError: If any parameter is of incorrect type.
            PlaybookAlertFetchError: If a connection or API error occurs.

        Returns:
            list[PLAYBOOK_ALERT_TYPE]: List of playbook alert ADT matching the query or IDs.
        """
        query_params = locals()
        for param in ['self', 'alerts', 'panels', 'fetch_images']:
            query_params.pop(param)
        if alerts is None:
            search_result = self.search(**query_params)
            alerts = [
                {'id': x.playbook_alert_id, 'category': x.category} for x in search_result.data
            ]
        else:
            alerts = [{'id': x[0], 'category': x[1]} for x in alerts]

        fetched_alerts = []
        errors = 0
        for cat in {x['category'] for x in alerts}:
            in_cat_alerts = filter(lambda x: x['category'] == cat, alerts)
            in_cat_ids = [x['id'] for x in in_cat_alerts]
            try:
                fetched_alerts.extend(self._do_bulk(in_cat_ids, cat, fetch_images, panels or []))
            except (PlaybookAlertBulkFetchError, PlaybookAlertRetrieveImageError) as err:  # noqa: PERF203
                errors += 1
                self.log.error(err)

        if errors:
            self.log.error(f'Failed to fetch alerts due to {errors} error(s). See errors above')
            raise PlaybookAlertFetchError('Failed to fetch alerts')

        return fetched_alerts

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=PlaybookAlertSearchError)
    def search(
        self,
        alerts_per_page: Optional[int] = Field(ge=1, le=10000, default=ALERTS_PER_PAGE),
        max_results: Optional[int] = DEFAULT_LIMIT,
        order_by: Optional[str] = None,
        direction: Optional[str] = None,
        entity: Union[str, list, None] = None,
        statuses: Union[str, list, None] = None,
        priority: Union[str, list, None] = None,
        category: Union[PACategory, list[PACategory], None] = None,
        assignee: Union[str, list, None] = None,
        created_from: Optional[str] = None,
        created_until: Optional[str] = None,
        updated_from: Optional[str] = None,
        updated_until: Optional[str] = None,
    ) -> SearchResponse:
        """Search for playbook alerts using various filters.

        Endpoint:
            - ``playbook-alert/search``

        Args:
            alerts_per_page (Optional[int]): Number of alerts per page. Defaults to 50.
            max_results (Optional[int]): Maximum total alerts to fetch. Defaults to 10.
            order_by (Optional[str]): Field to order alerts by, e.g. 'created' or 'updated'.
            direction (Optional[str]): Sort direction, 'asc' or 'desc'.
            entity (Union[str, list, None]): Entity or list of entities to filter by.
            statuses (Union[str, list, None]): Status or list of statuses to filter by.
            priority (Union[str, list, None]): Priority or list of priorities to filter by.
            category (Union[PACategory, list[PACategory], None]): Category/ies to filter by.
            assignee (Union[str, list, None]): Assignee or list of assignees to filter by.
            created_from (Optional[str]): Start of created date range (ISO or relative).
            created_until (Optional[str]): End of created date range (ISO or relative).
            updated_from (Optional[str]): Start of updated date range (ISO or relative).
            updated_until (Optional[str]): End of updated date range (ISO or relative).

        Raises:
            ValidationError: If any parameter is of incorrect type.
            PlaybookAlertSearchError: If a connection or API error occurs.

        Returns:
            SearchResponse: Search results matching the query.
        """
        query_params = locals()
        query_params.pop('self')
        request_body = self._prepare_query(**query_params).json()
        self.log.info(
            f'Searching for playbook alert query: {request_body}, max_results: {max_results}'
        )

        search_results = self.rf_client.request_paged(
            method='post',
            url=EP_PLAYBOOK_ALERT_SEARCH,
            data=request_body,
            max_results=max_results,
            results_path='data',
            offset_key='from',
        )

        # To avoid a breaking change have to reconstruct the SearchResponse model manually
        # We did lost the total count the API "could" return
        result = {
            'status': {'status_code': 'Ok', 'status_message': 'Playbook alert search successful'},
            'data': search_results,
            'counts': {'returned': len(search_results), 'total': len(search_results)},
        }

        self.log.info(f'Search returned {len(search_results)} playbook alerts')

        return SearchResponse.model_validate(result)

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=PlaybookAlertUpdateError)
    def update(
        self,
        alert: Union[PLAYBOOK_ALERT_TYPE, str],
        priority: Optional[str] = None,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        log_entry: Optional[str] = None,
        reopen_strategy: Optional[str] = None,
    ) -> requests.Response:
        """Update a playbook alert.

        Endpoints:
            ``playbook-alert/common/{playbook_alert_id}``

        Args:
            alert (Union[PLAYBOOK_ALERT_TYPE, str]): Playbook alert ADT or alert ID to update
            priority (str, optional): Alert priority. Defaults to None
            status (str, optional): Alert Status. Defaults to None
            assignee (str, optional): Assignee. Defaults to None
            log_entry (str, optional): Log entry. Defaults to None
            reopen_strategy (str, optional): Reopen strategy. Defaults to None

        Raises:
            ValidationError if any parameter is of incorrect type
            ValueError: If no update parameters are supplied
            PlaybookAlertUpdateError: If the update request fails

        Returns:
            requests.Response: API response
        """
        body = {
            'priority': priority,
            'status': status,
            'assignee': assignee,
            'log_entry': log_entry,
            'reopen': reopen_strategy,
        }

        body = {k: v for k, v in body.items() if v is not None}
        if not body:
            raise ValueError('No update parameters were supplied')

        alert_id = alert.playbook_alert_id if isinstance(alert, PLAYBOOK_ALERT_INST) else alert
        validated_payload = UpdateAlertIn.model_validate(body)

        url = f'{EP_PLAYBOOK_ALERT_COMMON}/{alert_id}'
        self.log.info(f'Updating playbook alert: {alert_id}')

        return self.rf_client.request('put', url=url, data=validated_payload.json())

    @debug_call
    @validate_call
    def _prepare_query(
        self,
        alerts_per_page: Optional[int] = ALERTS_PER_PAGE,
        max_results: Optional[int] = DEFAULT_LIMIT,
        order_by: Optional[str] = None,
        direction: Optional[str] = None,
        entity: Union[str, list, None] = None,
        statuses: Union[str, list, None] = None,
        priority: Union[str, list, None] = None,
        category: Union[str, list, None] = None,
        assignee: Union[str, list, None] = None,
        created_from: Optional[str] = None,
        created_until: Optional[str] = None,
        updated_from: Optional[str] = None,
        updated_until: Optional[str] = None,
    ) -> SearchIn:
        """Create a query for searching playbook alerts.

        See search() and fetch_bulk() for parameter descriptions.

        Raises:
            ValidationError if any parameter is of incorrect type

        Returns:
            SearchIn: Validated search query
        """
        params = {key: val for key, val in locals().items() if val and key != 'self'}
        query = {
            'created_range': {},
            'updated_range': {},
            'limit': min(max_results, alerts_per_page),
        }

        # If no category is specified by the caller,
        # restrict the search to only the supported categories
        if not category:
            query['category'] = [cat.value for cat in PACategory]

        for arg in params:
            key, value = self._process_arg(arg, params[arg])
            if isinstance(value, dict):
                query[key].update(value)
            else:
                query[key] = value

        query = {
            key: val
            for key, val in query.items()
            if not ((isinstance(val, (dict, list))) and len(val) == 0)
        }

        return SearchIn.model_validate(query)

    @debug_call
    @validate_call
    @connection_exceptions(
        ignore_status_code=[], exception_to_raise=PlaybookAlertRetrieveImageError
    )
    def fetch_one_image(
        self,
        alert_id: str = None,
        image_id: str = None,
        alert_category: PBA_WITH_IMAGES_VALIDATOR = 'domain_abuse',
    ) -> bytes:
        """Retrieve image from playbook alert that have images.

        Endpoints:
            ``playbook-alert/domain_abuse/{alert_id}/image/{image_id}``
            ``playbook-alert/geopolitics_facility/image/{image_id}``

        Args:
            alert_id (str): Alert ID for corresponding image ID
            image_id (str): Image ID to fetch
            alert_category (str): Category of the alert

        Raises:
            ValidationError: if any parameter is of incorrect type
            PlaybookAlertRetrieveImageError: If the image fetch fails

        Returns:
            bytes: Bytes of the image
        """
        if alert_category == PACategory.DOMAIN_ABUSE.value:
            url = f'/{alert_category}/{alert_id}/image/{image_id}'
        else:
            url = f'/{alert_category}/image/{image_id}'

        self.log.info(f'Retrieving image: {image_id} for alert: {alert_id}')
        response = self.rf_client.request('get', EP_PLAYBOOK_ALERT + url)

        return response.content

    @debug_call
    @validate_call
    @connection_exceptions(
        ignore_status_code=[], exception_to_raise=PlaybookAlertRetrieveImageError
    )
    def fetch_images(self, playbook_alert: PBA_WITH_IMAGES_TYPE) -> None:
        """Domain Abuse: Retrieve the associated images, if any available.

        Endpoint:
            ``playbook-alert/domain_abuse/{alert_id}/image/{image_id}``
            ``playbook-alert/geopolitics_facility/image/{image_id}``

        Examples:
            Search and fetch images of alerts:

                .. code-block:: python
                     :linenos:
                        from psengine.playbook_alerts import PlaybookAlertMgr, PBA_WITH_IMAGES_INST

                        mgr = PlaybookAlertMgr()
                        alerts = mgr.search()
                        alerts_to_fetch = [(a.playbook_alert_id, a.category) for a in alerts.data]

                        alerts_details = mgr.fetch_bulk(alerts_to_fetch)
                        retrieve_images_alerts = [
                            a for a in alerts_details if isinstance(a, PBA_WITH_IMAGES_INST)
                        ]

                        for alert in retrieve_images_alerts:
                            mgr.fetch_images(alert)
                            print(alert.images)

        Args:
            playbook_alert: ADT of an alert supporting images.

        Raises:
            ValidationError if any parameter is of incorrect type
            PlaybookAlertRetrieveImageError: if an API error occurs
        """
        for image_id in playbook_alert.image_ids:
            image_bytes = self.fetch_one_image(
                playbook_alert.playbook_alert_id, image_id, playbook_alert.category
            )
            playbook_alert.store_image(image_id, image_bytes)

    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=PlaybookAlertFetchError)
    def _fetch_alert_category(self, alert_id: str) -> PACategory:
        """Fetch the alert category based on the alert ID.

        Endpoints:
            ``playbook-alert/common/{alert_id}``

        Args:
            alert_id (str): Alert ID

        Returns:
            RFPACategory: Alert category
        """
        endpoint = EP_PLAYBOOK_ALERT_COMMON + '/' + alert_id
        result = self.rf_client.request('get', endpoint).json()['data']
        validated_alert_info = PreviewAlertOut.model_validate(result)

        try:
            return PACategory(validated_alert_info.category)
        except ValueError as v:
            raise ValueError(
                f'Unsupported playbook alert category(s): {validated_alert_info.category}. '
                f'Supported: {list(CATEGORY_ENDPOINTS.keys())}'
            ) from v

    @debug_call
    def _playbook_alert_factory(
        self,
        category: str,
        raw_alert: dict,
    ) -> PLAYBOOK_ALERT_TYPE:
        """Return correct playbook alert type from raw alert and category.

        Args:
            category (string): Alert category
            raw_alert (dict): Raw alert payload

        Returns:
            Playbook Alert ADT
        """
        p_alert = None
        try:
            p_alert = CATEGORY_TO_OBJECT_MAP[category].model_validate(raw_alert)
        except pydantic.ValidationError as ve:
            self.log.error(
                'Error validating playbook alert {}'.format(raw_alert['playbook_alert_id'])
            )
            for error in ve.errors():
                self.log.error('{} at location: {}'.format(error['msg'], error['loc']))
            raise

        return p_alert

    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=PlaybookAlertBulkFetchError)
    def _do_bulk(
        self, alert_ids: list, category: str, fetch_image: bool, panels: list
    ) -> list[PLAYBOOK_ALERT_TYPE]:
        """Does bulk fetch (used by bulk() after alert IDs have been sorted by category).

        Args:
            alert_ids (list): List of alert IDs to fetch
            category (str): Category of alert to fetch
            fetch_image (bool): Whether to fetch images for Domain Abuse alerts
            panels (list): List of panels to fetch

        Raises:
            ValidationError if any supplied parameter is of incorrect type
            PlaybookAlertBulkFetchError if connection error occurs

        Returns:
            list: Playbook alert ADTs. Unknown alert types return PBA_Generic
        """
        category = category.lower()

        data = {}
        if panels:
            # We must always fetch status panel for ADT initialization
            if STATUS_PANEL_NAME not in panels:
                panels.append(STATUS_PANEL_NAME)
            data = {'panels': panels}

        self.log.info(f'Fetching {len(alert_ids)} {category} alerts')

        results = []
        for batch in batched(alert_ids, BULK_LOOKUP_BATCH_SIZE):
            data['playbook_alert_ids'] = batch
            response = self.rf_client.request('post', url=CATEGORY_ENDPOINTS[category], data=data)
            results += response.json()['data']

        p_alerts = [self._playbook_alert_factory(category, raw_alert) for raw_alert in results]

        if (
            category == PACategory.DOMAIN_ABUSE.value
            or category == PACategory.GEOPOLITICS_FACILITY.value
        ) and fetch_image:
            for alert in p_alerts:
                self.fetch_images(alert)

        return p_alerts

    def _process_arg(
        self,
        attr: str,
        value: Union[int, str, list],
    ) -> tuple[str, Union[str, list]]:
        """Return attribute and value normalized based on type of value.

        Args:
            attr (str): Attribute to verify
            value (Union[str, list]): Value of attribute

        Returns:
            tuple (str, Union[str, list]): canonicalized query attributes
        """
        list_or_str_args = ['entity', 'statuses', 'priority', 'category', 'assignee']
        if attr in ['created_from', 'created_until', 'updated_from', 'updated_until']:
            range_field = attr.split('_')[0] + '_range'
            query_key = 'from' if attr.endswith('from') else 'until'
            if TimeHelpers.is_rel_time_valid(value):
                return range_field, {query_key: TimeHelpers.rel_time_to_date(value)}
            return range_field, {query_key: value}
        if attr in list_or_str_args and isinstance(value, str):
            return attr, [value]

        return attr, value

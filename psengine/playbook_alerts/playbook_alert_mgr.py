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
from pathlib import Path
from typing import Optional, Union

import pydantic
import requests
from more_itertools import batched
from pydantic import validate_call

from ..constants import DEFAULT_LIMIT, ROOT_DIR
from ..endpoints import (
    EP_PLAYBOOK_ALERT,
    EP_PLAYBOOK_ALERT_COMMON,
    EP_PLAYBOOK_ALERT_DOMAIN_ABUSE,
    EP_PLAYBOOK_ALERT_SEARCH,
)
from ..helpers import TimeHelpers, connection_exceptions, debug_call
from ..rf_client import RFClient
from .constants import PLAYBOOK_ALERT_TYPE, STATUS_PANEL_NAME
from .errors import (
    PlaybookAlertFetchError,
    PlaybookAlertRetrieveImageError,
    PlaybookAlertSearchError,
    PlaybookAlertUpdateError,
)
from .mappings import CATEGORY_ENDPOINTS, CATEGORY_TO_OBJECT_MAP
from .models import SearchResponse
from .pa_category import PACategory
from .playbook_alerts import (
    LookupAlertIn,
    PBA_DomainAbuse,
    PBA_Generic,
    PreviewAlertOut,
    SearchIn,
    UpdateAlertIn,
)

BULK_LOOKUP_BATCH_SIZE = 200

DEFAULT_ALERTS_OUTPUT_DIR = Path(ROOT_DIR) / 'playbook_alerts'
PLAYBOOK_ALERTS_OUTPUT_FNAME = 'rf_playbook_alerts_'


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
        category: Optional[str] = None,
        panels: Optional[list[str]] = None,
        fetch_images: Optional[bool] = True,
    ) -> PLAYBOOK_ALERT_TYPE:
        """Fetch an individual Playbook Alert.

        Endpoints:

            - ``playbook-alert/{category}``
            - ``playbook-alert/common/{alert_id}``

        Args:
            alert_id (str): Alert ID to fetch
            category (Optional[PACategory], optional): Category to fetch. When this is not supplied,
                                                       fetch uses ``playbook-alert/common`` to find
                                                       the alert category. Defaults to None
            panels (Optional[List[str]]): Panels to fetch. The ``status`` panel is always fetched,
                                          to correctly initialize ADTs. Defaults to None (all)
            fetch_images (Optional[bool]): Fetch images for Domain Abuse alerts. Defaults to True

        Raises:
            ValidationError if any parameter is of incorrect type
            PlaybookAlertFetchError: if an API-related error occurs

        Returns:
            PBA ADT: Any one of the playbook alert ADTs. Unknown alert types return PBA_Generic
        """
        if category is None:
            category = self._fetch_alert_category(alert_id)

        category = category.lower()
        if category in CATEGORY_ENDPOINTS:
            endpoint = CATEGORY_ENDPOINTS[category]
        else:
            # Workaround to fetch new PAs that have not been officially supported
            self.log.warning(
                f'Unknown playbook alert category: {category}, for alert: {alert_id}. '
                'Using category as an endpoint for this lookup'
            )
            endpoint = f'{EP_PLAYBOOK_ALERT}/{category}'

        data = {}
        if panels:
            # We must always fetch status panel for ADT initialization
            panels = panels.append(STATUS_PANEL_NAME) if STATUS_PANEL_NAME not in panels else panels
            data = {'panels': panels}
        request_data = LookupAlertIn.model_validate(data)

        url = f'{endpoint}/{alert_id}'
        self.log.info(f'Fetching playbook alert: {alert_id}, category: {category}')
        response = self.rf_client.request('post', url=url, data=request_data.json())
        p_alert = self._playbook_alert_factory(category, response.json()['data'])

        if isinstance(p_alert, PBA_DomainAbuse) and fetch_images:
            self.fetch_images(p_alert)

        return p_alert

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=PlaybookAlertFetchError)
    def fetch_bulk(
        self,
        alerts: Optional[list[tuple[str, str]]] = None,
        panels: Optional[list] = None,
        fetch_images: Optional[bool] = False,
        filter_from: Optional[int] = 0,
        max_results: Optional[int] = DEFAULT_LIMIT,
        order_by: Optional[str] = None,
        direction: Optional[str] = None,
        entity: Optional[Union[str, list]] = None,
        statuses: Optional[Union[str, list]] = None,
        priority: Optional[Union[str, list]] = None,
        category: Optional[Union[str, list]] = None,
        assignee: Optional[Union[str, list]] = None,
        created_from: Optional[str] = None,
        created_until: Optional[str] = None,
        updated_from: Optional[str] = None,
        updated_until: Optional[str] = None,
    ) -> list[PLAYBOOK_ALERT_TYPE]:
        """Fetch alerts in bulk based on a search query.

        Endpoints:

            - ``playbook-alert/search``
            - ``playbook-alert/{category}/{alert_id}``

        Args:
            alerts (tuple, optional): Alert (id, category) tuples to fetch. If alerts are supplied,
                                      other search parameters (query, limit, statuses, category,
                                      priority, created, updated) are ignored. Defaults to None
            panels (list, optional): Panels to fetch. Always fetches status panel. Defaults to None
            fetch_images (bool, optional): Fetch images for Domain Abuse alerts. Defaults to True
            filter_from: (int, optional): Offset to page from. Defaults to 0
            max_results (int, optional): Maximum total number of alerts to fetch. Defaults to 10
            order_by (str, optional): Order alerts by field [created|updated]
            direction (str, optional): Direction to order alerts [asc|desc]
            entity (list, optional): List of entities to fetch alerts for
            statuses (list, optional): List of statuses to fetch e.g. ['New', 'InProgress']
            priority (list, optional): Priority of alerts to fetch e.g. ['High', 'Informational']
            category (list, optional): List of categories to fetch e.g. ['domain_abuse']
            assignee (list, optional): List of assignee uhashes to fetch alerts for
            created_from (str, optional): ISO or relative [h|d], e.g. -3d or 2023-07-21T17:32:28Z
            created_until (str, optional): ISO or relative [h|d], e.g. -3d or 2023-07-21T17:32:28Z
            updated_from (str, optional): ISO or relative [h|d], e.g. -3d or 2023-07-21T17:32:28Z
            updated_until (str, optional): ISO or relative [h|d], e.g. -3d or 2023-07-21T17:32:28Z

        Raises:
            ValidationError if any parameter is of incorrect type
            PlaybookAlertFetchError: if connection error occurs

        Returns:
            list: PlaybookAlert ADTs
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
            except PlaybookAlertFetchError as err:  # noqa: PERF203
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
        filter_from: Optional[int] = 0,
        max_results: Optional[int] = DEFAULT_LIMIT,
        order_by: Optional[str] = None,
        direction: Optional[str] = None,
        entity: Optional[Union[str, list]] = None,
        statuses: Optional[Union[str, list]] = None,
        priority: Optional[Union[str, list]] = None,
        category: Optional[Union[str, list]] = None,
        assignee: Optional[Union[str, list]] = None,
        created_from: Optional[str] = None,
        created_until: Optional[str] = None,
        updated_from: Optional[str] = None,
        updated_until: Optional[str] = None,
    ) -> SearchResponse:
        """Search playbook alerts.

        Endpoints:
            ``playbook-alert/search``

        Args:
            filter_from: (int, optional): Offset to page from. Defaults to 0
            max_results (int, optional): Maximum total number of alerts to fetch. Defaults to 10
            order_by (str, optional): Order alerts by field [created|updated]
            direction (str, optional): Direction to order alerts [asc|desc]
            entity (list, optional): List of entities to fetch alerts for
            statuses (list, optional): List of statuses to fetch e.g. ['New', 'InProgress']
            priority (list, optional): Priority of alerts to fetch e.g. ['High', 'Informational']
            category (list, optional): List of categories to fetch e.g. ['domain_abuse']
            assignee (list, optional): List of assignee uhashes to fetch alerts for
            created_from (str, optional): ISO or relative [h|d], e.g. -3d or 2023-07-21T17:32:28Z
            created_until (str, optional): ISO or relative [h|d], e.g. -3d or 2023-07-21T17:32:28Z
            updated_from (str, optional): ISO or relative [h|d], e.g. -3d or 2023-07-21T17:32:28Z
            updated_until (str, optional): ISO or relative [h|d], e.g. -3d or 2023-07-21T17:32:28Z

        Raises:
            ValidationError if any parameter is of incorrect type
            PlaybookAlertSearchError: if connection error occurs

        Returns:
            SearchResponse: Search results
        """
        query_params = locals()
        query_params.pop('self')
        request_body = self._prepare_query(**query_params).json()
        self.log.info(f'Searching for playbook alerts with params {request_body}')
        response = self.rf_client.request('post', EP_PLAYBOOK_ALERT_SEARCH, data=request_body)
        search_results = response.json()

        status_message = search_results.get('status', {}).get('status_message')
        count_returned = search_results.get('counts', {}).get('returned')
        count_total = search_results.get('counts', {}).get('total')
        self.log.info(
            'Status: {}, returned: {} {}, total: {} {}'.format(
                status_message,
                count_returned,
                'alert' if count_returned == 1 else 'alerts',
                count_total,
                'alert' if count_total == 1 else 'alerts',
            ),
        )

        return SearchResponse.model_validate(search_results)

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=PlaybookAlertUpdateError)
    def update(
        self,
        alert: PLAYBOOK_ALERT_TYPE,
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
            alert (BasePlaybookAlert): Playbook alert to update
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
        if (
            priority is None
            and status is None
            and assignee is None
            and log_entry is None
            and reopen_strategy is None
        ):
            raise ValueError('No update parameters were supplied')

        body = {}
        if priority is not None:
            body['priority'] = priority

        if status is not None:
            body['status'] = status

        if assignee is not None:
            body['assignee'] = assignee

        if log_entry is not None:
            body['log_entry'] = log_entry

        if reopen_strategy is not None:
            body['reopen'] = reopen_strategy

        alert_id = alert.playbook_alert_id
        validated_payload = UpdateAlertIn.model_validate(body)
        url = f'{EP_PLAYBOOK_ALERT_COMMON}/{alert_id}'
        self.log.info(f'Updating playbook alert: {alert_id}')
        response = self.rf_client.request('put', url=url, data=validated_payload.json())

        return response

    @debug_call
    @validate_call
    def _prepare_query(
        self,
        filter_from: Optional[int] = 0,
        max_results: Optional[int] = DEFAULT_LIMIT,
        order_by: Optional[str] = None,
        direction: Optional[str] = None,
        entity: Optional[Union[str, list]] = None,
        statuses: Optional[Union[str, list]] = None,
        priority: Optional[Union[str, list]] = None,
        category: Optional[Union[str, list]] = None,
        assignee: Optional[Union[str, list]] = None,
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

        query = {'created_range': {}, 'updated_range': {}}

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
    def fetch_one_image(self, alert_id: str, image_id: str) -> bytes:
        """Retrieve image from Domain Abuse playbook alert.

        Endpoints:
            ``playbook-alert/domain_abuse/{alert_id}/image/{image_id}``

        Args:
            alert_id (str): Alert ID for corresponding image ID
            image_id (str): Image ID to fetch

        Raises:
            ValidationError if any parameter is of incorrect type
            PlaybookAlertRetrieveImageError: If the image fetch fails

        Returns:
            bytes: Bytes of the image
        """
        url = f'{EP_PLAYBOOK_ALERT_DOMAIN_ABUSE}/{alert_id}/image/{image_id}'

        self.log.info(f'Retrieving image: {image_id} for alert: {alert_id}')
        response = self.rf_client.request('get', url)

        return response.content

    @debug_call
    @validate_call
    @connection_exceptions(
        ignore_status_code=[], exception_to_raise=PlaybookAlertRetrieveImageError
    )
    def fetch_images(self, playbook_alert: PBA_DomainAbuse) -> None:
        """Domain Abuse: Retrieve the associated images, if any available.

        Endpoint:
            ``playbook-alert/domain_abuse/{alert_id}/image/{image_id}``

        Args:
            playbook_alert (DomainAbuse): Domain Abuse Playbook Alert ADT

        Raises:
            ValidationError if any parameter is of incorrect type
            PlaybookAlertRetrieveImageError: if an API error occurs
        """
        if isinstance(playbook_alert, PBA_DomainAbuse):
            for image_id in playbook_alert.image_ids:
                image_bytes = self.fetch_one_image(playbook_alert.playbook_alert_id, image_id)
                playbook_alert.store_image(image_id, image_bytes)
        else:
            self.log.debug('Image fetching is only supported for Domain Abuse alerts')

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
        result = self.rf_client.request('get', endpoint)
        validated_alert_info = PreviewAlertOut.model_validate(result.json()['data'])

        return PACategory(validated_alert_info.category)

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
            try:
                p_alert = CATEGORY_TO_OBJECT_MAP[category].model_validate(raw_alert)
            except KeyError:
                # This way when we consume an unmapped(new) PA, we get a base object to work with
                self.log.warning(
                    f'Unmapped playbook alert category: {category}. '
                    + 'Will initialize {} as a BasePlaybookAlert'.format(
                        raw_alert['playbook_alert_id']
                    ),
                )
                p_alert = PBA_Generic.model_validate(raw_alert)
        except pydantic.ValidationError as validation_error:
            self.log.error(
                'Error validating playbook alert {}'.format(raw_alert['playbook_alert_id'])
            )
            for error in validation_error.errors():
                self.log.error('{} at location: {}'.format(error['msg'], error['loc']))
            raise

        return p_alert

    @validate_call
    @connection_exceptions(
        ignore_status_code=[], exception_to_raise=PlaybookAlertRetrieveImageError
    )
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
            PlaybookAlertRetrieveImageError: if connection error occurs

        Returns:
            list: Playbook alert ADTs. Unknown alert types return PBA_Generic
        """
        category = category.lower()
        if category in CATEGORY_ENDPOINTS:
            endpoint = CATEGORY_ENDPOINTS[category]
        else:
            # Workaround to fetch new PAs that have not been officially supported
            self.log.warning(
                f'Unknown playbook alert category: {category}.'
                'Using category as an endpoint for this lookup',
            )
            endpoint = f'{EP_PLAYBOOK_ALERT}/{category}'

        data = {}
        if panels:
            # We must always fetch status panel for ADT initialization
            panels = panels.append(STATUS_PANEL_NAME) if STATUS_PANEL_NAME not in panels else panels
            data = {'panels': panels}

        self.log.info(f'Fetching {len(alert_ids)} {category} alerts')

        results = []
        for batch in batched(alert_ids, BULK_LOOKUP_BATCH_SIZE):
            data['playbook_alert_ids'] = batch
            response = self.rf_client.request('post', url=endpoint, data=data)
            results += response.json()['data']

        p_alerts = [self._playbook_alert_factory(category, raw_alert) for raw_alert in results]

        if category == PACategory.DOMAIN_ABUSE.value and fetch_image:
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
        if attr == 'filter_from':
            return 'from', value
        elif attr in ['created_from', 'created_until', 'updated_from', 'updated_until']:
            range_field = attr.split('_')[0] + '_range'
            query_key = 'from' if attr.endswith('from') else 'until'
            if TimeHelpers.is_rel_time_valid(value):
                return range_field, {query_key: TimeHelpers.rel_time_to_date(value)}
            return range_field, {query_key: value}
        elif attr in list_or_str_args and isinstance(value, str):
            return attr, [value]
        elif attr == 'max_results':
            return 'limit', value

        return attr, value

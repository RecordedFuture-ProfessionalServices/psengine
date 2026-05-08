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
from ..endpoints import EP_CREATE_LIST, EP_LIST, EP_SEARCH_LIST
from ..entity_match import EntityMatchMgr
from ..helpers import debug_call
from ..helpers.helpers import connection_exceptions
from ..rf_client import RFClient
from .entity_list import EntityList
from .errors import ListApiError, ListResolutionError


class EntityListMgr:
    """Manages requests for Recorded Future List API."""

    def __init__(
        self,
        rf_token: Annotated[Optional[str], Doc('Recorded Future API token.')] = None,
    ) -> None:
        """Initialize the `EntityListMgr` object."""
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()
        self.match_mgr = EntityMatchMgr(rf_token=rf_token) if rf_token else EntityMatchMgr()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ListApiError)
    def fetch(
        self,
        list_: Annotated[
            Union[str, tuple[str, str]], Doc('List string ID or tuple of (name, type).')
        ],
    ) -> Annotated[EntityList, Doc('RFList object for the given list ID.')]:
        """Get a list by its ID. Use this method to retrieve list info.

        Endpoint:
            `list/{list_id}/info`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            ListResolutionError: When `list_` is a tuple and name matches zero or multiple entities.
            ListApiError: If connection error occurs.
        """
        resolved_id = self._resolve_list_id(list_)
        self.log.info(f'Getting list with ID: {resolved_id}')
        url = EP_LIST + f'/{resolved_id}/info'
        response = self.rf_client.request('get', url)
        list_info_data = response.json()
        self.log.debug("Found list ID '{}'".format(list_info_data['id']))
        self.log.debug('  Type: {}'.format(list_info_data['type']))
        self.log.debug('  Created: {}'.format(list_info_data['created']))
        self.log.debug('  Updated: {}'.format(list_info_data['updated']))

        return EntityList(rf_client=self.rf_client, match_mgr=self.match_mgr, **list_info_data)

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ListApiError)
    def create(
        self,
        list_name: Annotated[str, Doc('List name to use for the new list.')],
        list_type: Annotated[
            str, Doc('List type. Supported types are documented in the List API support page.')
        ] = 'entity',
    ) -> Annotated[EntityList, Doc('EntityList object for the new list.')]:
        """Create a new list.

        Endpoint:
            `list/create`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            ListApiError: If connection error occurs.
        """
        self.log.debug(f"Creating list '{list_name}'")
        request_body = {'name': list_name, 'type': list_type}
        response = self.rf_client.request('post', EP_CREATE_LIST, data=request_body)
        list_create_data = response.json()
        self.log.debug(f"List '{list_name}' created")
        self.log.debug('  ID: {}'.format(list_create_data['id']))
        self.log.debug('  Type: {}'.format(list_create_data['type']))

        return EntityList(rf_client=self.rf_client, match_mgr=self.match_mgr, **list_create_data)

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ListApiError)
    def search(
        self,
        list_name: Annotated[Optional[str], Doc('List name to search.')] = None,
        list_type: Annotated[Optional[str], Doc('List type to filter by. Ignored if None.')] = None,
        max_results: Annotated[int, Doc('Maximum number of lists to return.')] = DEFAULT_LIMIT,
    ) -> Annotated[list[EntityList], Doc('List of EntityList objects from `list/search`.')]:
        """Search lists.

        Endpoint:
            `list/search`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            ListApiError: If the list API call fails.
        """
        request_body = {}
        request_body['limit'] = max_results
        if list_name:
            request_body['name'] = list_name
        if list_type:
            request_body['type'] = list_type
        self.log.info(f'Searching list API with parameters: {request_body}')
        response = self.rf_client.request('post', EP_SEARCH_LIST, data=request_body)
        list_search_data = response.json()
        self.log.info(
            'Found {} matching {}'.format(
                len(list_search_data), 'lists' if len(list_search_data) != 1 else 'list'
            )
        )

        return [
            EntityList(rf_client=self.rf_client, match_mgr=self.match_mgr, **list_)
            for list_ in list_search_data
        ]

    @debug_call
    def _resolve_list_id(self, list_: Union[str, tuple[str, str]]) -> str:
        """Resolves a list name to a list ID.

        Args:
            list_ (str, tuple): list string ID or (name, type) tuple

        Raises:
            ListResolutionError: when a list name matches none or multiple entities

        Returns:
            str: list ID
        """
        if isinstance(list_, str):
            resolved_id = list_
        else:
            list_name, list_type = list_
            self.log.info(f"Resolving ID for list '{list_name}' with type '{list_type}'")
            matches = self.search(list_name, list_type)
            if len(matches) == 0:
                message = f"No match found for string '{list_name}'"
                raise ListResolutionError(message)
            if len(matches) > 1:
                exact_count = 0
                resolved_id = None
                for match in matches:
                    if match.name == list_name:
                        resolved_id = match.id_
                        exact_count += 1
                if (not resolved_id) or exact_count > 1:
                    message = f"Multiple matches found for string '{list_name}'"
                    raise ListResolutionError(message)
            else:
                resolved_id = matches[0].id_

        return resolved_id

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
from typing import Union

from pydantic import validate_call

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

    def __init__(self, rf_token: str = None) -> None:
        """Initialize EntityListMgr object.

        Args:
            rf_token (str, optional): Recorded Future API token. Defaults to None
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()
        self.match_mgr = EntityMatchMgr(rf_token=rf_token) if rf_token else EntityMatchMgr()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ListApiError)
    def fetch(self, list_: Union[str, tuple[str, str]]) -> EntityList:
        """Gets a list by its ID. Use this function for list info response.

        Endpoint:
            ``list/{list_id}/info``

        Args:
            list_ (str, tuple): list string ID or tuple of (name, type)

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            ListResolutionError: when ``list_`` is a tuple and name matches 0 or multiple entities
            ListApiError: if connection error occurs.

        Returns:
            RFList: RFList object for list ID
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
    def create(self, list_name: str, list_type: str = 'entity') -> EntityList:
        """Create list.

        Endpoint:
            ``list/create``

        Args:
            list_name (str): list name to use for new list
            list_type (str, optional): list type. Defaults to "entity"

            Supported list types are available on the support page for List API:
            https://support.recordedfuture.com/hc/en-us/articles/360058691913-List-API

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            ListApiError: if connection error occurs.

        Returns:
            EntityList: EntityList object for new list
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
        self, list_name: str = None, list_type: str = None, max_results: int = DEFAULT_LIMIT
    ) -> list[EntityList]:
        """Search lists.

        Endpoint:
            ``list/search``

        Args:
            list_name (str): list name to search
            list_type (str, optional): list type. Defaults to None, ignored when None
            max_results (int, optional): maximum total number of lists to return

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            ListApiError: if list API call fails

        Returns:
            list: EntityList objects from list/search
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
            elif len(matches) > 1:
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

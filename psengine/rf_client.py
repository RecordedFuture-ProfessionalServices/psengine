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

import re
from json.decoder import JSONDecodeError
from typing import Union

import jsonpath_ng
from jsonpath_ng.exceptions import JsonPathParserError
from pydantic import validate_call
from requests.models import Response

from .base_http_client import BaseHTTPClient
from .constants import RF_TOKEN_VALIDATION_REGEX
from .helpers import debug_call


@validate_call
def is_api_token_format_valid(token: str):
    """Checks if the token format is valid. The function does a
    simple regex check, but does not validate the token against the API.

    Args:
        token(str): Recorded Future API token

    Returns:
        bool: True if token format is valid, False otherwise
    """
    return re.match(RF_TOKEN_VALIDATION_REGEX, token) is not None


class RFClient(BaseHTTPClient):
    """Recorded Future HTTP API client."""

    def __init__(
        self,
        api_token: Union[str, None] = None,
        http_proxy=None,
        https_proxy=None,
        verify: Union[str, bool] = None,
        auth: tuple[str, str] = None,
        cert: Union[str, tuple[str, str], None] = None,
        timeout: int = None,
        retries: int = None,
        backoff_factor: int = None,
        status_forcelist: list = None,
        pool_max_size: int = None,
    ):
        """Recorded Future HTTP API client.

        Args:
            api_token (str, optional): RF API token. Defaults to RF_TOKEN env variable.
            http_proxy (str, optional): HTTP Proxy URL. Defaults to None.
            https_proxy (str, optional): HTTPS Proxy URL. Defaults to None.
            verify (Union[str, bool], optional): SSL verification flag or path to CA bundle.
                                            Defaults to True.
            auth (Tuple[str, str], optional): Basic Auth credentials. Defaults to None.
            cert (Union[str, Tuple[str, str], None], optional): Client certificates.
                                            Defaults to None.
            timeout (int, optional): Request timeout. Defaults to 120.
            retries (int, optional): Number of retries. Defaults to 5.
            backoff_factor (int, optional): Backoff factor. Defaults to 1.
            status_forcelist (int, optional): List of status codes to force a retry.
                                            Defaults to [502, 503, 504].
            pool_max_size (int, optional): Maximum number of connections in the pool.
                                                Defaults to 120.
        """
        super().__init__(
            http_proxy=http_proxy,
            https_proxy=https_proxy,
            verify=verify,
            auth=auth,
            cert=cert,
            timeout=timeout,
            retries=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            pool_max_size=pool_max_size,
        )

        self._api_token = api_token or self.config.rf_token.get_secret_value()
        if not self._api_token:
            raise ValueError('Missing Recorded Future API token.')
        if not is_api_token_format_valid(self._api_token):
            raise ValueError(
                f'Invalid Recorded Future API token, must match regex {RF_TOKEN_VALIDATION_REGEX}'
            )

    @debug_call
    @validate_call
    def request(
        self,
        method: str,
        url: str,
        data: Union[dict, list[dict], None] = None,
        *,
        params: Union[dict, None] = None,
        headers: Union[dict, None] = None,
        **kwargs,
    ) -> Response:
        """Perform an HTTP request.

        Args:
            method (str): HTTP Method, one of GET, PUT, POST, DELETE, HEAD, OPTIONS, PATCH
            url (str): URL to make the request to
            data (dict, optional): Request body. Defaults to None.
            params (dict, optional): HTTP query parameters. Defaults to None.
            headers (dict, optional): If specified it will override default headers and wont set
                                    the token.
            **kwargs: Additional keyword arguments, passed to the requests library

        Raises:
            ValueError: if method is neither of GET, PUT, POST, DELETE, HEAD, OPTIONS, PATCH

        Returns:
            requests.Response: requests.Response object
        """
        headers = headers or self._prepare_headers()

        return self.call(
            method=method,
            url=url,
            headers=headers,
            data=data,
            params=params,
            **kwargs,
        )

    def _request_paged_get(
        self,
        all_results,
        params,
        max_results,
        offset_key,
        method,
        url,
        headers,
        data,
        results_expr,
        json_response,
        **kwargs,
    ):
        if (
            'counts' not in json_response
            or 'total' not in json_response['counts']
            or 'returned' not in json_response['counts']
        ):
            return json_response

        seen = json_response['counts']['returned']
        if json_response['counts']['total'] > max_results:
            total = max_results
        else:
            total = json_response['counts']['total']

        while seen < total:
            if not params:
                params = {}
            params[offset_key] = seen
            params['limit'] = min(json_response['counts']['returned'], max_results - seen)
            response = self.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                params=params,
                **kwargs,
            )
            json_response = response.json()
            all_results += self._get_matches(results_expr, json_response)
            seen += json_response['counts']['returned']
        return all_results

    def _request_paged_post(
        self,
        data,
        offset_key,
        method,
        url,
        headers,
        params,
        results_expr,
        max_results,
        json_response,
        all_results,
        **kwargs,
    ):
        if 'next_offset' in json_response:
            while 'next_offset' in json_response:
                data[offset_key] = json_response['next_offset']
                json_response = self.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,
                    params=params,
                    **kwargs,
                ).json()
                all_results += self._get_matches(results_expr, json_response)
                if len(all_results) >= max_results:
                    all_results = all_results[:max_results]
                    break
        else:
            seen = json_response['counts']['returned']
            if json_response['counts']['total'] > max_results:
                total = max_results
            else:
                total = json_response['counts']['total']

            while seen < total:
                data[offset_key] = seen
                json_response = self.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,
                    params=params,
                    **kwargs,
                ).json()
                all_results += self._get_matches(results_expr, json_response)
                seen += json_response['counts']['returned']
        return all_results

    def request_paged(
        self,
        method: str,
        url: str,
        max_results: int = 1000,
        data: Union[dict, list[dict], None] = None,
        *,
        params: Union[dict, None] = None,
        headers: Union[dict, None] = None,
        results_path: str = 'data',
        offset_key: str = 'offset',
        **kwargs,
    ) -> list[dict]:
        """Perform a paged HTTP request.

        Please note that some RF APIs can not paginate through more than 1000 results and will
        result in an error (HTTP 400) if ``max_results`` is set to a higher value. While APIs such
        as Identity can paginate through more than 1000 results.

            .. code-block:: python
                :linenos:

                >>> response = rfc.request_paged(
                        method='post',
                        url='https://api.recordedfuture.com/identity/credentials/search',
                        max_results=1565,
                        data={
                            'domains': ['norsegods.online'],
                            'filter': {'first_downloaded_gte': '2024-01-01T23:40:47.034Z'},
                            'limit': 100,
                        },
                        results_path='identities',
                        offset_key='offset',
                    )

                >>> response = rfc.request_paged(
                        method='get',
                        url='https://api.recordedfuture.com/v2/ip/search',
                        params={'limit': 100, 'fields': 'entity', 'riskRule': 'dnsAbuse'},
                        results_path='data.results',
                        offset_key='from',
                    )

        Args:
            method (str): HTTP method: GET or POST
            url (str): URL to make the request to
            max_results (int, optional): Maximum number of results to return. Defaults to 1000.
            data (dict, optional): Request body. Defaults to None.
            params (dict, optional): HTTP query parameters. Defaults to None.
            headers (dict, optional): If specified it will override default headers and wont set
                                    the token.
            results_path (str, optional): Path to extract paged results from. Defaults to 'data'.
            offset_key (str, optional): Key to use for paging. Defaults to 'offset'.
            **kwargs: Additional keyword arguments, passed to the requests library

        Raises:
            ValueError: if method is not GET or POST
            ValueError: If results_path is invalid
            KeyError: If no results are found in the API response

        Returns:
            list[dict]: List of dict containing the results
        """
        try:
            results_expr = jsonpath_ng.parse(results_path)
        except JsonPathParserError as err:
            raise ValueError(f'Invalid results_path: {results_path}') from err
        root_key = self._get_root_key(results_expr)

        # Make the first request
        response = self.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            params=params,
            **kwargs,
        )

        all_results = []
        try:
            # Try to parse the response as JSON
            json_response = response.json()
        except JSONDecodeError:
            self.log.debug(f'Paged request does not contain valid JSON:\n{response.text}')
            raise

        # Check if the root key is in the response
        if root_key not in json_response:
            raise KeyError(results_path)

        if len(json_response[root_key]) == 0:
            return all_results

        # Get the initial results from the first response and add them to the list
        all_results += self._get_matches(results_expr, json_response)

        if method.lower() == 'get':
            return self._request_paged_get(
                url=url,
                headers=headers,
                data=data,
                method=method,
                params=params,
                max_results=max_results,
                results_expr=results_expr,
                offset_key=offset_key,
                json_response=json_response,
                all_results=all_results,
                **kwargs,
            )

        if method.lower() == 'post':
            return self._request_paged_post(
                url=url,
                method=method,
                headers=headers,
                data=data,
                params=params,
                max_results=max_results,
                results_expr=results_expr,
                offset_key=offset_key,
                json_response=json_response,
                all_results=all_results,
                **kwargs,
            )

        raise ValueError('Invalid method for paged request. Must be GET or POST')

    @debug_call
    @validate_call
    def is_authorized(self, method: str, url: str, **kwargs) -> bool:
        """Check if the request is authorized to a given Recorded Future API endpoint.

        Args:
            method (str): HTTP method
            url (str): URL to perform the check against
            **kwargs: Additional keyword arguments, passed to the requests library

        Returns:
            bool: True if authorized, False otherwise
        """
        try:
            response = self.request(method, url, **kwargs)
            return response.status_code == 200
        except Exception as err:  # noqa: BLE001:
            self.log.error(f'Error during validation: {err}')
            return False

    def _prepare_headers(self):
        user_agent = self._get_user_agent_header()
        headers = {
            'User-Agent': user_agent,
            'Content-Type': 'application/json',
            'accept': 'application/json',
        }
        if self._api_token:
            headers['X-RFToken'] = self._api_token
        else:
            # In theory should never happen, but just in case
            self.log.warning('Request being made with no Recorded Future API key set')

        return headers

    def _get_root_key(self, path: jsonpath_ng.jsonpath.Child) -> str:
        try:
            return self._get_root_key(path.left)
        except AttributeError:
            return str(path)

    def _get_matches(
        self, results_expr: jsonpath_ng.jsonpath.Fields, results: Union[list, dict]
    ) -> list:
        """Get matches from results.

        Args:
            results_expr (jsonpath_ng): jsonpath_ng object
            results (dict): results

        Raises:
            KeyError: if no results are found

        Returns:
            list: list of matches
        """
        matches = results_expr.find(results)
        results = []
        if not len(matches):
            self.log.warning(f'No results found for path: {str(results_expr)}')
            raise KeyError(str(results_expr))

        for match in matches:
            if isinstance(match.value, list):
                results += match.value
            else:
                results.append(match.value)
        return results

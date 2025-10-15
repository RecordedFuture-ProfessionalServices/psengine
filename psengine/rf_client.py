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
from collections import defaultdict
from contextlib import suppress
from json.decoder import JSONDecodeError
from typing import Annotated, Optional, Union

import jsonpath_ng
from jsonpath_ng.exceptions import JsonPathParserError
from pydantic import validate_call
from requests.models import Response
from typing_extensions import Doc

from .base_http_client import BaseHTTPClient
from .constants import RF_TOKEN_VALIDATION_REGEX
from .helpers import debug_call


@validate_call
def is_api_token_format_valid(
    token: Annotated[str, Doc('A Recorded Future API token.')],
) -> Annotated[bool, Doc('True if the token format is valid, False otherwise.')]:
    """Check if the token format is valid.

    The function performs a simple regex check but does not validate the token against the API.
    """
    return re.match(RF_TOKEN_VALIDATION_REGEX, token) is not None


class RFClient(BaseHTTPClient):
    """Recorded Future HTTP API client."""

    def __init__(
        self,
        api_token: Annotated[
            Union[str, None], Doc('An RF API token. Defaults to RF_TOKEN environment variable.')
        ] = None,
        http_proxy: Annotated[str, Doc('An HTTP proxy URL.')] = None,
        https_proxy: Annotated[str, Doc('An HTTPS proxy URL.')] = None,
        verify: Annotated[
            Union[str, bool],
            Doc('An SSL verification flag or path to CA bundle.'),
        ] = None,
        auth: Annotated[tuple[str, str], Doc('Basic Auth credentials.')] = None,
        cert: Annotated[Union[str, tuple[str, str], None], Doc('Client certificates.')] = None,
        timeout: Annotated[int, Doc('A request timeout. Defaults to 120.')] = None,
        retries: Annotated[int, Doc('A number of retries. Defaults to 5.')] = None,
        backoff_factor: Annotated[int, Doc('A backoff factor. Defaults to 1.')] = None,
        status_forcelist: Annotated[
            list, Doc('A list of status codes to force a retry. Defaults to [502, 503, 504].')
        ] = None,
        pool_max_size: Annotated[
            int, Doc('The maximum number of connections in the pool. Defaults to 120.')
        ] = None,
    ):
        """Recorded Future HTTP API client."""
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
                f'Invalid Recorded Future API token: must match regex {RF_TOKEN_VALIDATION_REGEX}'
            )

    @debug_call
    @validate_call
    def request(
        self,
        method: Annotated[
            str, Doc('An HTTP method, one of GET, PUT, POST, DELETE, HEAD, OPTIONS, PATCH.')
        ],
        url: Annotated[str, Doc('A URL to make the request to.')],
        data: Annotated[Union[dict, list[dict], bytes, None], Doc('A request body.')] = None,
        *,
        params: Annotated[Optional[dict], Doc('HTTP query parameters.')] = None,
        headers: Annotated[
            Optional[dict],
            Doc('If specified, it overrides default headers and does not set the token.'),
        ] = None,
        content_type_header: Annotated[
            Optional[str], Doc('Content-Type header value.')
        ] = 'application/json',
        **kwargs,
    ) -> Annotated[Response, Doc('A requests.Response object.')]:
        """Perform an HTTP request.

        Raises:
            ValidationError: If method is not one of GET, PUT, POST, DELETE, HEAD, OPTIONS, PATCH.
        """
        headers = headers or self._prepare_headers(content_type_header)

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
        dict_results,
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
                if isinstance(results_expr, list):
                    for expr in results_expr:
                        with suppress(KeyError):
                            dict_results[str(expr)].extend(self._get_matches(expr, json_response))

                    if any(len(v) >= max_results for v in dict_results.values()):
                        dict_results = {k: v[:max_results] for k, v in dict_results.items()}
                        break
                else:
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
                data['limit'] = min(json_response['counts']['returned'], max_results - seen)
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
        return dict_results or all_results

    def request_paged(
        self,
        method: Annotated[str, Doc('An HTTP method: GET or POST.')],
        url: Annotated[str, Doc('A URL to make the request to.')],
        max_results: Annotated[int, Doc('The maximum number of results to return.')] = 1000,
        data: Annotated[Union[dict, list[dict], None], Doc('A request body.')] = None,
        *,
        params: Annotated[Union[dict, None], Doc('HTTP query parameters.')] = None,
        headers: Annotated[
            Union[dict, None],
            Doc('If specified, it overrides default headers and does not set the token.'),
        ] = None,
        results_path: Annotated[
            Union[str, list[str]], Doc('Path to extract paged results from.')
        ] = 'data',
        offset_key: Annotated[str, Doc("Key to use for paging. Defaults to 'offset'.")] = 'offset',
        **kwargs,
    ) -> Annotated[list[dict], Doc('Resulting data.')]:
        """Perform a paged HTTP request.

        Please note that some RF APIs cannot paginate through more than 1000 results and will
        return an error (HTTP 400) if `max_results` exceeds that. APIs such as Identity support
        pagination beyond 1000 results.

        Example:
            ```python
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
            ```

        Raises:
            KeyError: If no results are found in the API response.
            ValueError:
                - If method is not GET or POST.
                - If results_path is invalid.
        """
        results_paths = [results_path] if isinstance(results_path, str) else results_path

        try:
            results_expr = [jsonpath_ng.parse(p) for p in results_paths]
        except JsonPathParserError as err:
            raise ValueError(f'Invalid results_path: {results_path}') from err
        root_key = [self._get_root_key(e) for e in results_expr]

        # Make the first request
        response = self.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            params=params,
            **kwargs,
        )

        try:
            json_response = response.json()
        except JSONDecodeError:
            self.log.debug(f'Paged request does not contain valid JSON:\n{response.text}')
            raise

        if all(r not in json_response for r in root_key):
            raise KeyError(results_path)

        all_results = []
        dict_results = defaultdict(list)

        if all(len(json_response[r]) == 0 for r in root_key):
            return all_results

        # Get the initial results from the first response and add them to the list
        if isinstance(results_path, str):
            all_results += self._get_matches(results_expr[0], json_response)
        else:
            for expr in results_expr:
                with suppress(KeyError):
                    dict_results[str(expr)].extend(self._get_matches(expr, json_response))

        if method.lower() == 'get':
            return self._request_paged_get(
                url=url,
                headers=headers,
                data=data,
                method=method,
                params=params,
                max_results=max_results,
                results_expr=results_expr[0] if isinstance(results_path, str) else results_expr,
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
                results_expr=results_expr[0] if isinstance(results_path, str) else results_expr,
                offset_key=offset_key,
                json_response=json_response,
                all_results=all_results,
                dict_results=dict_results,
                **kwargs,
            )

        raise ValueError('Invalid method for paged request. Must be GET or POST')

    @debug_call
    @validate_call
    def is_authorized(
        self,
        method: Annotated[str, Doc('An HTTP method.')],
        url: Annotated[str, Doc('A URL to perform the check against.')],
        **kwargs,
    ) -> Annotated[bool, Doc('True if authorized, False otherwise.')]:
        """Check if the request is authorized to a given Recorded Future API endpoint."""
        try:
            response = self.request(method, url, **kwargs)
            return response.status_code == 200
        except Exception as err:  # noqa: BLE001
            self.log.error(f'Error during validation: {err}')
            return False

    def _prepare_headers(self, content_type_header: str = 'application/json'):
        user_agent = self._get_user_agent_header()
        headers = {
            'User-Agent': user_agent,
            'Content-Type': content_type_header,
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

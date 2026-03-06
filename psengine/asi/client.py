import re
from collections import defaultdict
from contextlib import suppress
from copy import deepcopy
from typing import Annotated, Any, Optional, Union

import jsonpath_ng
from jsonpath_ng.exceptions import JsonPathParserError
from pydantic import Field, validate_call
from requests.exceptions import JSONDecodeError
from requests.models import Response
from typing_extensions import Doc

from ..base_http_client import BaseHTTPClient
from ..constants import ASI_TOKEN_VALIDATION_REGEX, DEFAULT_LIMIT
from ..helpers import debug_call
from .constants import DEFAULT_ASI_PAGE_SIZE, MAX_ASI_PAGE_SIZE


@validate_call
def is_api_token_format_valid(
    token: Annotated[str, Doc('A Recorded Future ASI API token.')],
) -> Annotated[bool, Doc('True if the token format is valid, False otherwise.')]:
    """Check if the token format is valid.

    The function performs a simple regex check but does not validate the token against the API.
    """
    return re.match(ASI_TOKEN_VALIDATION_REGEX, token) is not None


class ASIClient(BaseHTTPClient):
    """Recorded Future ASI Attack Surface Intelligence API client."""

    def __init__(
        self,
        api_token: Annotated[
            Union[str, None],
            Doc('A Recorded Future ASI API key.'),
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
        self._api_token = api_token or self.config.asi_token.get_secret_value()
        if not self._api_token:
            raise ValueError('Missing Recorded Future Recorded Future ASI API token.')
        if not is_api_token_format_valid(self._api_token):
            raise ValueError(
                f'Invalid Recorded Future API token: must match regex {ASI_TOKEN_VALIDATION_REGEX}'
            )

    @debug_call
    @validate_call
    def request(
        self,
        method: Annotated[
            str, Doc('An HTTP method, one of GET, PUT, POST, DELETE, HEAD, OPTIONS, PATCH.')
        ],
        url: Annotated[str, Doc('A URL or API path to make the request to.')],
        data: Annotated[Union[dict, list[dict], bytes, None], Doc('A request body.')] = None,
        *,
        params: Annotated[Optional[dict], Doc('HTTP query parameters.')] = None,
        headers: Annotated[
            Optional[dict],
            Doc('If specified, it overrides default headers and does not set the API key.'),
        ] = None,
        **kwargs,
    ) -> Annotated[Response, Doc('A requests.Response object.')]:
        """Perform an HTTP request against Recorded Future ASI."""
        headers = headers or self._prepare_headers()

        return self.call(
            method=method,
            url=url,
            headers=headers,
            data=data,
            params=params,
            **kwargs,
        )

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
        **kwargs,
    ) -> Annotated[list[dict], Doc('Resulting data.')]:
        """Perform a paged HTTP request.

         Please note that some RF APIs cannot paginate through more than 1000 results and will
         return an error (HTTP 400) if `max_results` exceeds that. APIs such as Identity support
         pagination beyond 1000 results.

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

        if len(all_results) >= max_results:
            return all_results[:max_results]

        if method.lower() == 'get':
            return self._request_paged_get(
                url=url,
                headers=headers,
                data=data,
                method=method,
                params=params,
                max_results=max_results,
                results_expr=results_expr[0] if isinstance(results_path, str) else results_expr,
                offset_key='cursor',
                json_response=json_response,
                all_results=all_results,
                **kwargs,
            )

        if method.lower() == 'post':
            data['limit'] = min(data['limit'], max_results - len(all_results))

            return self._request_paged_post(
                url=url,
                method=method,
                headers=headers,
                data=data,
                params=params,
                max_results=max_results,
                results_expr=results_expr[0] if isinstance(results_path, str) else results_expr,
                offset_key='cursor',
                json_response=json_response,
                all_results=all_results,
                dict_results=dict_results,
                **kwargs,
            )

        raise ValueError('Invalid method for paged request. Must be GET or POST')

    def _initialize_paged_request(
        self,
        method: str,
        params: Optional[dict],
        data: Optional[dict],
        limit: Optional[int],
    ) -> tuple[dict, Union[dict, list[dict], bytes, None]]:
        request_params = deepcopy(params) if params else {}
        request_data = deepcopy(data)

        if method == 'GET':
            if 'limit' not in request_params:
                request_params['limit'] = limit
            return request_params, request_data

        if request_data is None:
            request_data = {}

        request_data.setdefault('pagination', {})
        if not isinstance(request_data['pagination'], dict):
            raise ValueError("`data['pagination']` must be a dictionary when provided")

        if limit is not None and 'limit' not in request_data['pagination']:
            request_data['pagination']['limit'] = limit
        return request_params, request_data

    def _prepare_headers(self) -> dict:
        headers = {
            'User-Agent': self._get_user_agent_header(),
            'Content-Type': 'application/json',
            'accept': 'application/json',
        }
        if self._api_token:
            headers['apikey'] = self._api_token
        else:
            self.log.warning('Request being made with no Recorded Future ASI API key set')
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
            not json_response['meta'].get('counts')
            or 'total' not in json_response['meta']['counts']
        ):
            return json_response

        seen = json_response['meta']['counts']['returned']
        if json_response['meta']['counts']['total'] > max_results:
            total = max_results
        else:
            total = json_response['meta']['counts']['total']

        while seen < total:
            if not params:
                params = {}
            params[offset_key] = seen
            params['limit'] = min(json_response['meta']['counts']['returned'], max_results - seen)
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
            seen += json_response['meta']['counts']['returned']
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
            current_len = 0
            while 'next_offset' in json_response:
                data[offset_key] = json_response['next_offset']
                data['limit'] = min(data['limit'], max_results - current_len)
                if data['limit'] <= 0:
                    break

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
                    current_len = max(len(v) for v in dict_results.values())

                else:
                    all_results += self._get_matches(results_expr, json_response)
                    current_len = len(all_results)
                    if current_len >= max_results:
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

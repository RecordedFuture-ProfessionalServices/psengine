import re
from copy import deepcopy
from typing import Annotated, Any, Optional, Union

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

    @debug_call
    @validate_call
    def request_paged(
        self,
        method: Annotated[str, Doc('An HTTP method. Supports GET and POST.')],
        url: Annotated[str, Doc('A URL or API path to make the request to.')],
        data: Annotated[Optional[dict], Doc('A request body.')] = None,
        *,
        params: Annotated[Optional[dict], Doc('HTTP query parameters.')] = None,
        headers: Annotated[
            Optional[dict],
            Doc('If specified, it overrides default headers and does not set the API key.'),
        ] = None,
        max_results: Annotated[
            int, Doc('The maximum number of results to return.')
        ] = DEFAULT_LIMIT,
        objects_per_page: Annotated[Optional[int], Doc('Requested page size.')] = Field(
            ge=1, le=MAX_ASI_PAGE_SIZE, default=DEFAULT_ASI_PAGE_SIZE
        ),
        **kwargs,
    ) -> Annotated[list[Any], Doc('Paged records merged into a single list.')]:
        """Perform a paged request using ASI cursor-based pagination."""
        method = method.upper()
        if method not in ('GET', 'POST'):
            raise ValueError('Invalid method for paged request. Must be GET or POST')

        request_params, request_data = self._initialize_paged_request(
            method=method, params=params, data=data, limit=objects_per_page
        )

        all_results = []
        meta = None

        while len(all_results) < max_results:
            remaining_results = max_results - len(all_results)
            if method == 'GET':
                request_params['limit'] = min(request_params['limit'], remaining_results)
            else:
                request_data['pagination']['limit'] = min(
                    request_data['pagination']['limit'], remaining_results
                )
            response = self.request(
                method=method,
                url=url,
                headers=headers,
                data=request_data,
                params=request_params,
                **kwargs,
            )

            try:
                json_response = response.json()
            except JSONDecodeError:
                self.log.error(f'Paged request does not contain valid JSON:\n{response.text}')
                raise
            try:
                page_results = json_response['data']
            except KeyError:
                self.log.error(f'Paged request does not contain `data` field:\n{response.text}')
                raise
            meta = json_response['meta']

            request_params['cursor'] = json_response['meta']['pagination']['next_cursor']

            all_results.extend(page_results)
            if len(all_results) >= max_results:
                break
        return {'data': all_results[:max_results], 'meta': meta}

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

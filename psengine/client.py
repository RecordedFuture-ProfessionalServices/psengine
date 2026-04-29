import re
from typing import Annotated, Optional, Union

from pydantic import Field, validate_call
from requests.exceptions import JSONDecodeError
from requests.models import Response
from typing_extensions import Doc

from ..base_http_client import BaseHTTPClient
from ..constants import DEFAULT_LIMIT, SANDBOX_TOKEN_VALIDATION_REGEX
from ..helpers import debug_call

SAMPLES_PER_PAGE = 50
MAXIMUM_SAMPLES = 200


@validate_call
def is_api_token_format_valid(
    token: Annotated[str, Doc('A Recorded Future API token.')],
) -> Annotated[bool, Doc('True if the token format is valid, False otherwise.')]:
    """Check if the token format is valid.

    The function performs a simple regex check but does not validate the token against the API.
    """
    return re.match(SANDBOX_TOKEN_VALIDATION_REGEX, token) is not None


class SandboxClient(BaseHTTPClient):
    #TODO: add the other base URLS as well
    def __init__(
        self,
        api_token: Annotated[
            Union[str, None],
            Doc('The Sandbox API token. Defaults to SANDBOX_TOKEN environment variable.'),
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

        self._api_token = api_token or self.config.sandbox_token.get_secret_value()
        if not self._api_token:
            raise ValueError('Missing Recorded Future Sandbox API token.')
        if not is_api_token_format_valid(self._api_token):
            raise ValueError(
                f'Invalid Sandbox API token: must match regex {SANDBOX_TOKEN_VALIDATION_REGEX}'
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

    @debug_call
    @validate_call
    def request_paged(
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
        max_samples: int = DEFAULT_LIMIT,
        samples_per_page: Annotated[
            Optional[int], Doc('The number of samples per page for pagination.')
        ] = Field(ge=1, le=MAXIMUM_SAMPLES, default=SAMPLES_PER_PAGE),
        **kwargs,
    ) -> Annotated[Response, Doc('A requests.Response object.')]:
        """Perform an HTTP request.

        Raises:
            ValidationError: If method is not one of GET, PUT, POST, DELETE, HEAD, OPTIONS, PATCH.
        """
        headers = headers or self._prepare_headers(content_type_header)
        all_results = []

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

        try:
            all_results.extend(json_response['data'])
        except KeyError:
            self.log.debug(f'Paged request does not contain `data` JSON key:\n{response.text}')
            raise

        while (offset := json_response.get('next')) or (len(all_results) < max_samples):
            params['offset'] = offset
            params['limit'] = samples_per_page
            response = self.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                params=params,
                **kwargs,
            )
            json_response = response.json()
            all_results.extend(json_response['data'])
        return all_results[:max_samples]

    def _prepare_headers(self, content_type_header: str = 'application/json'):
        user_agent = self._get_user_agent_header()
        headers = {
            'User-Agent': user_agent,
            'Content-Type': content_type_header,
            'accept': 'application/json',
        }
        if self._api_token:
            headers['Authorization'] = f'Bearer {self._api_token}'
        else:
            # In theory should never happen, but just in case
            self.log.warning('Request being made with no Sandbox API key set')
        return headers

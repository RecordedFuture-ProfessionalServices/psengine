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
from typing import Annotated

from pydantic import Field, validate_call
from requests.exceptions import JSONDecodeError
from requests.models import Response
from typing_extensions import Doc

from ..base_http_client import BaseHTTPClient
from ..constants import SANDBOX_TOKEN_VALIDATION_REGEX
from ..helpers import debug_call
from .constants import DEFAULT_PAGE_LIMIT

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
    """Recorded Future Sandbox API client."""

    def __init__(
        self,
        api_token: Annotated[
            str | None,
            Doc('The Sandbox API token. Defaults to SANDBOX_TOKEN environment variable.'),
        ] = None,
        http_proxy: Annotated[str, Doc('An HTTP proxy URL.')] = None,
        https_proxy: Annotated[str, Doc('An HTTPS proxy URL.')] = None,
        verify: Annotated[
            str | bool,
            Doc('An SSL verification flag or path to CA bundle.'),
        ] = None,
        auth: Annotated[tuple[str, str], Doc('Basic Auth credentials.')] = None,
        cert: Annotated[str | tuple[str, str] | None, Doc('Client certificates.')] = None,
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
        data: Annotated[dict | list[dict] | bytes | None, Doc('A request body.')] = None,
        *,
        params: Annotated[dict | None, Doc('HTTP query parameters.')] = None,
        headers: Annotated[
            dict | None,
            Doc('If specified, it overrides default headers and does not set the token.'),
        ] = None,
        content_type_header: Annotated[
            str | None, Doc('Content-Type header value.')
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
        data: Annotated[dict | list[dict] | bytes | None, Doc('A request body.')] = None,
        *,
        params: Annotated[dict | None, Doc('HTTP query parameters.')] = None,
        headers: Annotated[
            dict | None,
            Doc('If specified, it overrides default headers and does not set the token.'),
        ] = None,
        content_type_header: Annotated[
            str | None, Doc('Content-Type header value.')
        ] = 'application/json',
        max_results: int = DEFAULT_PAGE_LIMIT,
        results_per_page: Annotated[
            int | None, Doc('The number of samples per page for pagination.')
        ] = Field(ge=1, le=MAXIMUM_SAMPLES, default=SAMPLES_PER_PAGE),
        **kwargs,
    ) -> Annotated[list, Doc('Result rows accumulated across all fetched pages.')]:
        """Perform a paged HTTP request, following `next` offsets until `max_results` is reached.

        Raises:
            ValidationError: If method is not one of GET, PUT, POST, DELETE, HEAD, OPTIONS, PATCH.
        """
        headers = headers or self._prepare_headers(content_type_header)
        # Copy so our `limit`/`offset` bookkeeping never mutates the caller's dict.
        params = dict(params or {})
        all_results: list = []

        # Trim `limit` to remaining headroom so the last page doesn't overfetch.
        params['limit'] = min(results_per_page, max_results - len(all_results))
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
            page = json_response['data']
        except KeyError:
            self.log.debug(f'Paged request does not contain `data` JSON key:\n{response.text}')
            raise

        all_results.extend(page)
        offset = json_response.get('next')
        prev_offset = None

        while offset and offset != prev_offset and len(all_results) < max_results:
            params['offset'] = offset
            params['limit'] = min(results_per_page, max_results - len(all_results))
            response = self.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                params=params,
                **kwargs,
            )
            json_response = response.json()
            page = json_response.get('data', [])

            if not page:
                # The last page is always empty
                self.log.debug('Paged request returned an empty `data` page; stopping.')
                break

            all_results.extend(page)
            prev_offset = offset
            offset = json_response.get('next')

        return all_results[:max_results]

    def _prepare_headers(self, content_type_header: str | None = 'application/json'):
        user_agent = self._get_user_agent_header()
        headers = {
            'User-Agent': user_agent,
            'accept': 'application/json',
        }
        # `content_type_header=None` omits Content-Type so `requests` can set the
        # multipart/form-data boundary itself (used by multipart file uploads).
        if content_type_header is not None:
            headers['Content-Type'] = content_type_header
        if self._api_token:
            headers['Authorization'] = f'Bearer {self._api_token}'
        else:
            # In theory should never happen, but just in case
            self.log.warning('Request being made with no Sandbox API key set')
        return headers

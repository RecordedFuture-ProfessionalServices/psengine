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
# accessed from any third party API.                                                         #.
##############################################################################################

import json
import logging
from typing import Union

from pydantic import validate_call
from requests import ConnectionError, ConnectTimeout, HTTPError, ReadTimeout, Session, adapters
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import JSONDecodeError
from requests.models import Response

from ._sdk_id import SDK_ID
from .config import get_config
from .constants import (
    BACKOFF_FACTOR,
    POOL_MAX_SIZE,
    REQUEST_TIMEOUT,
    RETRY_TOTAL,
    SSL_VERIFY,
    STATUS_FORCELIST,
)
from .endpoints import BASE_URL
from .helpers import OSHelpers, debug_call


class BaseHTTPClient:
    """Generic HTTP client for making requests (requests wrapper)."""

    def __init__(
        self,
        http_proxy: str = None,
        https_proxy: str = None,
        verify: Union[str, bool] = SSL_VERIFY,
        auth: tuple[str, str] = None,
        cert: Union[str, tuple[str, str], None] = None,
        timeout=REQUEST_TIMEOUT,
        retries=RETRY_TOTAL,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=STATUS_FORCELIST,
        pool_max_size=POOL_MAX_SIZE,
    ):
        """Generic HTTP client for making requests (``requests`` wrapper).

        Args:
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
        self.log = logging.getLogger(__name__)
        self.config = get_config()
        self.http_proxy = http_proxy if http_proxy is not None else self.config.http_proxy
        self.https_proxy = https_proxy if https_proxy is not None else self.config.https_proxy
        self.proxies = self._set_proxies()
        self.verify = verify if verify is not None else self.config.client_ssl_verify
        self.timeout = timeout if timeout is not None else self.config.client_timeout
        self.retries = retries if retries is not None else self.config.client_retries
        self.backoff_factor = (
            backoff_factor if backoff_factor is not None else self.config.client_backoff_factor
        )
        self.status_forcelist = (
            status_forcelist
            if status_forcelist is not None
            else self.config.client_status_forcelist
        )
        self.pool_max_size = (
            pool_max_size if pool_max_size is not None else self.config.client_pool_max_size
        )
        self.session = self._create_session()
        self.session.cert = cert if cert is not None else self.config.client_cert
        self.session.auth = auth if auth is not None else self.config.client_basic_auth

        self._set_retry_config()

    @debug_call
    @validate_call
    def call(
        self,
        method: str,
        url: str,
        data: Union[dict, list[dict], None] = None,
        *,
        params: Union[dict, None] = None,
        headers: Union[dict, None] = None,
        **kwargs,
    ) -> Response:
        """Invokes a HTTP request using the ``requests`` library.

        Args:
            method (str): HTTP Method, one of GET, PUT, POST, DELETE, HEAD, OPTIONS, PATCH
            url (str): URL to make the request to
            headers (dict, optional): If specified it will override default headers and wont
            set the token. Defaults to None.
            data (dict, optional): Body. Defaults to None.
            params (dict, optional): HTTP query parameters. Defaults to None.
            **kwargs: Additional keyword arguments, passed to the requests library

        Raises:
            ValueError: if method is neither of GET, PUT, POST, DELETE, HEAD, OPTIONS, PATCH
            HTTPError: if requests returns a non 2xx status.
            JSONDecodeError: if requests returns malformed data.
            ConnectTimeout: if requests times out while trying to connect to the server.
            ConnectionError: if requests fails before terminating.
            ReadTimeout: if the server didnt send any data on time.

        Returns:
            requests.Response: requests.Response object
        """
        method_func = self._choose_method_type(method)

        if not headers:
            headers = {}

        if 'User-Agent' not in headers:
            headers['User-Agent'] = self._get_user_agent_header()

        data = json.dumps(data) if data is not None else None

        try:
            response = method_func(
                url=url,
                headers=headers,
                data=data,
                params=params,
                verify=self.verify,
                timeout=self.timeout,
                **kwargs,
            )
            self.log.debug(f'HTTP Status Code: {response.status_code}')

        except (ConnectionError, ConnectTimeout, ReadTimeout) as err:
            self.log.debug(f'GET request failed. Cause: {err}')
            raise

        try:
            response.raise_for_status()

        except HTTPError as err:
            msg = str(err)
            try:
                data = response.json()
            except JSONDecodeError:
                data = {}

            message = data.get('message') or data.get('error', {}).get('message')
            if message:
                msg += f', Cause: {message}'

            self.log.debug(f'{method} request failed. {msg}')

            raise HTTPError(msg, response=response) from err

        return response

    @debug_call
    @validate_call
    def can_connect(self, method: str = 'get', url: str = BASE_URL) -> bool:
        """Check if the client can reach the specified API URL.

        Args:
            method (str, optional): HTTP Method, one of GET, PUT, POST, DELETE,
                HEAD, OPTIONS, PATCH. Default: GET
            url (str, optional): url to test. Default: api.recordedfuture.com

        Returns:
            bool: True if connection is 200 else False
        """
        try:
            request = self.call(method=method, url=url)
            request.raise_for_status()
            return True
        except Exception as err:  # noqa: BLE001
            self.log.error(f'Error during connectivity test: {err}')
            return False

    @debug_call
    @validate_call
    def set_urllib_log_level(self, level: str) -> None:
        """Set log level for urllib3 library.

        Args:
            level (str): log level to be set: CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
        """
        if not level or level.upper() not in (
            'CRITICAL',
            'ERROR',
            'WARNING',
            'INFO',
            'DEBUG',
            'NOTSET',
        ):
            self.log.warning('Log level is empty or not valid')
            return
        logging.getLogger('urllib3').setLevel(level.upper())

    def _set_proxies(self):
        """Set the proxy configuration.

        Returns:
            dict: Proxy configuration
        """
        proxies = {}
        if self.http_proxy:
            proxies['http'] = self.http_proxy
        if self.https_proxy:
            proxies['https'] = self.https_proxy
        return proxies

    def _create_session(self):
        """Create a base HTTP client session.

        Returns:
            session: requests.Session object
        """
        self.log.debug('Creating an HTTP client session')
        session = Session()
        adapter = adapters.HTTPAdapter(pool_maxsize=self.pool_max_size)
        session.mount('https://', adapter)

        if len(self.proxies) > 0:
            session.proxies.update(self.proxies)

        return session

    def _set_retry_config(self):
        """Set the retry configuration for the session."""
        retries = Retry(
            total=self.retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=self.status_forcelist,
        )
        for prefix in 'http://', 'https://':
            self.session.mount(prefix, HTTPAdapter(max_retries=retries))

    def _choose_method_type(self, method: str):
        method_func = {
            'GET': self.session.get,
            'PUT': self.session.put,
            'POST': self.session.post,
            'DELETE': self.session.delete,
            'HEAD': self.session.head,
            'OPTIONS': self.session.options,
            'PATCH': self.session.patch,
        }.get(method.upper())

        if not method_func:
            raise ValueError(f'Unknown HTTP method: {method}')

        return method_func

    def _get_user_agent_header(self):
        os_info = OSHelpers.os_platform()
        app_id = self.config.app_id or 'app_id unknown'
        platform_id = self.config.platform_id or 'platform_id unknown'
        user_agent_list = []

        user_agent_list.append(app_id)
        if os_info is not None:
            user_agent_list.append(f'({os_info})')
        user_agent_list.append(SDK_ID)
        user_agent_list.append(platform_id)

        return ' '.join(user_agent_list)

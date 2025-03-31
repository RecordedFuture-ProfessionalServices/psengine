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

import csv
import logging
from collections.abc import Generator
from typing import Any, Optional, Union

from pydantic import BaseModel, validate_call
from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    HTTPError,
    JSONDecodeError,
    ReadTimeout,
    SSLError,
)

from ..endpoints import EP_FUSION_FILES, EP_RISKLIST
from ..helpers import debug_call
from ..rf_client import RFClient
from .constants import DEFAULT_RISKLIST_FORMAT
from .errors import RiskListNotAvailableError


class RisklistMgr:
    """Manages requests for Recorded Future risk lists."""

    def __init__(self, rf_token: str = None):
        """Initializes the RiskListMgr object.

        Args:
            rf_token (str, optional): Recorded Future API token. Defaults to None
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    def fetch_risklist(
        self,
        list: str,  # noqa: A002
        entity_type: str = None,
        format: str = None,  # noqa: A002
        headers: bool = True,
        validate: Optional[Any] = None,
    ) -> Generator[Union[dict, list[str], BaseModel], None, None]:
        """Get a Recorded Future RiskList. Specify a fusion_path to get a custom
        risklist instead - format field is ignored when custom risklists are used.

        Gotchas:

            - If a specified list does not exist, RF API returns the default risklist
            - An empty risklist can be returned.
                - If ``validate`` is None: If it has headers, they will be returned.
                - If ``validate`` is not None, an empty list will be returned.

        Args:
            list (str): name of the risklist to download.
            entity_type (str, optional): Type of entity to get risklist for.
            format (str, optional): Format of the risklist.
            headers (bool, optional): Whether headers are included in the CSV.
            validate (BaseModel, optional): Validation model to use. Has to be subclass of pydantic
                BaseModel.

        Raises:
            RisklistNotAvailableError: if HTTP error occurs on risklist fetch
            ValidationError if any supplied parameter is of incorrect type

        Returns:
            Generator: Yields risklist rows or validated risklist models.
        """
        if validate and not issubclass(validate, BaseModel):
            raise ValueError('`validate` should be a subclass of Pydantic BaseModel or None')

        format = format if format else DEFAULT_RISKLIST_FORMAT  # noqa: A001
        risklist_type, url, params = self._get_risklist_url_and_params(list, entity_type, format)

        if risklist_type == 'fusion' and list.endswith('json'):
            return self._fetch_json_risklist(url, params, validate)
        return self._fetch_csv_risklist(url, params, validate, headers)

    @debug_call
    def _fetch_csv_risklist(
        self, url, params, validate, headers
    ) -> Generator[Union[dict, BaseModel, list[str]], None, None]:
        try:
            response = self.rf_client.request('get', url, params=params)
            response.raise_for_status()
        except (
            HTTPError,
            ConnectTimeout,
            ConnectionError,
            ReadTimeout,
            OSError,
            SSLError,
            KeyError,
        ) as e:
            raise RiskListNotAvailableError(message=str(e)) from e

        lines = response.iter_lines(decode_unicode=True)
        if headers:
            reader = csv.DictReader(lines)
            for row in reader:
                if validate:
                    yield validate(**row)
                else:
                    yield row
        else:
            reader = csv.reader(lines)
            yield from reader

    @debug_call
    def _fetch_json_risklist(
        self, url, params, validate
    ) -> Generator[Union[dict, BaseModel], None, None]:
        try:
            response = self.rf_client.request('get', url, params=params)
            response.raise_for_status()
            response = response.json()
        except (
            HTTPError,
            ConnectTimeout,
            ConnectionError,
            ReadTimeout,
            OSError,
            SSLError,
            JSONDecodeError,
        ) as e:
            raise RiskListNotAvailableError(message=str(e)) from e

        if validate:
            for row in response:
                yield validate(**row)
        else:
            yield from response

    def _get_risklist_url_and_params(self, filename: str, entity_type: str, format_type: str):
        """Helper function to determine URL and parameters based on entity type."""
        if entity_type:
            return (
                'risklist',
                EP_RISKLIST.format(entity_type),
                {'format': format_type, 'list': filename},
            )
        return 'fusion', EP_FUSION_FILES, {'path': filename}

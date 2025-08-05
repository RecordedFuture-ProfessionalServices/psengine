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
from typing import Annotated, Any, Optional, Union

from pydantic import BaseModel, validate_call
from requests.exceptions import (
    ConnectionError,  # noqa: A004
    ConnectTimeout,
    HTTPError,
    JSONDecodeError,
    ReadTimeout,
    SSLError,
)
from typing_extensions import Doc

from ..endpoints import EP_FUSION_FILES, EP_RISKLIST
from ..helpers import debug_call
from ..rf_client import RFClient
from .constants import DEFAULT_RISKLIST_FORMAT
from .errors import RiskListNotAvailableError


class RisklistMgr:
    """Manages requests for Recorded Future risk lists."""

    def __init__(
        self,
        rf_token: Annotated[Optional[str], Doc('Recorded Future API token.')] = None,
    ):
        """Initializes the RiskListMgr object."""
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    def fetch_risklist(
        self,
        list: Annotated[str, Doc('Name of the risklist to download.')],  # noqa: A002
        entity_type: Annotated[Optional[str], Doc('Type of entity to get risklist for.')] = None,
        format: Annotated[Optional[str], Doc('Format of the risklist.')] = None,  # noqa: A002
        headers: Annotated[bool, Doc('Whether headers are included in the CSV.')] = True,
        validate: Annotated[
            Optional[Any], Doc('Validation model to use. Must be a subclass of pydantic BaseModel.')
        ] = None,
    ) -> Annotated[
        Generator[Union[dict, list[str], BaseModel], None, None],
        Doc('Yields risklist rows or validated risklist models.'),
    ]:
        """Get a Recorded Future RiskList as generator.

        For a custom risklist, specify a `fusion_path` the `format` field is ignored
        when custom risklists are used.

        Warning:
            - If a specified list does't exist, the API returns the default risklist.
            - An empty risklist may be returned:
                - If `validate` is None and headers are included, headers are returned.
                - If `validate` is set, an empty list is returned.

        Example:
            Download and return entries as JSON:

            ```python
            from psengine.risklists import RisklistMgr, DefaultRiskList

            mgr = RisklistMgr()
            data = mgr.fetch_risklist('default', 'domain', validate=DefaultRiskList)
            for entry in data:
                print(entry.json())
            ```

        Raises:
            RisklistNotAvailableError: If an HTTP error occurs during risklist fetch.
            ValidationError: If any parameter is of incorrect type.
        """
        if validate and not issubclass(validate, BaseModel):
            raise ValueError('`validate` should be a subclass of Pydantic BaseModel or None')

        format = format or DEFAULT_RISKLIST_FORMAT  # noqa: A001
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

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
from typing import Optional, Union

from pydantic import validate_call

from .constants import DEFAULT_PAGE_LIMIT
from .sandbox import SampleSummary, SearchIn, SearchResult

from ..helpers import debug_call
from .client import SandboxClient

TRIAGE_URL = 'https://private.tria.ge/api/v0/'
SANDBOX_SAMPLE_SUMMARY = TRIAGE_URL + 'samples/{}/summary'
SANDBOX_SEARCH = TRIAGE_URL + 'search'


class SandboxMgr:
    """Manages requests for Recorded Future sandbox."""

    def __init__(self, api_token: str = None):
        """Initializes the `SandboxMgr` object.

        Args:
            api_token (str, optional): Sandbox API token.
        """
        self.log = logging.getLogger(__name__)
        self.sb_client = SandboxClient(api_token=api_token) if api_token else SandboxClient()

    @debug_call
    @validate_call
    def sample_summary(self, sample_id: str) -> SampleSummary:
        data = self.sb_client.request(
            'get',
            SANDBOX_SAMPLE_SUMMARY.format(sample_id),
        )
        return SampleSummary.model_validate(data.json())

    def search(
        self,
        file_hash: Optional[Union[list[str], str]] = None,
        family: Optional[Union[list[str], str]] = None,
        tag: Optional[Union[list[str], str]] = None,
        botnet: Optional[Union[list[str], str]] = None,
        platform: Optional[Union[list[str], str]] = None,
        extracted_c2_data: Optional[Union[list[str], str]] = None,
        wallet: Optional[Union[list[str], str]] = None,
        analysis_time: Optional[Union[list[str], str]] = None,
        query: Optional[str] = None,
        max_results: Optional[int] = DEFAULT_PAGE_LIMIT,
    ):
        # TODO: write about the id constraints
        params = {p: v for p, v in locals().items() if p not in ('self', 'query', 'max_results')}
        params = SearchIn.model_validate(params).to_query_out()

        if query:
            params.query += query

        data = self.sb_client.request_paged(
            'get', SANDBOX_SEARCH, params=params.model_dump(), max_samples=max_results
        )
        return [SearchResult.model_validate(e) for e in data]

    def submit_sample(): ...

    def fetch_sample(): ...

    def fetch_my_sample(): ...

    def download_sample(): ...

    def sample_overview(): ...

    def delete_sample(): ...

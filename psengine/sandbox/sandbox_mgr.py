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

import json
import logging
from pathlib import Path
from typing import Annotated, Literal, cast

from pydantic import Field, validate_call
from typing_extensions import Doc

from ..endpoints import (
    EP_SANDBOX_SAMPLES,
    EP_SANDBOX_SAMPLES_ID,
    EP_SANDBOX_SAMPLES_SUMMARY,
    EP_SANDBOX_SEARCH,
    SANDBOX_BASE_URLS,
)
from ..helpers import connection_exceptions, debug_call
from .client import SAMPLES_PER_PAGE, SandboxClient
from .constants import DEFAULT_PAGE_LIMIT
from .errors import SampleDeleteError, SampleFetchError, SampleSubmitError
from .sandbox import (
    DeleteOut,
    NetworkMode,
    SampleOut,
    SampleSummary,
    SearchIn,
    SearchResult,
    SubmitSampleIn,
    SubmitKind,
)

SandboxChoice = Literal['eu', 'usa', 'apj', 'public', 'private']


def validate_sandbox_choice(sandbox_choice: str) -> SandboxChoice:
    """Validate the sandbox selection and return a typed value."""
    if sandbox_choice not in SANDBOX_BASE_URLS:
        raise ValueError(
            f'Invalid sandbox choice: {sandbox_choice}. Must be one of {list(SANDBOX_BASE_URLS.keys())}'
        )
    return cast(SandboxChoice, sandbox_choice)


class SandboxMgr:
    """Manages requests for Recorded Future sandbox."""

    def __init__(
        self,
        api_token: Annotated[
            str | None,
            Doc('The Sandbox API token. Defaults to SANDBOX_TOKEN environment variable.'),
        ] = None,
        sandbox_choice: Annotated[
            SandboxChoice,
            Doc('Sandbox environment to use. Options: eu (default), usa, apj, public, private.'),
        ] = 'eu',
    ):
        """Initializes the `SandboxMgr` object."""
        self.log = logging.getLogger(__name__)
        self.base_url = SANDBOX_BASE_URLS[validate_sandbox_choice(sandbox_choice)]
        self.sb_client = SandboxClient(api_token=api_token) if api_token else SandboxClient()

    @debug_call
    @validate_call
    def sample_summary(self, sample_id: str) -> SampleSummary:
        endpoint = EP_SANDBOX_SAMPLES_SUMMARY.format(base_url=self.base_url, sample_id=sample_id)
        data = self.sb_client.request(
            'get',
            endpoint,
        )
        return SampleSummary.model_validate(data.json())

    def search(
        self,
        file_hash: list[str] | str | None = None,
        family: list[str] | str | None = None,
        tag: list[str] | str | None = None,
        botnet: list[str] | str | None = None,
        platform: list[str] | str | None = None,
        extracted_c2_data: list[str] | str | None = None,
        wallet: list[str] | str | None = None,
        analysis_time: list[str] | str | None = None,
        query: str | None = None,
        max_results: int | None = DEFAULT_PAGE_LIMIT,
    ):
        # TODO: write about the id constraints
        params = {p: v for p, v in locals().items() if p not in ('self', 'query', 'max_results')}
        params = SearchIn.model_validate(params).to_query_out()

        if query:
            params.query += query

        endpoint = EP_SANDBOX_SEARCH.format(base_url=self.base_url)
        data = self.sb_client.request_paged(
            'get', endpoint, params=params.model_dump(), max_samples=max_results
        )
        return [SearchResult.model_validate(e) for e in data]

    @debug_call
    @validate_call
    def fetch_samples(
        self,
        subset: Annotated[
            Literal['owned', 'public', 'org'],
            Doc(
                "Which samples to list: 'owned' (default — samples the requesting user can "
                "access), 'public' (only valid on the public cloud), or 'org' (all "
                'organisation samples).'
            ),
        ] = 'owned',
        max_results: Annotated[
            int,
            Field(ge=1),
            Doc('Total cap on samples returned across all pages.'),
        ] = DEFAULT_PAGE_LIMIT,
        samples_per_page: Annotated[
            int,
            Field(ge=1, le=200),
            Doc('Per-request page size (max 200).'),
        ] = SAMPLES_PER_PAGE,
    ) -> Annotated[
        list[SampleOut],
        Doc('List of SampleOut models.'),
    ]:
        """List samples visible to the token..

        Pagination is performed automatically, capping
        the total result count at `max_results`.

        Example:
            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            samples = mgr.fetch_samples(max_results=20)
            for s in samples:
                print(s.id_, s.status, s.kind)
            ```

        Endpoint:
            `GET /samples`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type or out of range.
        """
        endpoint = EP_SANDBOX_SAMPLES.format(base_url=self.base_url)
        data = self.sb_client.request_paged(
            'get',
            endpoint,
            params={'subset': subset},
            max_samples=max_results,
            samples_per_page=samples_per_page,
        )
        return [SampleOut.model_validate(e) for e in data]

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=SampleFetchError)
    def fetch_sample(
        self,
        sample_id: Annotated[
            str,
            Field(min_length=1),
            Doc('Sandbox sample ID, e.g. "260501-h4p7laawme".'),
        ],
    ) -> Annotated[SampleOut, Doc('Sample record returned by `GET /samples/{sample_id}`.')]:
        """Fetch a single sample by id.


        Example:
            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            sample = mgr.fetch_sample('260501-h4p7laawme')
            print(sample.id_, sample.status)
            for task in sample.tasks or []:
                print(task)
            ```

        Endpoint:
            `GET /samples/{sample_id}`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            SampleFetchError: If the API returns a non-2xx (e.g. 404 for an unknown id,
                401 for an inaccessible sample) or a connection error occurs.
        """
        endpoint = EP_SANDBOX_SAMPLES_ID.format(base_url=self.base_url, sample_id=sample_id)
        response = self.sb_client.request('get', endpoint)
        return SampleOut.model_validate(response.json())

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=SampleSubmitError)
    def submit_sample(
        self,
        kind: Annotated[
            SubmitKind,
            Doc("Submission kind: 'file', 'url', 'fetch' (sandbox downloads), or 'import'."),
        ],
        file_path: Annotated[
            Path | None,
            Doc("Path to the file to upload. Required when kind='file'."),
        ] = None,
        url: Annotated[
            str | None,
            Doc("Target URL. Required when kind in {'url', 'fetch'}."),
        ] = None,
        source_id: Annotated[
            str | None,
            Doc("Public Triage sample id to import. Required when kind='import'."),
        ] = None,
        interactive: Annotated[
            bool | None,
            Doc('Pause at static_analysis for manual profile selection.'),
        ] = None,
        password: Annotated[
            str | None,
            Doc('Decrypt password for archive submissions.'),
        ] = None,
        profiles: Annotated[
            list[dict] | None,
            Doc('Per-file profile mappings, e.g. [{"pick":"path","profile":"<id>"}].'),
        ] = None,
        user_tags: Annotated[
            list[str] | None,
            Doc('Custom tags attached to the submission (max 1kB total).'),
        ] = None,
        timeout: Annotated[
            int | None,
            Doc('Analysis duration in seconds, max 3600. Maps to `defaults.timeout`.'),
        ] = None,
        network: Annotated[
            NetworkMode | None,
            Doc('Network mode for the analysis VM. Maps to `defaults.network`.'),
        ] = None,
        geolocation: Annotated[
            str | None,
            Doc("VPN exit region tag. Requires `network='vpn'`. Maps to `defaults.geolocation`."),
        ] = None,
    ) -> Annotated[
        SearchResult,
        Doc('The freshly-created sample record (id, status, kind, submitted, ...).'),
    ]:
        """Submit a sample for analysis via `POST /samples`.

        Accepts one of four submission `kind`s: `file` (upload a local file),
        `url` (detonate a URL in a browser), `fetch` (sandbox downloads the file
        from the URL, then detonates), or `import` (import a public Triage sample
        by id). The manager builds a `SubmitIn` payload, validates kind-specific
        required fields, and posts it as `multipart/form-data` with the JSON body
        carried under the `_json` part.

        Example:
            Submit a URL:

            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            result = mgr.submit_sample(kind='url', url='https://example.com')
            print(result.id_, result.status)
            ```

            Submit a local file with custom tags:

            ```python
            from pathlib import Path
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            result = mgr.submit_sample(
                kind='file',
                file_path=Path('sample.exe'),
                user_tags=['triage', 'opportunistic'],
            )
            print(result.id_, result.status)
            ```

        Note:
            For `kind='fetch'` the returned record's `kind` is `'file'` — Triage
            materialises the URL into a downloaded file before analysis, so the
            submission is filed under `'file'` in the API.

        Endpoint:
            `POST /samples`

        Raises:
            ValidationError: If kind-specific required fields are missing (e.g.
                `kind='file'` without `file_path`) or if `geolocation` is set
                without `network='vpn'`.
            SampleSubmitError: If the API returns a non-2xx or a connection error occurs.
        """
        payload = SubmitSampleIn(
            kind=kind,
            file_path=file_path,
            url=url,
            source_id=source_id,
            interactive=interactive,
            password=password,
            profiles=profiles,
            user_tags=user_tags,
            timeout=timeout,
            network=network,
            geolocation=geolocation,
        )
        json_body, file_to_upload = payload.to_api_payload()

        files: dict = {'_json': (None, json.dumps(json_body))}
        if file_to_upload is not None:
            files['file'] = (
                file_to_upload.name,
                file_to_upload.read_bytes(),
                'application/octet-stream',
            )

        # `requests` sets the multipart/form-data Content-Type (with boundary) when
        # `files=` is passed — so drop our default JSON Content-Type header.
        headers = self.sb_client._prepare_headers()
        headers.pop('Content-Type', None)

        endpoint = EP_SANDBOX_SAMPLES.format(base_url=self.base_url)
        response = self.sb_client.request('post', endpoint, headers=headers, files=files)
        return SearchResult.model_validate(response.json())

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=SampleDeleteError)
    def delete_sample(
        self,
        sample_id: Annotated[
            str,
            Field(min_length=1),
            Doc('Sandbox sample ID to delete.'),
        ],
    ) -> Annotated[
        DeleteOut,
        Doc('`DeleteOut(deleted=True)` on success; any HTTP failure raises `SampleDeleteError`.'),
    ]:
        """Delete a sample by id.

        Returns `DeleteOut(deleted=True)` only on a successful 2xx response. Any
        HTTP failure raises `SampleDeleteError`; this method never returns
        `deleted=False`.

        Example:
            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            result = mgr.delete_sample('260501-h4p7laawme')
            print(result.deleted)
            ```

        Note:
            The Triage API returns `401 Unauthorized` for every non-success outcome
            — already deleted, never existed, no permission to delete, or expired
            token. Status alone cannot distinguish these cases; `SampleDeleteError`
            carries the raw API message verbatim for inspection.

        Endpoint:
            `DELETE /samples/{sample_id}`

        Raises:
            ValidationError: If `sample_id` is empty or of incorrect type.
            SampleDeleteError: If the API returns a non-2xx or a connection error occurs.
        """
        endpoint = EP_SANDBOX_SAMPLES_ID.format(base_url=self.base_url, sample_id=sample_id)
        self.sb_client.request('delete', endpoint)
        return DeleteOut(deleted=True)

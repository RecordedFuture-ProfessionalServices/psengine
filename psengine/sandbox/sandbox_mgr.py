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
import time
from pathlib import Path
from typing import Annotated, Literal, cast
from urllib.parse import quote

from pydantic import Field, validate_call
from requests.exceptions import HTTPError
from typing_extensions import Doc

from ..endpoints import (
    EP_SANDBOX_PROFILES,
    EP_SANDBOX_PROFILES_ID,
    EP_SANDBOX_SAMPLES,
    EP_SANDBOX_SAMPLES_BEHAVIORAL,
    EP_SANDBOX_SAMPLES_DOWNLOAD,
    EP_SANDBOX_SAMPLES_ID,
    EP_SANDBOX_SAMPLES_OVERVIEW,
    EP_SANDBOX_SAMPLES_PROFILE,
    EP_SANDBOX_SAMPLES_STATIC_REPORT,
    EP_SANDBOX_SAMPLES_SUMMARY,
    EP_SANDBOX_SEARCH,
    SANDBOX_BASE_URLS,
)
from ..helpers import MultiThreadingHelper, connection_exceptions, debug_call
from .client import SandboxClient
from .constants import (
    BEHAVIORAL_REPORT_WAIT_DEFAULT_TIMEOUT_SECONDS,
    BEHAVIORAL_REPORT_WAIT_INTERVAL_SECONDS,
    DEFAULT_PAGE_LIMIT,
    OVERVIEW_REPORT_WAIT_DEFAULT_TIMEOUT_SECONDS,
    OVERVIEW_REPORT_WAIT_INTERVAL_SECONDS,
    SAMPLES_PER_PAGE,
    STATIC_REPORT_WAIT_DEFAULT_TIMEOUT_SECONDS,
    STATIC_REPORT_WAIT_INTERVAL_SECONDS,
)
from .errors import (
    ProfileCreateError,
    ProfileDeleteError,
    ProfileFetchError,
    ProfileNotFoundError,
    ProfileUpdateError,
    SampleBehavioralReportError,
    SampleDeleteError,
    SampleFetchError,
    SampleFileFetchError,
    SampleOverviewError,
    SampleProfileError,
    SampleReportNotAvailableError,
    SampleReportNotFoundError,
    SampleSearchError,
    SamplesFetchError,
    SampleStaticReportError,
    SampleSubmitError,
    SampleSummaryError,
)
from .sandbox import (
    BehavioralReport,
    BehavioralReportFailure,
    BehavioralReportsResult,
    Browser,
    CreateUpdateProfileIn,
    NetworkMode,
    OverviewReport,
    Profile,
    ProfileDeleteOut,
    ProfileUpdateOut,
    Sample,
    SampleDeleteOut,
    SampleProfileOut,
    SampleSummary,
    SampleTasks,
    SearchIn,
    SetProfileIn,
    StaticAnalysisReport,
    SubmitKind,
    SubmitSampleIn,
)

SandboxChoice = Literal['eu', 'usa', 'apj', 'public', 'private']
SandboxSubset = Literal['owned', 'public', 'org']


def validate_sandbox_choice(sandbox_choice: str) -> SandboxChoice:
    """Validate the sandbox selection and return a typed value."""
    if sandbox_choice not in SANDBOX_BASE_URLS:
        raise ValueError(
            f'Invalid sandbox choice: {sandbox_choice}. '
            f'Must be one of {list(SANDBOX_BASE_URLS.keys())}'
        )
    return cast(SandboxChoice, sandbox_choice)


def _response_error_code(err: HTTPError) -> str | None:
    """Return the RF `error` code from the response envelope, or None if not decodable."""
    response = err.response
    if response is None:
        return None
    try:
        return response.json().get('error')
    except (ValueError, AttributeError):
        return None


def _report_404_code(err: HTTPError) -> str | None:
    """Return the RF `error` code from a 404 envelope, or None if not a decodable 404."""
    if err.response is None or err.response.status_code != 404:
        return None
    return _response_error_code(err)


def _raise_semantic_404(err: HTTPError, sample_id: str) -> None:
    """Map a discriminated report 404 to its semantic error; return for anything else.

    Used by the overview and static report fetches. `NOT_FOUND` means the sample does
    not exist; `NOT_AVAILABLE` (static) and `REPORT_NOT_AVAILABLE` (overview) mean the
    sample exists but the report is not ready yet. Any other error returns so the
    caller re-raises the original `HTTPError` for `@connection_exceptions` to wrap
    into the endpoint error.
    """
    code = _report_404_code(err)
    if code in ('NOT_AVAILABLE', 'REPORT_NOT_AVAILABLE'):
        raise SampleReportNotAvailableError(
            f'Report not available for sample {sample_id}. '
            'The sample may not have finished analysis yet.'
        ) from err
    if code == 'NOT_FOUND':
        raise SampleReportNotFoundError(f'Sample {sample_id} not found.') from err


class SandboxMgr:
    """Manages requests for Recorded Future sandbox."""

    def __init__(
        self,
        api_token: Annotated[
            str | None,
            Doc('The Sandbox API token. Defaults to RF_SANDBOX_TOKEN environment variable.'),
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
    @connection_exceptions(ignore_status_code=[], exception_to_raise=SampleSearchError)
    def search_samples(
        self,
        file_hash: Annotated[
            list[str] | str | None,
            Doc(
                'One or more file hashes (MD5/SHA1/SHA256/SHA512). Sent bare -- Triage '
                'auto-detects the hash type.'
            ),
        ] = None,
        family: Annotated[
            list[str] | str | None,
            Doc('Malware family tag(s), e.g. "emotet". Maps to the `family:` operator.'),
        ] = None,
        tag: Annotated[
            list[str] | str | None,
            Doc('Behaviour tag(s), e.g. "ransomware". Maps to the `tag:` operator.'),
        ] = None,
        botnet: Annotated[
            list[str] | str | None,
            Doc('Botnet tag(s). Maps to the `botnet:` operator.'),
        ] = None,
        wallet: Annotated[
            list[str] | str | None,
            Doc('Cryptocurrency wallet address(es). Maps to the `wallet:` operator.'),
        ] = None,
        ip: Annotated[
            list[str] | str | None,
            Doc('Extracted C2 IP address(es). Maps to the `ip:` operator.'),
        ] = None,
        domain: Annotated[
            list[str] | str | None,
            Doc('Extracted C2 domain(s). Maps to the `domain:` operator.'),
        ] = None,
        url: Annotated[
            list[str] | str | None,
            Doc('Extracted C2 URL(s). Maps to the `url:` operator.'),
        ] = None,
        from_date: Annotated[
            str | None,
            Doc(
                'Start of the submission-date window (`yyyy-mm-dd`). Maps to the `from:` operator.'
            ),
        ] = None,
        to_date: Annotated[
            str | None,
            Doc('End of the submission-date window (`yyyy-mm-dd`). Maps to the `to:` operator.'),
        ] = None,
        query: Annotated[
            str | None,
            Doc(
                'Raw Triage query string appended to the structured filters with `AND`. Use for '
                'operators not exposed as parameters or to build `OR`/`NOT` expressions.'
            ),
        ] = None,
        results_per_page: Annotated[
            int,
            Field(ge=1, le=200),
            Doc('Per-request page size (max 200).'),
        ] = SAMPLES_PER_PAGE,
        max_results: Annotated[
            int,
            Field(ge=1),
            Doc('Total cap on samples returned across all pages.'),
        ] = DEFAULT_PAGE_LIMIT,
    ) -> Annotated[
        list[Sample],
        Doc('List of Sample models matching the search.'),
    ]:
        """Search available analyses for a range of IoCs or file characteristics.

        Structured parameters are translated into Triage search operators and joined with `AND`
        (e.g. `family='emotet', tag='ransomware'` becomes `family:emotet AND tag:ransomware`).
        Each list-valued parameter may be a single string or a list of strings.

        Example:
            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            results = mgr.search_samples(tag='ransomware', from_date='2024-01-01')
            for r in results:
                print(r.id_, r.sha256, r.status)
            ```

        Note:
            A raw `query` is combined with the structured filters using `AND`. Pass `query`
            alone to run an arbitrary Triage query (e.g. `query='family:emotet OR family:qakbot'`).
            More information at: https://sandbox.recordedfuture.com/docs/cloud-api/search/

        Endpoint:
            `GET /search`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type or out of range.
            ValueError: If no filter is supplied (no structured parameter and no raw `query`).
            SampleSearchError: If the API returns a non-2xx (e.g. 400 `INVALID_QUERY` for a
                malformed query) or a connection error occurs.
        """
        search_query = SearchIn(
            file_hash=file_hash,
            family=family,
            tag=tag,
            botnet=botnet,
            wallet=wallet,
            ip=ip,
            domain=domain,
            url=url,
            from_date=from_date,
            to_date=to_date,
        ).to_query_out()

        if query:
            search_query.query = (
                f'{search_query.query} AND {query}' if search_query.query else query
            )

        if not search_query.query:
            raise ValueError(
                'search_samples requires at least one filter: pass a structured parameter '
                '(e.g. tag=, family=, file_hash=) or a raw `query` string.'
            )

        endpoint = EP_SANDBOX_SEARCH.format(base_url=self.base_url)
        data = self.sb_client.request_paged(
            'get',
            endpoint,
            params=search_query.model_dump(),
            max_results=max_results,
            results_per_page=results_per_page,
        )
        return [Sample.model_validate(e) for e in data]

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=SamplesFetchError)
    def fetch_samples(
        self,
        subset: Annotated[
            SandboxSubset,
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
        list[Sample],
        Doc('List of Sample models.'),
    ]:
        """List the collection of samples submitted to the sandbox.

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
            SamplesFetchError: If the API returns a non-2xx or a connection error occurs.
        """
        endpoint = EP_SANDBOX_SAMPLES.format(base_url=self.base_url)
        data = self.sb_client.request_paged(
            'get',
            endpoint,
            params={'subset': subset},
            max_results=max_results,
            results_per_page=samples_per_page,
        )
        return [Sample.model_validate(e) for e in data]

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
    ) -> Annotated[
        SampleTasks,
        Doc('SampleTasks model, the sample record plus its list of analysis tasks.'),
    ]:
        """Fetch a single sample by id.

        Unlike the list endpoints (which return bare `Sample` records), this returns a
        `SampleTasks` -- the same fields plus a `tasks` list of per-target analysis tasks
        (id, status, target, pick).

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
        return SampleTasks.model_validate(response.json())

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=SampleSummaryError)
    def fetch_sample_summary(
        self,
        sample_id: Annotated[
            str,
            Field(min_length=1),
            Doc('Sandbox sample ID, e.g. "260501-h4p7laawme".'),
        ],
    ) -> Annotated[
        SampleSummary,
        Doc('SampleSummary model, overall score/status plus a per-task breakdown.'),
    ]:
        """Fetch the short summary for a sample.

        The summary is a compact one-object overview: the overall `score` and `status`, the
        submission `target`, and a `tasks` map keyed by task id (e.g. `static1`, `behavioral1`,
        `urlscan1`) where each task carries its own kind, status and score.

        Example:
            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            summary = mgr.fetch_sample_summary('260501-h4p7laawme')
            print(summary.score, summary.status)
            for task_id, task in summary.tasks.items():
                print(task_id, task.kind, task.status, task.score)
            ```

        Note:
            `completed` is `None` until every task has finished -- in-progress samples
            (e.g. still in `static_analysis`) return a summary without it.

        Endpoint:
            `GET /samples/{sample_id}/summary`

        Raises:
            ValidationError: If `sample_id` is empty or of incorrect type.
            SampleSummaryError: If the API returns a non-2xx (e.g. 404 for an unknown id)
                or a connection error occurs.
        """
        endpoint = EP_SANDBOX_SAMPLES_SUMMARY.format(base_url=self.base_url, sample_id=sample_id)
        response = self.sb_client.request('get', endpoint)
        return SampleSummary.model_validate(response.json())

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=SampleFileFetchError)
    def fetch_sample_file(
        self,
        sample_id: Annotated[
            str,
            Field(min_length=1),
            Doc('Sandbox sample ID, e.g. "260501-h4p7laawme".'),
        ],
    ) -> Annotated[
        bytes,
        Doc('Raw bytes of the originally submitted file.'),
    ]:
        """Download the originally submitted file for a sample.

        Returns the raw file content exactly as it was submitted.

        Warning:
            This returns live, potentially malicious bytes. Handle them in an isolated
            environment.

        Example:
            ```python
            from pathlib import Path
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            content = mgr.fetch_sample_file('260501-h4p7laawme')
            Path('260501-h4p7laawme.bin').write_bytes(content)
            ```

        Endpoint:
            `GET /samples/{sample_id}/sample`

        Raises:
            ValidationError: If `sample_id` is empty or of incorrect type.
            SampleFileFetchError: If the API returns a non-2xx (e.g. 404 for an
                unknown id, 401 for a sample outside your organisation) or a
                connection error occurs.
        """
        endpoint = EP_SANDBOX_SAMPLES_DOWNLOAD.format(base_url=self.base_url, sample_id=sample_id)
        response = self.sb_client.request('get', endpoint)
        return response.content

    def _fetch_static_report_once(self, sample_id: str) -> StaticAnalysisReport:
        """Issue a single static report request.

        Isolated in its own method (rather than inlined in the polling `while` loop) so
        the `SampleReportNotAvailableError`/`SampleReportNotFoundError` raised by
        `_raise_semantic_404` -- itself invoked from inside an `except HTTPError`
        clause -- propagates all the way out of this call. A single `try` cannot add a
        handler for an exception raised by one of its own `except` clauses, so the
        polling loop's `except SampleReportNotAvailableError` needs to sit in a
        different `try` statement than this one.
        """
        endpoint = EP_SANDBOX_SAMPLES_STATIC_REPORT.format(
            base_url=self.base_url, sample_id=sample_id
        )
        try:
            response = self.sb_client.request('get', endpoint)
        except HTTPError as err:
            _raise_semantic_404(err, sample_id)
            raise
        return StaticAnalysisReport.model_validate(response.json())

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=SampleStaticReportError)
    def fetch_sample_static_report(
        self,
        sample_id: Annotated[
            str,
            Field(min_length=1),
            Doc('Sandbox sample ID, e.g. "260501-h4p7laawme".'),
        ],
        wait_until_ready: Annotated[
            bool,
            Doc('When true, keep polling until the static report is available.'),
        ] = False,
        timeout: Annotated[
            int,
            Field(ge=1),
            Doc('Max seconds to keep polling when wait_until_ready is true.'),
        ] = STATIC_REPORT_WAIT_DEFAULT_TIMEOUT_SECONDS,
    ) -> Annotated[
        StaticAnalysisReport,
        Doc('StaticAnalysisReport model'),
    ]:
        """Fetch the static analysis report for a sample.

        The static report is the pre-detonation pass: it identifies the submitted
        sample, scores it, lists any static `signatures`, enumerates the `files`
        table -- the submitted file plus everything unpacked from it (e.g. members
        of a submitted archive) -- and surfaces any malware configuration recovered
        at this stage in `extracted`.

        Example:
            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            report = mgr.fetch_sample_static_report('260501-h4p7laawme')
            print(report.analysis.score)
            for f in report.files:
                print(f.filename, f.sha256, f.kind)
            for cfg in report.extracted:
                print(cfg.config.family, cfg.config.c2)
            ```

            Block until the report is ready instead of handling the not-available error:

            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            report = mgr.fetch_sample_static_report(
                '260501-h4p7laawme', wait_until_ready=True, timeout=300
            )
            print(report.unpack_count)
            ```

        Note:
            `files`, `signatures` and `extracted` are always lists -- the API returns
            `null` for them when empty (e.g. `files` for a URL submission), which this
            method normalises to `[]`.

        Endpoint:
            `GET /samples/{sample_id}/reports/static`

        Raises:
            ValidationError: If `sample_id` is empty or of incorrect type, or `timeout`
                is less than 1.
            SampleReportNotAvailableError: If the sample exists but its static report is
                not available yet (404 `NOT_AVAILABLE`). When `wait_until_ready` is true,
                this is instead raised once polling exceeds `timeout` seconds without the
                report becoming available.
            SampleReportNotFoundError: If the sample does not exist (404 `NOT_FOUND`).
                Not retried, even when `wait_until_ready` is true.
            SampleStaticReportError: If the API returns any other non-2xx or a connection
                error occurs. Base class of the two 404 errors above.
        """
        if not wait_until_ready:
            return self._fetch_static_report_once(sample_id)

        started = time.monotonic()
        deadline = started + timeout
        while True:
            try:
                return self._fetch_static_report_once(sample_id)
            except SampleReportNotAvailableError:  # noqa: PERF203
                now = time.monotonic()
                if now >= deadline:
                    raise SampleReportNotAvailableError(
                        f'Static report for sample {sample_id} still not available after '
                        f'waiting {now - started:.0f}s.'
                    ) from None
                time.sleep(STATIC_REPORT_WAIT_INTERVAL_SECONDS)

    def _fetch_overview_report_once(self, sample_id: str) -> OverviewReport:
        """Issue a single overview report request.

        Isolated in its own method (mirroring `_fetch_static_report_once`) so the
        `SampleReportNotAvailableError`/`SampleReportNotFoundError` raised by
        `_raise_semantic_404` -- itself invoked from inside an `except HTTPError`
        clause -- propagates all the way out of this call. A single `try` cannot add a
        handler for an exception raised by one of its own `except` clauses, so the
        polling loop's `except SampleReportNotAvailableError` needs to sit in a
        different `try` statement than this one.
        """
        endpoint = EP_SANDBOX_SAMPLES_OVERVIEW.format(base_url=self.base_url, sample_id=sample_id)
        try:
            response = self.sb_client.request('get', endpoint)
        except HTTPError as err:
            _raise_semantic_404(err, sample_id)
            raise
        return OverviewReport.model_validate(response.json())

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=SampleOverviewError)
    def fetch_sample_overview_report(
        self,
        sample_id: Annotated[
            str,
            Field(min_length=1),
            Doc('Sandbox sample ID, e.g. "260501-h4p7laawme".'),
        ],
        wait_until_ready: Annotated[
            bool,
            Doc('When true, keep polling until the overview report is available.'),
        ] = False,
        timeout: Annotated[
            int,
            Field(ge=1),
            Doc('Max seconds to keep polling when wait_until_ready is true.'),
        ] = OVERVIEW_REPORT_WAIT_DEFAULT_TIMEOUT_SECONDS,
    ) -> Annotated[
        OverviewReport,
        Doc('OverviewReport model'),
    ]:
        """Fetch the overview report for a sample.

        The overview is the one-pager that combines every task's result: the overall
        `analysis` verdict (score, family, tags), the `sample` identity, recovered malware
        configs in `extracted`, the sample-level `signatures`, a per-`targets` breakdown
        (each target with its own IOCs and signature hits) and the `tasks` map keyed by
        task id (e.g. `static1`, `behavioral1`, `urlscan1`).

        Example:
            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            report = mgr.fetch_sample_overview_report('260501-h4p7laawme')
            print(report.analysis.score, report.analysis.family)
            for cfg in report.extracted:
                print(cfg.config.family if cfg.config else None, cfg.tasks)
            for target in report.targets:
                print(target.target, target.iocs.domains)
            for task_id, task in report.tasks.items():
                print(task_id, task.kind, task.status, task.score)
            ```

            Block until the report is ready instead of handling the not-available error:

            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            report = mgr.fetch_sample_overview_report(
                '260501-h4p7laawme', wait_until_ready=True, timeout=1800
            )
            print(report.analysis.score)
            ```

        Note:
            The overview is only generated once the sample reaches the `reported` state.
            A sample that exists but has not been fully analysed yet (e.g. still in
            `static_analysis`) returns `404 REPORT_NOT_AVAILABLE`, which raises
            `SampleReportNotAvailableError` -- distinct from a `404 NOT_FOUND` for an
            unknown sample id.

        Endpoint:
            `GET /samples/{sample_id}/overview.json`

        Raises:
            ValidationError: If `sample_id` is empty or of incorrect type, or `timeout`
                is less than 1.
            SampleReportNotAvailableError: If the sample exists but its overview is not
                available yet (404 `REPORT_NOT_AVAILABLE`). When `wait_until_ready` is
                true, this is instead raised once polling exceeds `timeout` seconds
                without the report becoming available.
            SampleReportNotFoundError: If the sample does not exist (404 `NOT_FOUND`).
                Not retried, even when `wait_until_ready` is true.
            SampleOverviewError: If the API returns any other non-2xx or a connection error
                occurs. Base class of the two 404 errors above.
        """
        if not wait_until_ready:
            return self._fetch_overview_report_once(sample_id)

        started = time.monotonic()
        deadline = started + timeout
        while True:
            try:
                return self._fetch_overview_report_once(sample_id)
            except SampleReportNotAvailableError:  # noqa: PERF203
                now = time.monotonic()
                if now >= deadline:
                    raise SampleReportNotAvailableError(
                        f'Overview report for sample {sample_id} still not available after '
                        f'waiting {now - started:.0f}s.'
                    ) from None
                time.sleep(OVERVIEW_REPORT_WAIT_INTERVAL_SECONDS)

    def _fetch_behavioral_reports_once(
        self, sample_id: str, max_workers: int = 0
    ) -> BehavioralReportsResult:
        """Issue a single sample lookup + per-task report fetch pass.

        Isolated in its own method (mirroring `_fetch_static_report_once`) so both the
        immediate-return and wait-loop paths in `fetch_behavioral_reports` share the same
        code. `SampleReportNotFoundError`/`SampleBehavioralReportError` raised on the
        sample lookup propagate straight out -- they are never retried by the wait loop.
        """
        endpoint = EP_SANDBOX_SAMPLES_ID.format(base_url=self.base_url, sample_id=sample_id)
        try:
            sample = SampleTasks.model_validate(self.sb_client.request('get', endpoint).json())
        except HTTPError as err:
            # Only NOT_FOUND is semantic here: the sample record itself is never
            # "not ready", and SampleReportNotAvailableError is outside this
            # endpoint's error hierarchy.
            if _report_404_code(err) == 'NOT_FOUND':
                raise SampleReportNotFoundError(f'Sample {sample_id} not found.') from err
            raise
        task_ids = [t.id_ for t in (sample.tasks or []) if t.id_.startswith('behavioral')]
        if not task_ids:
            return BehavioralReportsResult()

        if max_workers:
            outcomes = MultiThreadingHelper.multithread_it(
                max_workers,
                self._fetch_behavioral_report,
                iterator=task_ids,
                sample_id=sample_id,
            )
        else:
            outcomes = [
                self._fetch_behavioral_report(task_id, sample_id=sample_id) for task_id in task_ids
            ]

        reports, not_ready, failed = [], [], []
        for task_id, report, failure in outcomes:
            if report is not None:
                reports.append(report)
            elif failure is not None:
                failed.append(failure)
            else:
                not_ready.append(task_id)
        return BehavioralReportsResult(reports=reports, not_ready=not_ready, failed=failed)

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=SampleBehavioralReportError)
    def fetch_behavioral_reports(
        self,
        sample_id: Annotated[
            str,
            Field(min_length=1),
            Doc('Sandbox sample ID, e.g. "260501-h4p7laawme".'),
        ],
        max_workers: Annotated[
            int,
            Field(ge=0),
            Doc(
                'Threads for fetching the per-task reports concurrently. 0 (default) = sequential.'
            ),
        ] = 0,
        wait_until_ready: Annotated[
            bool,
            Doc('When true, keep polling until the result is complete, or timeout seconds elapse.'),
        ] = False,
        timeout: Annotated[
            int,
            Field(ge=1),
            Doc('Max seconds to keep polling when wait_until_ready is true.'),
        ] = BEHAVIORAL_REPORT_WAIT_DEFAULT_TIMEOUT_SECONDS,
    ) -> Annotated[
        BehavioralReportsResult,
        Doc(
            'Envelope with the finished `reports` (in task order), the `not_ready` task ids '
            'still awaiting analysis, and the `failed` task fetches.'
        ),
    ]:
        """Fetch every behavioral report for a sample.

        Convenience wrapper: it first fetches the sample to discover its tasks, then fetches
        the `report_triage.json` for each behavioral task. Per-task outcomes are returned in
        a `BehavioralReportsResult` envelope, so one unfinished or broken task does not hide
        the reports that are ready: finished reports land in `reports`, tasks whose report is
        not available yet (still queued/running) in `not_ready`, and tasks whose fetch failed
        for any other HTTP reason in `failed`.

        Every finished behavioral task lands in `reports`, whether its *analysis* succeeded
        or failed; a failed analysis' report carries an `errors` list and omits
        `processes`/`dumped`/`extracted`. Each report's `task_id` (e.g. `behavioral1`)
        identifies which task it belongs to. Non-behavioral tasks (`static*`, `urlscan*`)
        have no triage report and are skipped.

        Example:
            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            result = mgr.fetch_behavioral_reports('260501-h4p7laawme')
            for report in result.reports:
                print(report.task_id, report.analysis.score, report.analysis.platform)
                for proc in report.processes:
                    print('  ', proc.pid, proc.cmd)
            if not result.complete:
                print('still running, retry later:', result.not_ready)
            for failure in result.failed:
                print('gave up on:', failure.task_id, failure.status_code, failure.message)
            ```

            Block until every task has a report or a failure, instead of polling
            `result.complete` yourself:

            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            result = mgr.fetch_behavioral_reports(
                '260501-h4p7laawme', max_workers=10, wait_until_ready=True
            )
            if result.complete:
                print('no tasks pending')
            else:
                print('timed out, still pending:', result.not_ready)
            ```

        Note:
            `result.complete` is `True` when no report is still pending -- including when
            the sample has no behavioral tasks at all (`reports` is empty then). For samples
            with many behavioral tasks (e.g. multi-architecture Linux submissions), pass
            `max_workers` to fetch the per-task reports concurrently.

        Endpoint:
            `GET /samples/{sample_id}` then `GET /samples/{sample_id}/{task_id}/report_triage.json`

        Raises:
            ValidationError: If `sample_id` is empty, `max_workers` is out of range, or
                `timeout` is less than 1.
            SampleReportNotFoundError: If the sample does not exist (404 `NOT_FOUND`). Not
                retried, even when `wait_until_ready` is true.
            SampleBehavioralReportError: If the sample lookup fails with any other non-2xx,
                or a connection error occurs (on the lookup or any report fetch). Base class
                of the 404 error above. Per-task HTTP failures do *not* raise -- they land in
                the envelope's `not_ready`/`failed` buckets, and a `wait_until_ready` timeout
                is reflected the same way (`complete=False`) rather than as an exception.
        """
        if not wait_until_ready:
            return self._fetch_behavioral_reports_once(sample_id, max_workers=max_workers)

        deadline = time.monotonic() + timeout
        result = self._fetch_behavioral_reports_once(sample_id, max_workers=max_workers)
        while not result.complete and time.monotonic() < deadline:
            time.sleep(BEHAVIORAL_REPORT_WAIT_INTERVAL_SECONDS)
            result = self._fetch_behavioral_reports_once(sample_id, max_workers=max_workers)
        return result

    def _fetch_behavioral_report(
        self, task_id: str, sample_id: str
    ) -> tuple[str, BehavioralReport | None, BehavioralReportFailure | None]:
        """Fetch and parse a single behavioral task's `report_triage.json`.

        Returns `(task_id, report, None)` on success, `(task_id, None, None)` when the
        report is not (yet) available, and `(task_id, None, failure)` for any other HTTP
        error. Connection-level errors propagate to the caller.
        """
        endpoint = EP_SANDBOX_SAMPLES_BEHAVIORAL.format(
            base_url=self.base_url, sample_id=sample_id, task_id=task_id
        )
        try:
            data = self.sb_client.request('get', endpoint).json()
        except HTTPError as err:
            if _report_404_code(err) in ('NOT_AVAILABLE', 'REPORT_NOT_AVAILABLE'):
                return task_id, None, None
            self.log.warning(
                f'Behavioral report fetch failed for {sample_id}/{task_id}. Error: {err}'
            )
            failure = BehavioralReportFailure(
                task_id=task_id,
                status_code=err.response.status_code if err.response is not None else None,
                error=_response_error_code(err),
                message=str(err),
            )
            return task_id, None, failure
        data['task_id'] = task_id
        return task_id, BehavioralReport.model_validate(data), None

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
            str | list[str] | None,
            Doc(
                'Custom tags attached to the submission (max 1kB total). A bare string is '
                'coerced to a single-item list.'
            ),
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
        Sample,
        Doc('The Sample model.'),
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

        # `content_type_header=None` drops our default JSON Content-Type so `requests`
        # sets the multipart/form-data Content-Type (with boundary) for the `files=` upload.
        endpoint = EP_SANDBOX_SAMPLES.format(base_url=self.base_url)
        response = self.sb_client.request('post', endpoint, files=files, content_type_header=None)
        return Sample.model_validate(response.json())

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=SampleProfileError)
    def set_sample_profile(
        self,
        sample_id: Annotated[
            str,
            Field(min_length=1),
            Doc('Sandbox sample ID, e.g. "260501-h4p7laawme".'),
        ],
        auto: Annotated[
            bool,
            Doc(
                'Let the sandbox pick profiles itself. When False (default) you must '
                'supply `profiles`; when True you may narrow targets with `pick`.'
            ),
        ] = False,
        profiles: Annotated[
            list[dict] | None,
            Doc(
                'Manual per-target profile mappings (required when `auto=False`), e.g. '
                '`[{"pick": "unpack001/file.exe", "profile": "<id-or-name>"}]`. `pick` is '
                'a target path from the static report (`files[].relpath`). `profile` may '
                'be a string (profile id or name) or a dict; a string is wrapped into the '
                '`{"id": ...}` object the API expects.'
            ),
        ] = None,
        pick: Annotated[
            list[str] | None,
            Doc(
                'Target filenames to advance when `auto=True` (empty/None = all). Only '
                'valid when `auto=True`.'
            ),
        ] = None,
    ) -> Annotated[
        SampleProfileOut,
        Doc('SampleProfileOut model'),
    ]:
        """Set the analysis profile for an interactive sample.

        Only valid while the sample is paused in `static_analysis` -- i.e. it was
        submitted with `interactive=True`. Setting the profile advances the sample
        into the analysis queue.

        Example:
            Manual selection (one mapping per target):

            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            mgr.set_sample_profile(
                '260501-h4p7laawme',
                profiles=[{'pick': 'file.exe', 'profile': 'w7_long'}],
            )
            ```

            Let the sandbox pick profiles automatically:

            ```python
            mgr.set_sample_profile('260501-h4p7laawme', auto=True)
            ```

        Endpoint:
            `POST /samples/{sample_id}/profile`

        Raises:
            ValidationError: If `sample_id` is empty, or the `auto`/`profiles`/`pick`
                combination is invalid (e.g. `auto=False` without `profiles`).
            SampleProfileError: If the API returns a non-2xx (e.g. the sample is not
                in `static_analysis`) or a connection error occurs.
        """
        payload = SetProfileIn(auto=auto, profiles=profiles, pick=pick)
        endpoint = EP_SANDBOX_SAMPLES_PROFILE.format(base_url=self.base_url, sample_id=sample_id)
        self.sb_client.request('post', endpoint, data=payload.to_api_payload())
        return SampleProfileOut(success=True)

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
        SampleDeleteOut,
        Doc('SampleDeleteOut model'),
    ]:
        """Delete a sample by id.

        Returns `SampleDeleteOut(deleted=True)` only on a successful 2xx response.
        Any HTTP failure raises `SampleDeleteError`; this method never returns
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
        return SampleDeleteOut(deleted=True)

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ProfileFetchError)
    def fetch_profiles(
        self,
    ) -> Annotated[list[Profile], Doc('List of Profile models.')]:
        """List analysis profiles.

        Profiles are company-scoped analysis configurations (OS tags, network mode,
        timeout, geolocation, browser).

        Example:
            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            profiles = mgr.fetch_profiles()
            for p in profiles:
                print(p.id_, p.name, p.network, p.tags)
            ```

        Endpoint:
            `GET /profiles`

        Raises:
            ProfileFetchError: If the API returns a non-2xx or a connection error occurs.
        """
        endpoint = EP_SANDBOX_PROFILES.format(base_url=self.base_url)
        response = self.sb_client.request('get', endpoint)
        return [Profile.model_validate(e) for e in response.json()['data']]

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ProfileNotFoundError)
    def fetch_profile(
        self,
        profile_id: Annotated[
            str,
            Field(min_length=1),
            Doc('Profile ID or name.'),
        ],
    ) -> Annotated[
        Profile,
        Doc('Profile model'),
    ]:
        """Fetch a single analysis profile by ID or name.

        The API accepts either the ID assigned at create time or the profile
        name. Prefer the ID for stable references — renames invalidate
        name-based lookups.

        Example:
            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            profile = mgr.fetch_profile('022b8c4e-22ab-46a4-ac49-a2732b2412b7')
            print(profile.id_, profile.name, profile.tags)
            ```

        Endpoint:
            `GET /profiles/{profile_id}`

        Raises:
            ValidationError: If `profile_id` is empty or of incorrect type.
            ProfileNotFoundError: If the API returns a non-2xx (e.g. 404 for an
                unknown profile id/name) or a connection error occurs.
        """
        endpoint = EP_SANDBOX_PROFILES_ID.format(
            base_url=self.base_url, profile_id=quote(profile_id, safe='.')
        )
        response = self.sb_client.request('get', endpoint)
        return Profile.model_validate(response.json())

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ProfileCreateError)
    def create_profile(
        self,
        name: Annotated[
            str,
            Field(min_length=1),
            Doc('Profile name. Must be unique within the company.'),
        ],
        tags: Annotated[
            str | list[str],
            Field(min_length=1),
            Doc(
                'Resource tags, e.g. `["os:windows10-2004-x64", "locale:en-us"]`. '
                'A bare string is coerced to a single-item list.'
            ),
        ],
        timeout: Annotated[
            int,
            Field(ge=1, le=3600),
            Doc('Analysis duration in seconds (1–3600).'),
        ],
        network: Annotated[
            NetworkMode | None,
            Doc('Network mode applied to analysis VMs using this profile.'),
        ] = None,
        geolocation: Annotated[
            str | list[str] | None,
            Doc(
                'Region tag(s). The API rejects this unless `network="vpn"`. '
                'A bare string is coerced to a single-item list.'
            ),
        ] = None,
        browser: Annotated[
            Browser | None,
            Doc("Browser used by analyses. One of 'chrome', 'firefox', 'ie11', 'microsoft-edge'."),
        ] = None,
    ) -> Annotated[
        Profile,
        Doc('The newly-created profile.'),
    ]:
        """Create a new analysis profile.

        Example:
            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            profile = mgr.create_profile(
                name='my-profile',
                tags=['os:windows10-2004-x64', 'locale:en-us'],
                timeout=120,
                network='internet',
                browser='firefox',
            )
            print(profile.id_, profile.name, profile.options)
            ```

        Endpoint:
            `POST /profiles`

        Raises:
            ValidationError: If `name`/`tags` are empty, `timeout` is out of range,
                or `browser` is not one of the allowed values.
            ProfileCreateError: If the API returns a non-2xx (e.g. 400 for an
                invalid `geolocation`+`network` combination, 409 if the name
                collides) or a connection error occurs.
        """
        payload = CreateUpdateProfileIn(
            name=name,
            tags=tags,
            timeout=timeout,
            network=network,
            geolocation=geolocation,
            browser=browser,
        )
        endpoint = EP_SANDBOX_PROFILES.format(base_url=self.base_url)
        response = self.sb_client.request('post', endpoint, data=payload.to_api_payload())
        return Profile.model_validate(response.json())

    @debug_call
    @validate_call
    @connection_exceptions(
        ignore_status_code=[404],
        exception_to_raise=ProfileUpdateError,
        on_ignore_return=ProfileUpdateOut(updated=False),
    )
    def update_profile(
        self,
        profile_id: Annotated[
            str,
            Field(min_length=1),
            Doc(
                'Profile ID or name. Renaming via `name=` is allowed, but stale '
                'name-based lookups will break afterwards -- prefer the ID for '
                'stable references.'
            ),
        ],
        name: Annotated[
            str,
            Field(min_length=1),
            Doc('Profile name. May differ from the existing name (rename).'),
        ],
        tags: Annotated[
            str | list[str],
            Field(min_length=1),
            Doc(
                'Resource tags, e.g. `["os:windows10-2004-x64", "locale:en-us"]`. '
                'A bare string is coerced to a single-item list.'
            ),
        ],
        timeout: Annotated[
            int,
            Field(ge=1, le=3600),
            Doc('Analysis duration in seconds (1–3600).'),
        ],
        network: Annotated[
            NetworkMode | None,
            Doc('Network mode applied to analysis VMs using this profile.'),
        ] = None,
        geolocation: Annotated[
            str | list[str] | None,
            Doc(
                'Region tag(s). The API rejects this unless `network="vpn"`. '
                'A bare string is coerced to a single-item list.'
            ),
        ] = None,
        browser: Annotated[
            Browser | None,
            Doc("Browser used by analyses. One of 'chrome', 'firefox', 'ie11', 'microsoft-edge'."),
        ] = None,
    ) -> Annotated[
        ProfileUpdateOut,
        Doc('ProfileUpdateOut model'),
    ]:
        """Update an existing analysis profile.

        The PUT is a **full replace**: all fields except `id` must be submitted.
        Any optional field omitted from this call is cleared on the server --
        e.g. calling without `browser` removes any browser previously set on
        the profile.

        Idempotent on 404: updating a profile that doesn't exist (already
        deleted, wrong id/name) returns `UpdateOut(updated=False)` rather than
        raising, so callers can check `result.updated` to know whether the
        target existed. Every other failure mode (401/403 auth, 409 name
        collision, 5xx, connection errors) still raises `ProfileUpdateError`.

        The API returns `200` with an empty body on success (it does not echo
        the updated profile), so this method returns `UpdateOut(updated=True)`
        rather than a `Profile`. Call `fetch_profile()` afterwards if you need
        the echoed record.

        Example:
            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            result = mgr.update_profile(
                profile_id='022b8c4e-22ab-46a4-ac49-a2732b2412b7',
                name='my-profile-v2',
                tags=['os:windows10-2004-x64', 'locale:en-us'],
                timeout=180,
                network='internet',
                browser='firefox',
            )
            if result.updated:
                print('updated')
            else:
                print('target profile did not exist')
            ```

        Endpoint:
            `PUT /profiles/{profile_id}`

        Raises:
            ValidationError: If `name`/`tags` are empty, `timeout` is out of range,
                or `browser` is not one of the allowed values.
            ProfileUpdateError: If the API returns a non-2xx other than 404
                (e.g. 409 if the new `name` collides) or a connection error occurs.
        """
        payload = CreateUpdateProfileIn(
            name=name,
            tags=tags,
            timeout=timeout,
            network=network,
            geolocation=geolocation,
            browser=browser,
        )
        endpoint = EP_SANDBOX_PROFILES_ID.format(
            base_url=self.base_url, profile_id=quote(profile_id, safe='.')
        )
        self.sb_client.request('put', endpoint, data=payload.to_api_payload())
        return ProfileUpdateOut(updated=True)

    @debug_call
    @validate_call
    @connection_exceptions(
        ignore_status_code=[404],
        exception_to_raise=ProfileDeleteError,
        on_ignore_return=ProfileDeleteOut(deleted=False),
    )
    def delete_profile(
        self,
        profile_id: Annotated[
            str,
            Field(min_length=1),
            Doc('Profile ID or name.'),
        ],
    ) -> Annotated[
        ProfileDeleteOut,
        Doc('ProfileDeleteOut model'),
    ]:
        """Delete an analysis profile.

        Idempotent on 404: deleting a profile that doesn't exist (already deleted,
        wrong id/name, etc.) returns `ProfileDeleteOut(deleted=False)` rather than
        raising, so callers can do best-effort cleanup without `try/except`. Every
        other failure mode (401/403 auth, 5xx, connection errors) still raises
        `ProfileDeleteError`.

        Example:
            ```python
            from psengine.sandbox import SandboxMgr

            mgr = SandboxMgr(sandbox_choice='eu')
            result = mgr.delete_profile('022b8c4e-22ab-46a4-ac49-a2732b2412b7')
            if result.deleted:
                print('removed')
            else:
                print('was already gone')
            ```

        Endpoint:
            `DELETE /profiles/{profile_id}`

        Raises:
            ValidationError: If `profile_id` is empty or of incorrect type.
            ProfileDeleteError: If the API returns a non-2xx other than 404, or
                a connection error occurs.
        """
        endpoint = EP_SANDBOX_PROFILES_ID.format(
            base_url=self.base_url, profile_id=quote(profile_id, safe='.')
        )
        self.sb_client.request('delete', endpoint)
        return ProfileDeleteOut(deleted=True)

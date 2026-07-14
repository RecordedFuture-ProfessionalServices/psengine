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

from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, field_validator, model_validator

from ..common_models import RFBaseModel
from ..helpers import Validators
from .models.analysis import LightweightSampleTask, Meta, Task
from .models.behavioral_report import (
    BehavioralAnalysis,
    BehavioralDumped,
    BehavioralError,
    BehavioralNetwork,
    BehavioralProcess,
    BehavioralReportTask,
    BehavioralSample,
)
from .models.overview_report import (
    OverviewAnalysis,
    OverviewError,
    OverviewExtracted,
    OverviewSample,
    OverviewSignature,
    OverviewTarget,
    OverviewTask,
)
from .models.static_report import (
    StaticReportAnalysis,
    StaticReportExtracted,
    StaticReportFile,
    StaticReportSample,
    StaticReportSignature,
    StaticReportTask,
)

SubmitKind = Literal['file', 'url', 'fetch', 'import']
NetworkMode = Literal['internet', 'drop', 'tor', 'vpn', 'sim200', 'sim404', 'simnx']
Browser = Literal['chrome', 'firefox', 'ie11', 'microsoft-edge']

_SEARCH_FIELD_PREFIX_MAP = {
    'file_hash': '',
    'family': 'family:',
    'tag': 'tag:',
    'botnet': 'botnet:',
    'wallet': 'wallet:',
    'ip': 'ip:',
    'domain': 'domain:',
    'url': 'url:',
    'from_date': 'from:',
    'to_date': 'to:',
}


class SampleSummary(RFBaseModel):
    """Short summary for a sample returned by `GET /samples/{sample_id}/summary`."""

    sample: str
    status: str
    custom: str
    owner: str
    target: str
    created: datetime
    completed: datetime | None = None
    score: int
    sha256: str | None = None
    org_id: str | None = None
    meta: Meta | None = None
    tasks: dict[str, Task] = Field(default_factory=dict)


class SearchQuery(RFBaseModel):
    """Triage query string wrapper sent as the `query` param of `GET /search`."""

    query: str


class SearchIn(RFBaseModel):
    """Structured search filters translated into Triage search operators."""

    file_hash: list[str] | str | None = None
    family: list[str] | str | None = None
    tag: list[str] | str | None = None
    botnet: list[str] | str | None = None
    wallet: list[str] | str | None = None
    ip: list[str] | str | None = None
    domain: list[str] | str | None = None
    url: list[str] | str | None = None
    from_date: str | None = None
    to_date: str | None = None

    @field_validator(
        'file_hash',
        'family',
        'tag',
        'botnet',
        'wallet',
        'ip',
        'domain',
        'url',
        mode='before',
    )
    @classmethod
    def _str_to_list(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            return [v] if v else []
        if isinstance(v, list):
            return [s.strip() for s in v if isinstance(s, str) and s.strip()]
        return v

    def to_query_out(self, join_operator='AND') -> SearchQuery:
        """Join the structured filters into a single Triage query string."""
        parts = []
        for field_name, values in self.model_dump(exclude_none=True).items():
            if not values:
                continue

            prefix = _SEARCH_FIELD_PREFIX_MAP[field_name]
            items = [values] if isinstance(values, str) else values
            for val in items:
                value = val if val.startswith(prefix) else f'{prefix}{val}'
                parts.append(value)

        return SearchQuery(query=f' {join_operator} '.join(parts))


class Sample(RFBaseModel):
    """Sample record returned by `/search` and `/samples`."""

    id_: str = Field(alias='id')
    status: str
    kind: str
    filename: str | None = None
    submitted: datetime
    completed: datetime | None = None
    sha256: str | None = None
    url: str | None = None
    user_id: str


class SampleTasks(Sample):
    """Sample record with tasks returned by `GET /samples/{sample_id}`."""

    tasks: list[LightweightSampleTask] | None = None


class StaticAnalysisReport(RFBaseModel):
    """Static report returned by `GET /samples/{sample_id}/reports/static`.

    Covers the pre-detonation pass: sample identity, the static task, a score,
    any static `signatures`, and the `files` table (the submitted file plus
    everything unpacked from it, e.g. archive members).
    """

    version: str | None = None
    build: str | None = None
    sample: StaticReportSample
    task: StaticReportTask
    analysis: StaticReportAnalysis
    signatures: list[StaticReportSignature] = Field(default_factory=list)
    files: list[StaticReportFile] = Field(default_factory=list)
    extracted: list[StaticReportExtracted] = Field(default_factory=list)
    unpack_count: int | None = None
    error_count: int | None = None

    # The API sends `null` for these when there's nothing (e.g. `files: null` for URL
    # reports) -- coerce to [] so the fields are always iterable.
    _coerce_lists = field_validator('signatures', 'files', 'extracted', mode='before')(
        Validators.none_to_empty_list
    )


class OverviewReport(RFBaseModel):
    """Overview report returned by `GET /samples/{sampleID}/overview.json`.

    The one-pager that combines every task's result: the overall `analysis` verdict,
    the `sample` identity, recovered malware `extracted` configs, `signatures`, the
    per-`targets` breakdown (each with its own IOCs and signatures) and the `tasks` map.
    """

    version: str | None = None
    build: str | None = None
    analysis: OverviewAnalysis
    sample: OverviewSample
    signatures: list[OverviewSignature] = Field(default_factory=list)
    extracted: list[OverviewExtracted] = Field(default_factory=list)
    targets: list[OverviewTarget] = Field(default_factory=list)
    tasks: dict[str, OverviewTask] = Field(default_factory=dict)
    errors: list[OverviewError] = Field(default_factory=list)

    # The API sends `targets: null` when there are no targets -- coerce to [] so the
    # field is always iterable.
    _coerce_targets = field_validator('targets', mode='before')(Validators.none_to_empty_list)


class BehavioralReport(RFBaseModel):
    """Behavioral report returned by `GET /samples/{sampleID}/{taskID}/report_triage.json`.

    Covers a single behavioral (detonation) task: the `sample`/`task` identity, the run
    `analysis` verdict, the `processes` tree, `signatures`, `network` activity (flows,
    requests, IP metadata), `dumped` artifacts and any `extracted` configs. Failed tasks
    carry an `errors` list and omit `processes`/`dumped`/`extracted`.

    `task_id` is populated by `SandboxMgr.fetch_behavioral_reports` (e.g. `behavioral1`)
    so each report in the returned list is identifiable; it is not part of the API body.
    """

    task_id: str | None = None
    version: str | None = None
    build: str | None = None
    sample: BehavioralSample
    task: BehavioralReportTask
    analysis: BehavioralAnalysis
    tags: list[str] = Field(default_factory=list)
    signatures: list[OverviewSignature] = Field(default_factory=list)
    processes: list[BehavioralProcess] = Field(default_factory=list)
    network: BehavioralNetwork = Field(default_factory=BehavioralNetwork)
    dumped: list[BehavioralDumped] = Field(default_factory=list)
    extracted: list[OverviewExtracted] = Field(default_factory=list)
    errors: list[BehavioralError] = Field(default_factory=list)

    # The API sends `tags: null` for the top-level tags -- coerce to [] so it is iterable.
    _coerce_tags = field_validator('tags', mode='before')(Validators.none_to_empty_list)


class BehavioralReportFailure(RFBaseModel):
    """A behavioral task whose report fetch failed for a reason other than "not ready yet".

    Constructed by `SandboxMgr.fetch_behavioral_reports` (not an API body): identifies the
    task and carries the HTTP evidence -- the status code, the RF error-envelope code when
    one was decodable (e.g. `NOT_FOUND`) and the raw error message.
    """

    task_id: str
    status_code: int | None = None
    error: str | None = None
    message: str | None = None


class BehavioralReportsResult(RFBaseModel):
    """Result of a `SandboxMgr.fetch_behavioral_reports` call.

    Batch envelope over the sample's behavioral tasks, so one unfinished or broken task
    does not hide the reports that are ready:

    - `reports`: one `BehavioralReport` per task whose `report_triage.json` was fetched,
      in task order. Failed *analyses* land here too (their report carries an `errors`
      list) -- the buckets classify the report fetch, not the analysis verdict.
    - `not_ready`: ids of tasks whose report is not available *yet* (404 `NOT_AVAILABLE`:
      the task is still queued or running). Poll again later.
    - `failed`: tasks whose report fetch failed for any other HTTP reason (unexpected
      404 `NOT_FOUND`, 5xx, ...), each with its status code and error message. These are
      terminal -- retrying is unlikely to help.

    `complete` is `True` when nothing is pending (`not_ready` is empty) -- including when
    the sample has no behavioral tasks at all -- so poll loops can simply retry until
    `result.complete`.
    """

    reports: list[BehavioralReport] = []
    not_ready: list[str] = []
    failed: list[BehavioralReportFailure] = []

    @property
    def complete(self) -> bool:
        """Whether no task report is still pending. `failed` tasks are terminal."""
        return not self.not_ready


class SampleDeleteOut(RFBaseModel):
    """Result of a `DELETE /samples/{sample_id}` call.

    The Sandbox API returns an empty body on success; the manager constructs this
    model with `deleted=True` when the HTTP request succeeds.
    """

    deleted: bool


class SampleProfileOut(RFBaseModel):
    """Result of a `POST /samples/{sample_id}/profile` call.

    The Sandbox API returns an empty body on success; the manager constructs this
    model with `success=True` when the HTTP request succeeds.
    """

    success: bool


class SubmitSampleIn(RFBaseModel):
    """Validated payload for `POST /samples`.

    Flat fields collected from the public `submit_sample` kwargs. `@model_validator`
    enforces required-per-kind and the geolocation-needs-vpn rule. `to_api_payload()`
    produces the `_json` dict (with nested `defaults`) and the file path (if any)
    for multipart upload.
    """

    kind: SubmitKind
    file_path: Path | None = None
    url: str | None = None
    source_id: str | None = None
    interactive: bool | None = None
    password: str | None = None
    profiles: list[dict] | None = None
    user_tags: Annotated[list[str] | None, BeforeValidator(Validators.convert_str_to_list)] = None
    timeout: int | None = Field(default=None, ge=1, le=3600)
    network: NetworkMode | None = None
    geolocation: str | None = None

    @model_validator(mode='after')
    def _check_required_per_kind(self):
        if self.kind == 'file' and self.file_path is None:
            raise ValueError("kind='file' requires `file_path`")
        if self.kind in ('url', 'fetch') and not self.url:
            raise ValueError(f'kind={self.kind!r} requires `url`')
        if self.kind == 'import' and not self.source_id:
            raise ValueError("kind='import' requires `source_id`")
        if self.kind != 'file' and self.file_path is not None:
            raise ValueError(f"`file_path` only valid when kind='file' (got kind={self.kind!r})")
        if self.kind not in ('url', 'fetch') and self.url is not None:
            raise ValueError(
                f"`url` only valid when kind in {{'url','fetch'}} (got kind={self.kind!r})"
            )
        if self.kind != 'import' and self.source_id is not None:
            raise ValueError(f"`source_id` only valid when kind='import' (got kind={self.kind!r})")
        return self

    @model_validator(mode='after')
    def _check_geolocation_needs_vpn(self):
        if self.geolocation is not None and self.network != 'vpn':
            raise ValueError("`geolocation` requires `network='vpn'`")
        return self

    @model_validator(mode='after')
    def _check_file_path_exists(self):
        if self.file_path is not None and not self.file_path.is_file():
            raise ValueError(f'`file_path` does not point to an existing file: {self.file_path}')
        return self

    def to_api_payload(self) -> tuple[dict, Path | None]:
        """Build the multipart payload for `POST /samples`.

        Despite what the API docs' curl examples suggest, the `url` field for
        kind in {'url','fetch'} must be carried *inside* the `_json` body, not
        as a separate multipart form field. The only top-level multipart field
        besides `_json` is the `file` binary for kind='file'.

        Returns:
            - `json_body`: dict to JSON-encode under the `_json` multipart field.
            - `file_path`: path to upload as the `file` field for kind='file',
              else None.
        """
        body: dict = {'kind': self.kind}
        if self.kind in ('url', 'fetch'):
            body['url'] = self.url
        # For kind='import' the public Triage reference (URL or bare sample id)
        # is carried in the same `url` field as url/fetch. We keep `source_id`
        # as the public-facing param name because it's semantically clearer.
        elif self.kind == 'import':
            body['url'] = self.source_id

        optional = {
            'interactive': self.interactive,
            'password': self.password,
            'profiles': self.profiles,
            'user_tags': self.user_tags,
        }
        body.update({k: v for k, v in optional.items() if v is not None})

        defaults = {
            k: v
            for k, v in (
                ('timeout', self.timeout),
                ('network', self.network),
                ('geolocation', self.geolocation),
            )
            if v is not None
        }
        if defaults:
            body['defaults'] = defaults

        return body, self.file_path


class SetProfileIn(RFBaseModel):
    """Validated payload for `POST /samples/{sample_id}/profile`.

    Two mutually-exclusive modes, keyed off `auto`:
    - `auto=False` (manual): `profiles` is required -- one mapping per target,
      e.g. `[{"pick": "unpack001/file.exe", "profile": "<id-or-name>"}]`. Each
      `profile` may be a string (an id *or* a human-readable name; wrapped to
      the `{"id": ...}` object the API expects) or a dict passed through as-is.
    - `auto=True`: the sandbox picks profiles itself; `pick` optionally narrows
      which targets to advance (empty/None = all).
    """

    auto: bool = False
    profiles: list[dict] | None = None
    pick: list[str] | None = None

    @model_validator(mode='after')
    def _check_mode(self):
        if self.auto:
            if self.profiles is not None:
                raise ValueError('`profiles` is only valid when auto=False')
        else:
            if not self.profiles:
                raise ValueError('auto=False requires a non-empty `profiles`')
            if self.pick is not None:
                raise ValueError('`pick` is only valid when auto=True')
        return self

    def to_api_payload(self) -> dict:
        """Build the JSON body for `POST /samples/{sample_id}/profile`.

        A string `profile` (id or name) is wrapped into the `{"id": ...}` object
        the API requires; a dict `profile` is sent verbatim.
        """
        if self.auto:
            return {'auto': True, 'pick': self.pick or []}

        normalised = []
        for entry in self.profiles:
            mapped = dict(entry)
            profile = mapped.get('profile')
            if isinstance(profile, str):
                mapped['profile'] = {'id': profile}
            normalised.append(mapped)
        return {'auto': False, 'profiles': normalised}


class ProfileOptions(RFBaseModel):
    """Per-profile analysis knobs returned under `Profile.options`.

    Today the only documented key is `browser`. Inherits `RFBaseModel`'s
    default `extra='ignore'` policy so newly-introduced option keys on the
    API don't break parsing.
    """

    browser: Browser | None = None

    # Real-world payloads show `"browser": ""` for profiles created without a browser
    # choice — normalise to None so the Browser Literal validator doesn't reject it.
    _browser_empty_to_none = field_validator('browser', mode='before')(Validators.empty_str_to_none)


class ProfileDeleteOut(RFBaseModel):
    """Result of a `DELETE /profiles/{profile_id}` call.

    The Sandbox API returns an empty body on success; the manager constructs this
    model with `deleted=True` on a 2xx response and `deleted=False` when the
    profile didn't exist (404, treated as idempotent).
    """

    deleted: bool


class ProfileUpdateOut(RFBaseModel):
    """Result of a `PUT /profiles/{profile_id}` call.

    `PUT /profiles/{id}` returns `200` with an empty body `{}` on success rather
    than echoing the updated profile, so the manager constructs this model with
    `updated=True` when the HTTP request succeeds.
    """

    updated: bool


class Profile(RFBaseModel):
    """Analysis profile record returned by `/profiles`."""

    id_: str = Field(alias='id')
    name: str
    tags: list[str] = Field(default_factory=list)
    network: NetworkMode | None = None
    geolocation: list[str] = Field(default_factory=list)
    timeout: int | None = None
    options: ProfileOptions | None = None

    # API returns either `null` or `[]` for unset geolocation; both normalise to [].
    _coerce_geolocation = field_validator('geolocation', mode='before')(
        Validators.none_to_empty_list
    )

    # POST /profiles echoes `network=""` for profiles created without a network mode.
    _network_empty_to_none = field_validator('network', mode='before')(Validators.empty_str_to_none)


class CreateUpdateProfileIn(RFBaseModel):
    """Validates payload for `POST /profiles` and `PUT /profiles/{id}`."""

    name: str = Field(min_length=1)
    tags: Annotated[list[str], BeforeValidator(Validators.convert_str_to_list), Field(min_length=1)]
    timeout: int = Field(ge=1, le=3600)
    network: NetworkMode | None = None
    geolocation: Annotated[list[str] | None, BeforeValidator(Validators.convert_str_to_list)] = None
    browser: Browser | None = None

    def to_api_payload(self) -> dict:
        """Build the JSON body for POST/PUT /profiles."""
        body = self.model_dump(exclude_none=True, exclude={'browser'})
        if self.browser is not None:
            body['options'] = ProfileOptions(browser=self.browser).model_dump(exclude_none=True)
        return body

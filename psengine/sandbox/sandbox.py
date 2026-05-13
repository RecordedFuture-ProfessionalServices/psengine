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
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from ..common_models import RFBaseModel
from .models.analysis import Meta, Task

SubmitKind = Literal['file', 'url', 'fetch', 'import']
NetworkMode = Literal['internet', 'drop', 'tor', 'vpn', 'sim200', 'sim404', 'simnx']

# TODO: remove ConfigDict


class SampleSummary(RFBaseModel):
    model_config = ConfigDict(extra='forbid')

    sample: str
    status: str
    custom: str
    owner: str
    target: str
    created: datetime
    completed: datetime
    score: int
    sha256: str | None = None
    org_id: str | None = None
    meta: Meta | None = None

    # Keys normalized to e.g. "static1", "behavioral1", ...
    tasks: dict[str, Task] = Field(default_factory=dict)

    @field_validator('tasks', mode='before')
    @classmethod
    def normalize_task_keys(cls, v):
        # Incoming keys look like "<id>-static1" keep only the suffix after the last '-'
        if isinstance(v, dict):
            return {str(k).rsplit('-', 1)[-1]: val for k, val in v.items()}
        return v


class SearchQuery(RFBaseModel):
    query: str


class SearchIn(RFBaseModel):
    model_config = ConfigDict(extra='forbid')

    file_hash: list[str] | str | None = None
    family: list[str] | str | None = None
    tag: list[str] | str | None = None
    botnet: list[str] | str | None = None
    platform: list[str] | str | None = None
    extracted_c2_data: list[str] | str | None = None
    wallet: list[str] | str | None = None
    analysis_time: str | None = None

    @field_validator(
        'file_hash',
        'family',
        'tag',
        'botnet',
        'platform',
        'extracted_c2_data',
        'wallet',
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
        parts = []
        special_fields = (
            'extracted_c2_data',
            'file_hash',
            'analysis_time',
        )

        for field_name, values in self.model_dump(exclude_none=True).items():
            if not values:
                continue

            prefix = '' if field_name in special_fields else f'{field_name}:'
            for val in values:
                value = val
                if not val.startswith(prefix):
                    value = f'{prefix}{val}'
                parts.append(value)

        return SearchQuery(query=f' {join_operator} '.join(parts))


class SearchResult(RFBaseModel):
    """Sample record returned by `/search`.

    Common shape across the sample-listing endpoints. `fetch_sample()` returns
    the richer `SampleOut` subclass.
    """

    id_: str = Field(alias='id')
    status: str
    kind: str
    filename: str | None = None
    submitted: datetime
    completed: datetime | None = None
    sha256: str | None = None
    url: str | None = None
    user_id: str


class SampleOut(SearchResult):
    """Sample record returned by `GET /samples/{sample_id}`."""

    tasks: list[dict] | None = None


class DeleteOut(RFBaseModel):
    """Result of a `DELETE /samples/{sample_id}` call.

    The Sandbox API returns an empty body on success; the manager constructs this
    model with `deleted=True` when the HTTP request succeeds.
    """

    deleted: bool


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
    user_tags: list[str] | None = None
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
        if self.kind == 'import':
            body['url'] = self.source_id
        if self.interactive is not None:
            body['interactive'] = self.interactive
        if self.password is not None:
            body['password'] = self.password
        if self.profiles is not None:
            body['profiles'] = self.profiles
        if self.user_tags is not None:
            body['user_tags'] = self.user_tags

        defaults: dict = {}
        if self.timeout is not None:
            defaults['timeout'] = self.timeout
        if self.network is not None:
            defaults['network'] = self.network
        if self.geolocation is not None:
            defaults['geolocation'] = self.geolocation
        if defaults:
            body['defaults'] = defaults

        return body, self.file_path


class SandboxUser(RFBaseModel):
    """Sandbox user record returned by user-management endpoints."""

    id_: str = Field(alias='id', default=None)
    company_id: str
    email: str = None
    name: str
    first_name: str
    last_name: str
    created_at: datetime
    role: str

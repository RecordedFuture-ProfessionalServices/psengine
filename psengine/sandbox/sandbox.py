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

from pydantic import ConfigDict, Field, field_validator

from ..common_models import RFBaseModel
from .models.analysis import Meta, Task

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
    model_config = ConfigDict(extra='forbid')
    id_: str = Field(alias='id')
    status: str
    kind: str
    filename: str | None = None
    submitted: datetime
    completed: datetime
    sha256: str | None = None
    url: str | None = None


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

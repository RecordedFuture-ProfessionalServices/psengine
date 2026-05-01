from datetime import datetime
from typing import Optional, Union

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
    sha256: Optional[str] = None
    org_id: Optional[str] = None
    meta: Optional[Meta] = None

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

    file_hash: Optional[Union[list[str], str]] = None
    family: Optional[Union[list[str], str]] = None
    tag: Optional[Union[list[str], str]] = None
    botnet: Optional[Union[list[str], str]] = None
    platform: Optional[Union[list[str], str]] = None
    extracted_c2_data: Optional[Union[list[str], str]] = None
    wallet: Optional[Union[list[str], str]] = None
    analysis_time: Optional[str] = None

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
    filename: Optional[str] = None
    submitted: datetime
    completed: datetime
    sha256: Optional[str] = None
    url: Optional[str] = None

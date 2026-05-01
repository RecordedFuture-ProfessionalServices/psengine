from typing import Annotated, Literal, Optional, Union

from pydantic import ConfigDict, Field

from ...common_models import RFBaseModel

# TODO: remove ConfigDict


class TaskBase(RFBaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: str
    status: str


class StaticTask(TaskBase):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['static']
    score: Optional[int] = None


class BehavioralTask(TaskBase):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['behavioral']

    tags: list[str] = Field(default_factory=list)
    score: int
    target: str
    backend: str
    resource: str
    platform: Optional[str] = None
    os: Optional[str] = None
    queue_id: Optional[int] = None
    timeout: Optional[int] = None
    sigs: Optional[int] = None


class UrlscanTask(TaskBase):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['urlscan']
    score: int


Task = Annotated[Union[BehavioralTask, StaticTask, UrlscanTask], Field(discriminator='kind')]


class Meta(RFBaseModel):
    model_config = ConfigDict(extra='forbid')
    channel: Optional[str] = None
    rforg: Optional[str] = None

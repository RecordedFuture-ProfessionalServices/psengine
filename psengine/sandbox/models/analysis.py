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

from typing import Annotated, Literal

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
    score: int | None = None


class BehavioralTask(TaskBase):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['behavioral']

    tags: list[str] = Field(default_factory=list)
    score: int
    target: str
    backend: str
    resource: str
    platform: str | None = None
    os: str | None = None
    queue_id: int | None = None
    timeout: int | None = None
    sigs: int | None = None


class UrlscanTask(TaskBase):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['urlscan']
    score: int


Task = Annotated[BehavioralTask | StaticTask | UrlscanTask, Field(discriminator='kind')]


class Meta(RFBaseModel):
    model_config = ConfigDict(extra='forbid')
    channel: str | None = None
    rforg: str | None = None

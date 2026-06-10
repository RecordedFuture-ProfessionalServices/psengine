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

from pydantic import Field

from ...common_models import RFBaseModel


class TaskBase(RFBaseModel):
    kind: str
    status: str


class StaticTask(TaskBase):
    kind: Literal['static']
    score: int | None = None
    tags: list[str] = Field(default_factory=list)
    sigs: int | None = None


class BehavioralTask(TaskBase):
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
    pick: str | None = None
    failure: str | None = None


class UrlscanTask(TaskBase):
    kind: Literal['urlscan']
    score: int | None = None
    failure: str | None = None


Task = Annotated[BehavioralTask | StaticTask | UrlscanTask, Field(discriminator='kind')]


class LightweightSampleTask(RFBaseModel):
    """Lightweight task reference embedded in `GET /samples/{sample_id}` responses."""

    id_: str = Field(alias='id')
    status: str
    target: str | None = None
    pick: str | None = None


class Meta(RFBaseModel):
    channel: str | None = None
    rforg: str | None = None

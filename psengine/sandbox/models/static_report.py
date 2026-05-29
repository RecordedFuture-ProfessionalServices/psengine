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

from pydantic import Field

from ...common_models import RFBaseModel


class StaticReportSample(RFBaseModel):
    """The `sample` block of a static report: identity of the submitted sample."""

    sample: str
    kind: str
    size: int | None = None
    target: str | None = None


class StaticReportTask(RFBaseModel):
    """The `task` block of a static report: the static-analysis task itself."""

    task: str
    target: str | None = None


class StaticReportAnalysis(RFBaseModel):
    """The `analysis` block: when the static pass ran and what it scored."""

    reported: datetime | None = None
    score: int | None = None
    tags: list[str] = Field(default_factory=list)


class StaticReportSignature(RFBaseModel):
    """A single static signature hit (present when the analysis flagged something)."""

    name: str
    score: int | None = None
    tags: list[str] = Field(default_factory=list)
    desc: str | None = None


class StaticReportFile(RFBaseModel):
    """A file seen during static analysis (the submitted file plus any unpacked children)."""

    filename: str
    relpath: str | None = None
    filesize: int | None = None
    md5: str | None = None
    sha1: str | None = None
    sha256: str | None = None
    sha512: str | None = None
    ssdeep: str | None = None
    tlsh: str | None = None
    exts: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    depth: int | None = None
    error: str | None = None
    kind: str | None = None
    selected: bool | None = None
    runas: str | None = None
    metadata: dict = Field(default_factory=dict)

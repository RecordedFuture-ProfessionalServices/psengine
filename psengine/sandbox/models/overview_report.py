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

from pydantic import Field, field_validator

from ...common_models import RFBaseModel
from .static_report import (
    StaticReportExtractedConfig,
    StaticReportSignatureIndicator,
)


class OverviewAnalysis(RFBaseModel):
    """The `analysis` block of an overview report: overall verdict for the sample."""

    score: int | None = None
    family: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class OverviewSample(RFBaseModel):
    """The `sample` block of an overview report: identity and hashes of the submission."""

    id_: str = Field(alias='id')
    score: int | None = None
    target: str | None = None
    created: datetime | None = None
    completed: datetime | None = None
    size: int | None = None
    md5: str | None = None
    sha1: str | None = None
    sha256: str | None = None
    sha512: str | None = None
    ssdeep: str | None = None
    tlsh: str | None = None


class OverviewSignature(RFBaseModel):
    """A signature hit in an overview report (sample-level or under a target).

    Same shape as a static-report signature plus the MITRE ATT&CK `ttp` list and an
    optional reference `url`.
    """

    name: str
    label: str | None = None
    score: int | None = None
    desc: str | None = None
    tags: list[str] = Field(default_factory=list)
    ttp: list[str] = Field(default_factory=list)
    indicators: list[StaticReportSignatureIndicator] = Field(default_factory=list)
    is_custom: bool | None = None
    url: str | None = None


class OverviewExtractedCredential(RFBaseModel):
    """A credential recovered alongside an extracted config (the item-level `credentials`).

    Distinct from `StaticReportExtractedConfig.credentials`: this one carries a `flow`
    identifier instead of `email_to`.
    """

    protocol: str | None = None
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    flow: int | None = None


class OverviewDropperUrl(RFBaseModel):
    """A single URL a dropper pulls from, with the kind of payload it fetches."""

    url: str | None = None
    type: str | None = None


class OverviewExtractedDropper(RFBaseModel):
    """A dropper recovered during analysis: the URLs it pulls plus its source script."""

    language: str | None = None
    source: str | None = None
    deobfuscated: str | None = None
    urls: list[OverviewDropperUrl] = Field(default_factory=list)

    @field_validator('urls', mode='before')
    @classmethod
    def _normalise_urls(cls, v):
        # `urls` items are usually bare strings but can be {"type": ..., "url": ...}
        # objects -- coerce bare strings to the object shape so the list is uniform.
        if not v:
            return []
        return [{'url': item} if isinstance(item, str) else item for item in v]


class OverviewExtractedRansomNote(RFBaseModel):
    """A ransom note recovered during analysis."""

    family: str | None = None
    note: str | None = None
    emails: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    wallets: list[str] = Field(default_factory=list)


class OverviewExtracted(RFBaseModel):
    """An item in the overview `extracted` list: a config, dropper, ransom note or credential
    recovered during analysis, with the tasks that produced it.
    """

    resource: str | None = None
    dumped_file: str | None = None
    path: str | None = None
    tasks: list[str] = Field(default_factory=list)
    config: StaticReportExtractedConfig | None = None
    credentials: OverviewExtractedCredential | None = None
    dropper: OverviewExtractedDropper | None = None
    ransom_note: OverviewExtractedRansomNote | None = None


class OverviewTargetIocs(RFBaseModel):
    """The `iocs` block of a target: network indicators observed for that target."""

    domains: list[str] = Field(default_factory=list)
    ips: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)


class OverviewTarget(RFBaseModel):
    """A single analysis target in an overview report (the submitted file/url or an
    unpacked child), with its score, IOCs and signature hits.
    """

    target: str | None = None
    pick: str | None = None
    score: int | None = None
    size: int | None = None
    md5: str | None = None
    sha1: str | None = None
    sha256: str | None = None
    sha512: str | None = None
    ssdeep: str | None = None
    tlsh: str | None = None
    family: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    iocs: OverviewTargetIocs | None = None
    signatures: list[OverviewSignature] = Field(default_factory=list)


class OverviewTask(RFBaseModel):
    """A single task entry from the overview `tasks` map (keyed by `{sampleID}-{taskName}`)."""

    kind: str
    status: str
    name: str | None = None
    score: int | None = None
    sigs: int | None = None
    tags: list[str] = Field(default_factory=list)
    target: str | None = None
    backend: str | None = None
    os: str | None = None
    resource: str | None = None
    timeout: int | None = None
    pick: str | None = None
    failure: str | None = None


class OverviewError(RFBaseModel):
    """A per-task error recorded in the overview `errors` list."""

    task: str | None = None
    reason: str | None = None

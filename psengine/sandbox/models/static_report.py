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


class StaticReportSignatureIndicator(RFBaseModel):
    """A single indicator backing a signature hit (e.g. the YARA rule that matched)."""

    resource: str | None = None
    yara_rule: str | None = None


class StaticReportSignature(RFBaseModel):
    """A single static signature hit (present when the analysis flagged something)."""

    label: str | None = None
    name: str
    score: int | None = None
    tags: list[str] = Field(default_factory=list)
    desc: str | None = None
    indicators: list[StaticReportSignatureIndicator] = Field(default_factory=list)
    is_custom: bool | None = None


class StaticReportExtractedKey(RFBaseModel):
    """A cryptographic key recovered by a config extractor (e.g. an RC4 or RSA key).

    Carried in `StaticReportExtractedConfig.keys`. `kind` describes the key type
    (e.g. `rc4.plain`, `rsa.pubkey.base64`), `key` is its label, and `value` is the
    encoded key material.
    """

    kind: str | None = None
    key: str | None = None
    value: str | None = None


class StaticReportExtractedCredential(RFBaseModel):
    """A credential recovered by a config extractor (e.g. an FTP/SMTP exfil account).

    Carried in `StaticReportExtractedConfig.credentials`.
    """

    protocol: str | None = None
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    email_to: str | None = None


class StaticReportExtractedConfig(RFBaseModel):
    """A malware configuration recovered by a Triage config extractor."""

    family: str | None = None
    rule: str | None = None
    version: str | None = None
    botnet: str | None = None
    campaign: str | None = None
    tags: list[str] = Field(default_factory=list)
    c2: list[str] = Field(default_factory=list)
    decoy: list[str] = Field(default_factory=list)
    mutex: list[str] = Field(default_factory=list)
    dns: list[str] = Field(default_factory=list)
    extracted_pe: list[str] = Field(default_factory=list)
    keys: list[StaticReportExtractedKey] = Field(default_factory=list)
    credentials: list[StaticReportExtractedCredential] = Field(default_factory=list)
    attr: dict = Field(default_factory=dict)
    raw: str | None = None


class StaticReportExtracted(RFBaseModel):
    """A malware configuration extracted from a file during static analysis."""

    dumped_file: str | None = None
    resource: str | None = None
    config: StaticReportExtractedConfig = Field(default_factory=StaticReportExtractedConfig)

    @field_validator('config', mode='before')
    @classmethod
    def _none_to_empty_config(cls, v):
        return v or {}


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

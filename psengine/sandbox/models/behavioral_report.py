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
from ...helpers import Validators


class BehavioralSample(RFBaseModel):
    """The `sample` block of a behavioral report: identity of the submitted sample."""

    id_: str = Field(alias='id')
    score: int | None = None
    target: str | None = None
    submitted: datetime | None = None
    size: int | None = None
    md5: str | None = None
    sha1: str | None = None
    sha256: str | None = None
    sha512: str | None = None
    ssdeep: str | None = None
    tlsh: str | None = None
    static_tags: list[str] = Field(default_factory=list)


class BehavioralTask(RFBaseModel):
    """The `task` block of a behavioral report: the file detonated in this behavioral run."""

    target: str | None = None
    pick: str | None = None
    size: int | None = None
    md5: str | None = None
    sha1: str | None = None
    sha256: str | None = None
    sha512: str | None = None
    ssdeep: str | None = None
    tlsh: str | None = None
    static_tags: list[str] = Field(default_factory=list)


class BehavioralAnalysis(RFBaseModel):
    """The `analysis` block: verdict and run metadata for this behavioral task."""

    score: int | None = None
    tags: list[str] = Field(default_factory=list)
    ttp: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    submitted: datetime | None = None
    reported: datetime | None = None
    max_time_network: int | None = None
    max_time_kernel: int | None = None
    backend: str | None = None
    resource: str | None = None
    resource_tags: list[str] = Field(default_factory=list)
    platform: str | None = None
    geolocation_tags: list[str] = Field(default_factory=list)
    interaction: dict = Field(default_factory=dict)

    # The API sends `tags: null` when there are none -- coerce to [] so it is iterable.
    _coerce_tags = field_validator('tags', mode='before')(Validators.none_to_empty_list)


class BehavioralProcess(RFBaseModel):
    """A process observed during detonation (the process tree of `processes`)."""

    procid: int | None = None
    procid_parent: int | None = None
    pid: int | None = None
    ppid: int | None = None
    cmd: str | list[str] | None = None
    image: str | None = None
    orig: bool | None = None
    started: int | None = None
    terminated: int | None = None


class BehavioralDumped(RFBaseModel):
    """A dumped artifact (memory region or file) written during detonation."""

    at: int | None = None
    pid: int | None = None
    procid: int | None = None
    name: str | None = None
    kind: str | None = None
    origin: str | None = None
    addr: int | None = None
    length: int | None = None
    path: str | None = None
    size: int | None = None
    md5: str | None = None
    sha1: str | None = None
    sha256: str | None = None
    sha512: str | None = None
    ssdeep: str | None = None
    tlsh: str | None = None


class BehavioralError(RFBaseModel):
    """A per-task error recorded in the behavioral `errors` list (present on failed runs)."""

    task: str | None = None
    reason: str | None = None


class BehavioralNetworkFlow(RFBaseModel):
    """A single network flow (connection) observed during detonation."""

    id_: int | None = Field(default=None, alias='id')
    src: str | None = None
    dst: str | None = None
    proto: str | None = None
    pid: int | None = None
    procid: int | None = None
    first_seen: int | None = None
    last_seen: int | None = None
    rx_bytes: int | None = None
    rx_packets: int | None = None
    tx_bytes: int | None = None
    tx_packets: int | None = None
    protocols: list[str] = Field(default_factory=list)
    domain: str | None = None
    tls_ja3: str | None = None
    tls_ja3s: str | None = None
    tls_sni: str | None = None


class BehavioralNetworkIp(RFBaseModel):
    """Geo/ASN metadata for an IP seen on the network (values of `network.ips`)."""

    cc: str | None = None
    asn: str | None = None


class BehavioralDnsQuestion(RFBaseModel):
    """A single question in a DNS request."""

    name: str | None = None
    type: str | None = None


class BehavioralDnsRequest(RFBaseModel):
    """The DNS query part of a network request."""

    domains: list[str] = Field(default_factory=list)
    questions: list[BehavioralDnsQuestion] = Field(default_factory=list)


class BehavioralDnsAnswer(RFBaseModel):
    """A single answer record in a DNS response."""

    name: str | None = None
    type: str | None = None
    value: str | None = None


class BehavioralDnsResponse(RFBaseModel):
    """The DNS answer part of a network request."""

    domains: list[str] = Field(default_factory=list)
    ip: list[str] = Field(default_factory=list)
    answers: list[BehavioralDnsAnswer] = Field(default_factory=list)


class BehavioralHttpRequest(RFBaseModel):
    """The HTTP request part of a network request."""

    method: str | None = None
    url: str | None = None
    request: str | None = None
    stream: int | None = None
    headers: list[str] = Field(default_factory=list)


class BehavioralHttpResponse(RFBaseModel):
    """The HTTP response part of a network request."""

    status: str | None = None
    response: str | None = None
    stream: int | None = None
    headers: list[str] = Field(default_factory=list)


class BehavioralNetworkRequest(RFBaseModel):
    """A single request on a flow: exactly one of the dns/http parts is populated."""

    flow: int | None = None
    index: int | None = None
    dns_request: BehavioralDnsRequest | None = None
    dns_response: BehavioralDnsResponse | None = None
    http_request: BehavioralHttpRequest | None = None
    http_response: BehavioralHttpResponse | None = None


class BehavioralNetwork(RFBaseModel):
    """The `network` block: flows, per-request detail and IP geo/ASN metadata."""

    flows: list[BehavioralNetworkFlow] = Field(default_factory=list)
    requests: list[BehavioralNetworkRequest] = Field(default_factory=list)
    ips: dict[str, BehavioralNetworkIp] = Field(default_factory=dict)

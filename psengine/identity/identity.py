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
from functools import total_ordering
from typing import Annotated, Optional

from pydantic import AfterValidator, BeforeValidator, Field, field_validator

from ..common_models import IdName, RFBaseModel
from ..constants import TIMESTAMP_STR
from ..helpers import Validators
from .models.common_models import (
    BaseIdentityIn,
    Cookie,
    DomainTypes,
    DumpSearchOut,
    FilterIn,
    IdentityOrgIn,
    PasswordHash,
)
from .models.detections import AuthorizationService, DetectionsCreated, DetectionsFilterIn, Password
from .models.incident_report import IncidentReportCredentials, IncidentReportDetails
from .models.lookup import IdentityDetails, IPRange, SecretDetails


@total_ordering
class Detection(RFBaseModel):
    """Model to validate output of the ``/identity/detections`` endpoint.

    Methods:
        __hash__:
            Returns hash value based on Detection ``id_`` and created time.

        __eq__:
            Checks equality between two Detection instances based on ``id_`` and created time.

        __gt__:
            Defines a greater-than comparison between two Detection instances based on
            created timestamp and ``id_``.

        __str__:
            Returns a string representation of the Detection instance with:
            ``id_``, created timestamp, type, and novel.

            .. code-block:: python

                >>> print(detection)
                ID: detection123, Created: 2025-01-01 05:00:30AM, Type: Workforce, Novel: True


    Total Ordering:
            The ordering of Detection instances is determined primarily by the created timestamp
            of the detection. If two instances have the same created timestamp, their
            ``id_`` is used as a secondary criterion for ordering.
    """

    id_: str = Field(alias='id')
    organization_id: Annotated[
        Optional[list[str]], BeforeValidator(Validators.check_uhash_prefix)
    ] = None
    novel: bool
    type_: str = Field(alias='type')
    subject: str
    password: Password
    authorization_service: Optional[AuthorizationService] = None
    cookies: list[Cookie]
    malware_family: Optional[IdName] = None
    dump: DumpSearchOut
    created: datetime

    def __hash__(self):
        return hash((self.id_, self.created))

    def __eq__(self, other: 'Detection'):
        return (self.id_, self.created) == (other.id_, other.created)

    def __gt__(self, other: 'Detection'):
        return (self.created, self.id_) > (other.created, other.id_)

    def __str__(self):
        return (
            f'Detection ID: {self.id_}, '
            f'Created: {self.created.strftime(TIMESTAMP_STR)}, '
            f'Type: {self.type_}, '
            f'Novel: {self.novel}'
        )


@total_ordering
class CredentialSearch(RFBaseModel):
    """Model to validate output of the ``/identity/credentials/search`` endpoint.

    Methods:
        __hash__:
            Returns hash value based on CredentialSearch ``login`` and ``domain``.

        __eq__:
            Checks equality between two CredentialSearch based on ``login`` and ``domain``.

        __gt__:
            Defines a greater-than comparison between two CredentialSearch instances based on
            ``login`` and ``domain``.

        __str__:
            Returns a string representation of the CredentialSearch instance with:
            ``login`` and ``domain``.

            .. code-block:: python

                >>> print(credential)
                Login: example Domain: norsegods.online

    Total Ordering:
            The ordering of CredentialSearch instances is determined primarily by the ``login`` of
            the detection. If two instances have the same ``login, their ``domain`` is used as a
            secondary criterion for ordering.

    """

    login: str
    login_sha1: Optional[str] = None  # This is used only by CredentialLookupIn.subject_login
    domain: str

    def __hash__(self):
        return hash((self.login, self.domain))

    def __eq__(self, other: 'CredentialSearch'):
        return (self.login, self.domain) == (other.login, other.domain)

    def __gt__(self, other: 'CredentialSearch'):
        return (self.login, self.domain) > (other.login, other.domain)

    def __str__(self):
        return f'Login: {self.login}, Domain: {self.domain}'


class Detections(RFBaseModel):
    """Model for payload received by POST ``/identity/detections`` endpoint."""

    total: int
    detections: list[Detection]

    def __str__(self):
        data = '\n'.join(str(d) for d in self.detections)
        return f'[{data}]'


@total_ordering
class PasswordLookup(RFBaseModel):
    """Model to validate output of the ``/identity/credentials/lookup`` endpoint.

    Methods:
        __hash__:
            Returns hash value based on ``password.hash_`` (or ``hash_prefix``) and ``algorithm``.

        __eq__:
            Checks equality between two PasswordLookup instances based on ``password.hash_`` (or
            ``hash_prefix``) and ``algorithm``.

        __gt__:
            Defines a greater-than comparison between two PasswordLookup instances based on
            ``password.hash_`` (or ``hash_prefix``) and ``algorithm``.

        __str__:
            Returns a string representation of the PasswordLookup instance with:
            ``password.hash_`` (or ``hash_prefix``), ``algorithm``, and ``exposure_status``.

            .. code-block:: python

                >>> print(lookup)
                Hash: abc123 Algorithm: sha1 Exposure Status: Common

    Total Ordering:
            The ordering of PasswordLookup instances is determined primarily by the
            ``password.hash_`` (or ``hash_prefix``). If two instances have the same hash, their
            ``algorithm`` is used as a secondary criterion for ordering.

    """

    password: PasswordHash
    exposure_status: str

    def __hash__(self):
        return hash(
            ((self.password.hash_ or self.password.hash_prefix), self.password.algorithm.value)
        )

    def __eq__(self, other: 'PasswordLookup'):
        return (
            (self.password.hash_ or self.password.hash_prefix),
            self.password.algorithm.value,
        ) == ((other.password.hash_ or other.password.hash_prefix), other.password.algorithm.value)

    def __gt__(self, other: 'PasswordLookup'):
        return (
            (self.password.hash_ or self.password.hash_prefix),
            self.password.algorithm.value,
        ) > ((other.password.hash_ or other.password.hash_prefix), other.password.algorithm.value)

    def __str__(self):
        return (
            f'Hash: {(self.password.hash_ or self.password.hash_prefix)}, '
            f'Algorithm: {self.password.algorithm.value}, '
            f'Exposure Status: {self.exposure_status}'
        )


class Credential(RFBaseModel):
    """Detection model to validate output of the ``/identity/credentials/search`` endpoint.

    Methods:
        __hash__:
            Returns hash value based on ``subject``, ``first_downloaded``, the exposed secret's
            ``hashes``, and the ``authorization_service`` URL (if present).

        __eq__:
            Checks equality between two Credential instances based on ``subject``,
            ``first_downloaded``, the exposed secret's ``hashes``, and the
            ``authorization_service`` URL.

        __gt__:
            Defines a greater-than comparison between two Credential instances based on
            ``subject``, ``first_downloaded``, the exposed secret's ``hashes``, and the
            ``authorization_service`` URL.

        __str__:
            Returns a string representation of the Credential instance with:
            ``subject``, ``first_downloaded``, exposed secret ``hashes``, and
            ``authorization_service``.

            .. code-block:: python

                >>> print(credential)
                Subject: admin@example.com, First Downloaded: 2024-03-01T12:00:00,
                Hashes: [abc123, def456], Authorization Service: login.service.com

    Total Ordering:
            The ordering of Credential instances is determined primarily by the ``subject`` and
            ``first_downloaded`` timestamp. If those are equal, the ``hashes`` and then the
            ``authorization_service`` URL are used as secondary criteria.
    """

    subject: str
    dumps: list[DumpSearchOut]
    first_downloaded: datetime
    latest_downloaded: datetime
    exposed_secret: SecretDetails
    compromise: Optional[dict[str, datetime]] = None
    malware_family: Optional[IdName] = None
    authorization_service: Optional[AuthorizationService] = None
    cookies: Optional[list[Cookie]] = None

    def __hash__(self):
        hashes = ', '.join(sorted(a.hash_ or a.hash_prefix for a in self.exposed_secret.hashes))
        auth = self.authorization_service.url if self.authorization_service else ''
        return hash((self.subject, self.first_downloaded, hashes, auth))

    def __eq__(self, other: 'Credential'):
        hashes_self = sorted(a.hash_ or a.hash_prefix for a in self.exposed_secret.hashes)
        hashes_other = sorted(a.hash_ or a.hash_prefix for a in other.exposed_secret.hashes)
        auth_self = self.authorization_service.url if self.authorization_service else ''
        auth_other = other.authorization_service.url if other.authorization_service else ''
        return (
            self.subject == other.subject
            and self.first_downloaded == other.first_downloaded
            and hashes_self == hashes_other
            and auth_self == auth_other
        )

    def __gt__(self, other: 'Credential'):
        hashes_self = ', '.join(
            sorted(a.hash_ or a.hash_prefix for a in self.exposed_secret.hashes)
        )
        hashes_other = ', '.join(
            sorted(a.hash_ or a.hash_prefix for a in other.exposed_secret.hashes)
        )
        auth_self = self.authorization_service.url if self.authorization_service else ''
        auth_other = other.authorization_service.url if other.authorization_service else ''
        return (self.subject, self.first_downloaded, hashes_self, auth_self) > (
            other.subject,
            other.first_downloaded,
            hashes_other,
            auth_other,
        )

    def __str__(self):
        hashes = ', '.join(sorted(a.hash_ or a.hash_prefix for a in self.exposed_secret.hashes))
        auth = self.authorization_service.url if self.authorization_service else 'None'
        return (
            f'Subject: {self.subject}, '
            f'First Downloaded: {self.first_downloaded.strftime(TIMESTAMP_STR)}, '
            f'Hashes: [{hashes}], '
            f'Authorization Service: {auth}'
        )


class LeakedIdentity(RFBaseModel):
    """Model to validate output of several endpoints.

    ``/identity/ip/lookup``, ``/identity/credentials/lookup``, ``/identity/hostname/lookup``
    """

    identity: IdentityDetails
    count: int
    credentials: list[Credential]


class DetectionsIn(RFBaseModel):
    """Model for payload sent to POST ``/identity/detections`` endpoint."""

    organization_id: Annotated[
        Optional[list[str]],
        BeforeValidator(Validators.convert_str_to_list),
        AfterValidator(Validators.check_uhash_prefix),
    ] = []
    include_enterprise_level: Optional[bool] = None
    filter: Optional[DetectionsFilterIn] = Field(default_factory=DetectionsFilterIn)
    limit: int
    offset: Optional[str] = None
    created: Optional[DetectionsCreated] = Field(default_factory=DetectionsCreated)


class IncidentReportIn(IdentityOrgIn):
    """Model for payload sent to POST ``/identity/detections`` endpoint."""

    source: str
    include_details: bool


class IncidentReportOut(RFBaseModel):
    """Model for payload received by POST ``/identity/incident/report`` endpoint."""

    details: Optional[IncidentReportDetails] = None
    credentials: list[IncidentReportCredentials]

    @field_validator('details', mode='before')
    @classmethod
    def transform_details(cls, value):
        """Paged request returns lists only so transforming by extracting the first one."""
        if isinstance(value, list) and len(value):
            return value.pop(0)

        return None


class HostnameLookupIn(BaseIdentityIn):
    """Model for payload sent to POST ``/identity/incident/report` endpoint."""

    hostname: str


class IPLookupIn(BaseIdentityIn):
    """Model for payload sent to POST ``/identity/ip/lookup`` endpoint."""

    ip: Optional[str] = None
    range_: Optional[IPRange] = Field(alias='range', default=None)


class CredentialsLookupIn(BaseIdentityIn):
    """Model for payload sent to POST ``/identity/credentials/lookup`` endpoint."""

    subjects: Annotated[Optional[list[str]], BeforeValidator(Validators.convert_str_to_list)] = None
    subjects_sha1: Annotated[
        Optional[list[str]], BeforeValidator(Validators.convert_str_to_list)
    ] = None
    subjects_login: Optional[list[CredentialSearch]] = None
    filter: Optional[FilterIn] = None


class CredentialsSearchIn(BaseIdentityIn):
    """Model for payload sent to POST ``/identity/credentials/search`` endpoint."""

    domains: Annotated[list[str], BeforeValidator(Validators.convert_str_to_list)]
    domain_types: Annotated[
        Optional[list[DomainTypes]], BeforeValidator(Validators.convert_str_to_list)
    ] = None

    filter: Optional[FilterIn] = None


class DumpSearchIn(RFBaseModel):
    """Model for payload sent to POST ``/identity/metadata/dump/search`` endpoint."""

    names: Annotated[list[str], BeforeValidator(Validators.convert_str_to_list)]
    limit: Optional[int] = None

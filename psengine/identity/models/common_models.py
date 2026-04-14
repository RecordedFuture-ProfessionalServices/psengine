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
from enum import Enum
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, Field, field_validator, model_validator
from pydantic.networks import IPvAnyAddress

from ...common_models import IdName, RFBaseModel
from ...constants import DEFAULT_LIMIT
from ...helpers import Validators


class DetectionType(Enum):
    WORKFORCE = 'Workforce'
    EXTERNAL = 'External'


class DomainTypes(Enum):
    AUTHORIZATION = 'Authorization'
    EMAIL = 'Email'


class Properties(Enum):
    LETTER = 'Letter'
    NUMBER = 'Number'
    SYMBOL = 'Symbol'
    UPPERCASE = 'UpperCase'
    LOWERCASE = 'LowerCase'
    MIXEDCASE = 'MixedCase'
    ATLEAST8CHARS = 'AtLeast8Characters'
    ATLEAST10CHARS = 'AtLeast10Characters'
    ATLEAST12CHARS = 'AtLeast12Characters'
    ATLEAST16CHARS = 'AtLeast16Characters'
    ATLEAST24CHARS = 'AtLeast24Characters'
    COOKIES = 'Cookies'
    UNEXPIREDCOOKIES = 'UnexpiredCookies'
    AUTHORIZATIONTECHNOLOGY = 'AuthorizationTechnology'
    MALWAREONLY = 'MalwareOnly'


class Precision(Enum):
    YEAR = 'year'
    MONTH = 'month'
    DAY = 'day'


class Algorithm(Enum):
    SHA1 = 'SHA1'
    SHA256 = 'SHA256'
    HASH32 = 'HASH32'
    HASH40 = 'HASH40'
    HASH64 = 'HASH64'
    HASH96 = 'HASH96'
    HASH128 = 'HASH128'
    BCRYPT = 'BCRYPT'
    PHPASS = 'PHPASS'
    HASHCAT_HEX = 'HASHCAT_HEX'
    BASE64 = 'BASE64'
    SSHA = 'SSHA'
    PBKDF2_SHA256 = 'PBKDF2_SHA256'
    BASE64_HASH32 = 'BASE64_HASH32'
    BASE64_HASH40 = 'BASE64_HASH40'
    BASE64_HASH128 = 'BASE64_HASH128'
    BASE64_INTEGER_HASH32 = 'BASE64_INTEGER_HASH32'
    BASE64_INTEGER_HASH40 = 'BASE64_INTEGER_HASH40'
    BASE64_INTEGER_HASH64 = 'BASE64_INTEGER_HASH64'
    BASE64_INTEGER_HASH96 = 'BASE64_INTEGER_HASH96'
    BASE64_INTEGER_HASH128 = 'BASE64_INTEGER_HASH128'
    MYSQL_SHA_V41PLUS = 'MYSQL_SHA_V41PLUS'
    NTLM = 'NTLM'
    MD5 = 'MD5'


class Technology(IdName):
    category: str | None = None


class PasswordHash(RFBaseModel):
    algorithm: Algorithm
    hash_: str | None = Field(alias='hash', default=None)
    hash_prefix: str | None = None

    @model_validator(mode='after')
    def check_hash_fields_present(self):
        """Validates at least one of hash or hash_prefix is supplied."""
        if not (self.hash_ or self.hash_prefix):
            raise ValueError('One of `hash` or `hash_prefix` must be supplied')
        return self


class Cookie(RFBaseModel):
    dns: str
    name: str
    http: bool
    expiration: datetime
    secure: bool


class Country(RFBaseModel):
    name: str
    display_name: str = Field(validation_alias='displayName')
    country_code: str = Field(validation_alias='countryCode')
    alpha_two_code: str = Field(validation_alias='alpha2Code')
    alpha_three_code: str = Field(validation_alias='alpha3Code')


class Location(RFBaseModel):
    country: Country
    postal_code: str | None = None
    city: str | None = None
    address: str | None = None
    address_one: str | None = Field(validation_alias='address1', default=None)
    address_two: str | None = Field(validation_alias='address2', default=None)
    state: str | None = None
    zip: str | None = None


class Infrastructure(RFBaseModel):
    ip: IPvAnyAddress


class Compromise(RFBaseModel):
    exfiltration_date: datetime
    os: str | None = None
    os_username: str | None = None
    malware_file: str | None = None
    timezone: str | None = None
    computer_name: str | None = None
    uac: str | None = None
    antivirus: str | list[str] | None = None


class Breach(RFBaseModel):
    name: str
    domain: str
    type_: str = Field(alias='type')
    breached: datetime | None = None
    start: datetime
    stop: datetime
    precision: Precision
    description: str
    site_description: str


class BaseIdentityOut(RFBaseModel):
    count: int
    next_offset: str


class QueryProperties(RFBaseModel):
    name: str | None = None
    date: datetime | None = None


class FilterIn(RFBaseModel):
    first_downloaded_gte: Annotated[
        datetime | None, BeforeValidator(Validators.convert_relative_time)
    ] = None
    latest_downloaded_gte: Annotated[
        datetime | None, BeforeValidator(Validators.convert_relative_time)
    ] = None
    exfiltration_date_gte: Annotated[
        datetime | None, BeforeValidator(Validators.convert_relative_time)
    ] = None
    breach_properties: QueryProperties | None = None
    dump_properties: QueryProperties | None = None
    properties: Annotated[
        list[Properties] | None, BeforeValidator(Validators.convert_str_to_list)
    ] = None
    username_properties: Annotated[
        list[str] | None, BeforeValidator(Validators.convert_str_to_list)
    ] = None
    authorization_technologies: Annotated[
        list[str] | None, BeforeValidator(Validators.convert_str_to_list)
    ] = None
    authorization_protocols: Annotated[
        list[str] | None, BeforeValidator(Validators.convert_str_to_list)
    ] = None
    malware_families: Annotated[
        list[str] | None, BeforeValidator(Validators.convert_str_to_list)
    ] = None

    @field_validator('username_properties', mode='before')
    @classmethod
    def validate_username_properties(cls, v):
        """Only valid value is 'email'."""
        if not all(isinstance(_, str) for _ in v):
            raise ValueError("field 'username_properties' must only contain strings")
        if len(v) != 1 or 'Email' not in v:
            raise ValueError("field 'username_properties' only accepts 'Email'")
        return v


class BaseIdentityIn(RFBaseModel):
    limit: int | None = Field(default=DEFAULT_LIMIT, gt=0, le=500)
    offset: str | None = None


class IdentityOrgIn(BaseIdentityIn):
    organization_id: Annotated[str | None, AfterValidator(Validators.check_uhash_prefix)] = None


class DumpSearchOut(RFBaseModel):
    """Model for payload received by POST `/identity/metadata/dump/search` endpoint."""

    name: str
    source: str | None = None
    description: str | None = None
    downloaded: datetime
    breaches: list[Breach] | None = None
    compromise: Compromise | None = None
    infrastructure: Infrastructure | None = None
    location: Location | None = None

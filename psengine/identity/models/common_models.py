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
from typing import Annotated, Optional, Union

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
    category: Optional[str] = None


class PasswordHash(RFBaseModel):
    algorithm: Algorithm
    hash_: Optional[str] = Field(alias='hash', default=None)
    hash_prefix: Optional[str] = None

    @model_validator(mode='after')
    @classmethod
    def check_hash_fields_present(cls, data):
        """Validates at least one of hash or hash_prefix is supplied."""
        if not (data.hash_ or data.hash_prefix):
            raise ValueError('One of `hash` or `hash_prefix` must be supplied')
        return data


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
    postal_code: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    address_one: Optional[str] = Field(validation_alias='address1', default=None)
    address_two: Optional[str] = Field(validation_alias='address2', default=None)
    state: Optional[str] = None
    zip: Optional[str] = None


class Infrastructure(RFBaseModel):
    ip: IPvAnyAddress


class Compromise(RFBaseModel):
    exfiltration_date: datetime
    os: Optional[str] = None
    os_username: Optional[str] = None
    malware_file: Optional[str] = None
    timezone: Optional[str] = None
    computer_name: Optional[str] = None
    uac: Optional[str] = None
    antivirus: Union[str, list[str], None] = None


class Breach(RFBaseModel):
    name: str
    domain: str
    type_: str = Field(alias='type')
    breached: Optional[datetime] = None
    start: datetime
    stop: datetime
    precision: Precision
    description: str
    site_description: str


class BaseIdentityOut(RFBaseModel):
    count: int
    next_offset: str


class QueryProperties(RFBaseModel):
    name: Optional[str] = None
    date: Optional[datetime] = None


class FilterIn(RFBaseModel):
    first_downloaded_gte: Annotated[
        Optional[datetime], BeforeValidator(Validators.convert_relative_time)
    ] = None
    latest_downloaded_gte: Annotated[
        Optional[datetime], BeforeValidator(Validators.convert_relative_time)
    ] = None
    exfiltration_date_gte: Annotated[
        Optional[datetime], BeforeValidator(Validators.convert_relative_time)
    ] = None
    breach_properties: Optional[QueryProperties] = None
    dump_properties: Optional[QueryProperties] = None
    properties: Annotated[
        Optional[list[Properties]], BeforeValidator(Validators.convert_str_to_list)
    ] = None
    username_properties: Annotated[
        Optional[list[str]], BeforeValidator(Validators.convert_str_to_list)
    ] = None
    authorization_technologies: Annotated[
        Optional[list[str]], BeforeValidator(Validators.convert_str_to_list)
    ] = None
    authorization_protocols: Annotated[
        Optional[list[str]], BeforeValidator(Validators.convert_str_to_list)
    ] = None
    malware_families: Annotated[
        Optional[list[str]], BeforeValidator(Validators.convert_str_to_list)
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
    limit: Optional[int] = Field(default=DEFAULT_LIMIT, gt=0, le=500)
    offset: Optional[str] = None


class IdentityOrgIn(BaseIdentityIn):
    organization_id: Annotated[Optional[str], AfterValidator(Validators.check_uhash_prefix)] = None


class DumpSearchOut(RFBaseModel):
    """Model for payload received by POST ``/identity/metadata/dump/search`` endpoint."""

    name: str
    source: Optional[str] = None
    description: Optional[str] = None
    downloaded: datetime
    breaches: Optional[list[Breach]] = None
    compromise: Optional[Compromise] = None
    infrastructure: Optional[Infrastructure] = None
    location: Optional[Location] = None

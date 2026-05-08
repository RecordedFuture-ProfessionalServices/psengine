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

import os
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, Secret
from typing_extensions import Doc


class RFBaseModel(BaseModel):
    model_config = ConfigDict(extra=os.environ.get('RF_MODEL_EXTRA', 'ignore'))

    def json(
        self,
        by_alias: Annotated[
            bool,
            Doc(
                """
                Alias flag:

                - If `True`, writes fields with their API alias (e.g., `IpAddress`)
                - If `False` uses the Python attribute name alias.
                """
            ),
        ] = True,
        exclude_none: Annotated[bool, Doc('Whether to exclude fields equal to None.')] = True,
        auto_exclude_unset: Annotated[
            bool,
            Doc("""
                Whether to auto exclude values not set.

                - If `True`, uses `RF_EXTRA_MODEL` config to decide inclusion of unmapped fields.
                - If `False`, you must specify `exclude_unset` manually.
                """),
        ] = True,
        **kwargs,
    ):
        """JSON representation of models. It is inherited by every model."""
        if not auto_exclude_unset and kwargs.get('exclude_unset') is None:
            raise ValueError('`auto_exclude_unset` is False, `exclude_unset has to be provided`')

        exclude_unset = (
            bool(self.model_config['extra'] != 'allow')
            if auto_exclude_unset
            else kwargs['exclude_unset']
        )
        kwargs['exclude_unset'] = exclude_unset
        return self.model_dump(mode='json', by_alias=by_alias, exclude_none=exclude_none, **kwargs)


class IdName(RFBaseModel):
    id_: str = Field(alias='id')
    name: str


class IdNameType(RFBaseModel):
    id_: str = Field(alias='id', default=None)
    name: Optional[str] = None
    type_: str = Field(alias='type', default=None)


class IdOptionalNameType(RFBaseModel):
    id_: str = Field(alias='id', default=None)
    name: Optional[str] = None
    type_: str = Field(alias='type', default=None)


class IdNameTypeDescription(IdNameType):
    description: Optional[str] = None


class IOCType(Enum):
    ip = 'ip'
    domain = 'domain'
    hash = 'hash'  # noqa: A003
    vulnerability = 'vulnerability'
    url = 'url'


class DetectionRuleType(Enum):
    sigma = 'sigma'
    yara = 'yara'
    snort = 'snort'


class ClearTextPassword(Secret[str]):
    """Model to hide passwords while logging.

    To view the clear text password do `value.get_secret_value()`
    """

    def _display(self) -> str:
        return self.get_secret_value()[:4] + '********'

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
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RFBaseModel(BaseModel):
    model_config = ConfigDict(extra=os.environ.get('RF_MODEL_EXTRA', 'ignore'))

    def json(self, by_alias=True, exclude_none=True, auto_exclude_unset=True, **kwargs):
        """JSON representation of models. It is inherited by every model.

        Args:
            by_alias (bool): If True, writes fields with their API alias (eg. ``IpAddress``) instead
                of the Python alias (eg. ``ip_address``). Defaults to True.

            exclude_none (bool): Whether fields equal to None should be excluded from the returned
                dictionary. Defaults to True.

            auto_exclude_unset (bool): Excludes values that are not set.

                - True: Based on ``RF_EXTRA_MODEL``, decides if output should have unmapped fields.
                  If the ``model_config`` extra is set to 'allow', includes unmapped values;
                  otherwise, excludes them.

                - False: You need to provide the boolean ``exclude_unset`` in the kwargs.

            kwargs (dict, optional): Any other parameters.
        """
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

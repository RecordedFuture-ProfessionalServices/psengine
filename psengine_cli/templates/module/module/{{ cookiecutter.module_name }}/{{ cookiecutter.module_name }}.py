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

from functools import total_ordering

from pydantic import Field

from .models import Data
from ..common_models import RFBaseModel

class SomethingCoolIn(RFBaseModel):
    """An example model to use for requests

    Args:
        RFBaseModel: RF Base model to inherit from
    """
    cool_field: str

class SomethingCoolOut(RFBaseModel):
    """An example model to use for responses

    Args:
        RFBaseModel: RF Base model to inherit from
    """
    args: dict
    data: Data
    files: dict
    form: dict
    headers: dict

@total_ordering
class {{ cookiecutter.module_class_name }}(RFBaseModel):
    """Validate data received from ``/new_endpoint`` endpoint.

    Methods:
        __hash__:
            your docstring

        __eq__:
            your docstring

        __gt__:
            your docstring

        __str__:
            your docstring

    Total Ordering:
            your docstring
    """

    id_: str = Field(alias='id')
    data: str

    def __hash__(self):
        pass

    def __eq__(self, other: '{{ cookiecutter.module_class_name }}'):
        pass

    def __gt__(self, other: '{{ cookiecutter.module_class_name }}'):
        pass

    def __str__(self):
        pass

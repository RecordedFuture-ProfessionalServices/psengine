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

import logging
from psengine.rf_client import RFClient

from ..helpers import connection_exceptions, debug_call
from pydantic import validate_call
from .errors import {{ cookiecutter.error_name }}
from .{{ cookiecutter.module_name }} import  SomethingCoolIn, {{ cookiecutter.module_class_name }}


class {{ cookiecutter.manager_class_name }}:
    def __init__(self, rf_token: str = None):
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()


    @validate_call
    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise={{ cookiecutter.error_name }})
    def call_and_get_something(
        self,
        something_cool: str,
    ) -> {{ cookiecutter.module_class_name }} :
        if not something_cool:
            raise ValueError('something_cool cannot be empty')
        
        payload = SomethingCoolIn.enhanced_model_validate({'cool_field': something_cool})

        response = self.rf_client.request(
            'post',
            url='https://httpbin.org/post',
            data=payload.json()
        )

        return {{ cookiecutter.module_class_name }}.enhanced_model_validate(response.json()) 

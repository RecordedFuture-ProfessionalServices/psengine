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

   
import pytest
from psengine.{{ cookiecutter.module_name }} import {{ cookiecutter.manager_class_name }}
from psengine.{{ cookiecutter.module_name }} import SomethingCoolOut


class {{ cookiecutter.test_manager_class_name }}:
    # utilise VCR to capture requests and responses to speed up tests
    # @pytest.mark.vcr
    def test_call_and_get_something(self, {{ cookiecutter.manager_file_name}}: {{ cookiecutter.manager_class_name }}):
        note = {{ cookiecutter.manager_file_name}}.call_and_get_something('tQHD_j')
        assert isinstance(note, SomethingCoolOut)

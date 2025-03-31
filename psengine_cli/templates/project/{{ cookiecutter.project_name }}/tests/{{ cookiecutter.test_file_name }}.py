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

from {{ cookiecutter.lib_folder_name }} import {{ cookiecutter.app_class_name }}

class Test_{{ cookiecutter.app_class_name }}r:

    def test_init(self):
        {{ cookiecutter.app_class_file_name }} = {{ cookiecutter.app_class_name }}()
        assert {{ cookiecutter.app_class_file_name }} is not None

    def test_make_some_magic(self):
        {{ cookiecutter.app_class_file_name }} = {{ cookiecutter.app_class_name }}()
        assert {{ cookiecutter.app_class_file_name }}.make_some_magic() is True
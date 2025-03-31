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
import sys
from os.path import abspath, dirname

import pytest

from {{ cookiecutter.lib_folder_name }} import APP_VERSION
from psengine.config import Config, get_config

ROOT_DIR = dirname(abspath(__file__))
sys.path.append(ROOT_DIR)

RF_TOKEN = 'PS_RF_TOKEN'


@pytest.fixture(scope='session')
def vcr_config():
    return {
        'filter_headers': [('X-RFToken', 'bmljZSB0cnkgOikpKSk=')],
    }

@pytest.fixture
def tests_dir():
    return ROOT_DIR

@pytest.fixture
def id_user_agent():
    return f'{{ cookiecutter.project_name}}-unittests/{APP_VERSION}'


@pytest.fixture(scope='session', autouse=True)
def global_config():
    Config.init(rf_token=os.environ.get(RF_TOKEN))
    return get_config()
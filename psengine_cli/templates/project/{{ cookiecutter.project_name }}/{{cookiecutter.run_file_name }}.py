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

import argparse
import os
import sys

from psengine.config import Config, get_config

from {{ cookiecutter.lib_folder_name}} import APP_VERSION, {{ cookiecutter.app_class_name}}

from psengine.logger import RFLogger
from psengine.constants import RF_TOKEN_ENV_VAR


# Set APP ID
APP_ID = '{{ cookiecutter.project_name}}/{}'.format(APP_VERSION)

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'


# Initialize RF Logger
LOG = RFLogger().get_logger()


def parse_cmdline_args():
    """Parse arguments from the command line"""
    parser = argparse.ArgumentParser(description='{{ cookiecutter.project_name_title}}')
    parser.add_argument(
        '-k',
        '--key',
        help='Recorded Future API key',
        default=os.environ.get(RF_TOKEN_ENV_VAR),
    )

    return parser.parse_args()


def main():
    global ERROR_COUNT
    LOG.info('{{ cookiecutter.project_name_title}} v{} starting'.format(APP_VERSION))
    try:
        args = parse_cmdline_args()
        Config.init(rf_token=args.key, app_id=APP_ID, platform_id=PLATFORM_ID)

        ap = {{ cookiecutter.app_class_name}}()

        # Try keep the main function as clean as possible and put the logic in the class
        # makes it easier to read as well as test
        ap.make_some_magic()


    except Exception as e:
        LOG.critical(e, exc_info=False)
        sys.exit(1)

    
    LOG.info('{{ cookiecutter.project_name_title}} completed.' )



if __name__ == '__main__':
    main()

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

from psengine.{{ cookiecutter.module_name }} import {{ cookiecutter.manager_class_name }}
from psengine.config import Config
from psengine.constants import RF_TOKEN_ENV_VAR
from psengine.logger import RFLogger

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = '{{ cookiecutter.module_name }}-sample/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'

# Initializes the logger
LOG = RFLogger().get_logger()


def parse_cmdline_args():
    """Parse arguments from the command line."""
    parser = argparse.ArgumentParser(description='Recorded Future {{ cookiecutter.manager_name_title }} example app')
    parser.add_argument('-k', '--key', default=os.environ.get(RF_TOKEN_ENV_VAR))
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    )

    return parser.parse_args()


def main():
    args = parse_cmdline_args()
    LOG.setLevel(args.log_level)
    LOG.info('Recorded Future {{ cookiecutter.manager_name_title }} usage example')

    Config.init(rf_token=args.key, app_id=APP_ID, platform_id=PLATFORM_ID)

    # {{ cookiecutter.manager_class_name }} will  automatically use the token set by the GlobalConfigSingleton,
    # but you can also pass it as a parameter {{ cookiecutter.manager_class_name }}(rf_token='your_token)
    {{ cookiecutter.manager_file_name }} = {{ cookiecutter.manager_class_name }}()

    result = {{ cookiecutter.manager_file_name }}.call_and_get_something('tQHD_j')


    LOG.info('Recorded Future {{ cookiecutter.manager_name_title }} usage example completed')


if __name__ == '__main__':
    main()

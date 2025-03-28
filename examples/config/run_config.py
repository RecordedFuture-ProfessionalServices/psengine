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
from pathlib import Path

from psengine.config import Config, ConfigModel, get_config
from psengine.logger import RFLogger

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = 'config-sample/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'

# Initializes the logger
LOG = RFLogger().get_logger()
CONFIG_PATH = Path(__file__).parent / 'configs'


def print_config(config: ConfigModel) -> None:
    LOG.info('Configuration settings:')
    for key, value in config.dict().items():
        LOG.info(f'  {key}: {value}')


def main():
    LOG.info('Config will use the following precedence for settings variables:')
    LOG.info('1. Arguments passed to GlobalConfig.init()')
    LOG.info("2. Environment variables with 'RF_' prefix")
    LOG.info('3. Configuration file specified with config_path argument in GlobalConfig.init()')
    LOG.info('4. Variables loaded from the secrets directory')
    LOG.info('5. Default values for the Config model')

    LOG.info('The following RF_* environment variables are set:')
    for arg in os.environ:
        if arg.startswith('RF_'):
            LOG.info(f'  {arg}={os.environ[arg]}')

    LOG.info('Always call GlobalConfig.init() first to initialize the configuration')
    LOG.info('Initializing configuration with no arguments')
    Config.init()
    LOG.info('Always call get_config() to get a single instance of Config shared by all classes')
    config = get_config()
    print_config(config)

    LOG.info('Initializing config with rf_token argument')
    Config.init(rf_token='a' * 32)
    config = get_config()
    LOG.info('Config masks secret values')
    LOG.info('  Masked secret: ' + str(config.rf_token))
    LOG.info('  Access secret values with get_secret_value()')
    LOG.info('  Unmasked secret: ' + config.rf_token.get_secret_value())

    LOG.info('Initializing configuration with .toml file')
    Config.init(config_path=CONFIG_PATH / 'config.toml')
    print_config(get_config())

    LOG.info('Config example complete')


if __name__ == '__main__':
    main()

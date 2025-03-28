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
from pathlib import Path

from psengine.config import Config, get_config
from psengine.constants import RF_TOKEN_ENV_VAR
from psengine.logger import RFLogger
from psengine.risklists import RisklistMgr

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = 'get-risklists-sample/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'

# Initializes the logger
LOG = RFLogger().get_logger()


def parse_cmdline_args():
    """Parse arguments from the command line."""
    LOG.info('Parsing command line arguments')
    parser = argparse.ArgumentParser(description='Recorded Future Get Risklists example app')
    parser.add_argument(
        '-k',
        '--key',
        help='Recorded Future API key',
        dest='rf_token',
        default=os.environ.get(RF_TOKEN_ENV_VAR),
    )
    parser.add_argument(
        '--log-level',
        help='Logging level',
        dest='log_level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    )

    return parser.parse_args()


def main():
    args = parse_cmdline_args()
    LOG.setLevel(args.log_level)
    LOG.info('Recorded Future get risk lists example')
    Config.init(config_path=Path(__file__).parent / 'config.toml')
    config = get_config()
    mgr = RisklistMgr()

    LOG.info('Getting risklist from fusion. Path specified in config.toml')
    data = mgr.fetch_risklist(list=config.ip_reputation_path, validate=None)
    for d in data:
        LOG.info(d)

    print('')
    LOG.info('Getting IP recentLinkedToCyberAttack risklist')
    data = mgr.fetch_risklist(list='recentLinkedToCyberAttack', entity_type='ip')
    count = 0
    while count < 2:
        LOG.info(next(data))
        count += 1

    print('')
    LOG.info('Getting default IP risklist')
    data = mgr.fetch_risklist(list='default', entity_type='ip')
    count = 0
    while count < 2:
        LOG.info(next(data))
        count += 1

    LOG.info('Recorded Future get risk lists example completed')


if __name__ == '__main__':
    main()

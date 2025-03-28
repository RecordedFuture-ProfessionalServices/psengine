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

from psengine.config import Config, get_config
from psengine.constants import RF_TOKEN_ENV_VAR
from psengine.enrich import LookupMgr, SoarMgr
from psengine.logger import RFLogger

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = 'get-enrichment-sample/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'

# Initializes the logger
LOG = RFLogger().get_logger()


def parse_cmdline_args():
    """Parse arguments from the command line."""
    parser = argparse.ArgumentParser(description='Recorded Future IOC Enrichment example app')
    parser.add_argument('-k', '--key', default=os.environ.get(RF_TOKEN_ENV_VAR))
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    )
    parser.add_argument('--input-file', default='input_file.csv')
    return parser.parse_args()


def main():
    args = parse_cmdline_args()
    LOG.setLevel(args.log_level)
    LOG.info('Recorded Future IOC Enrichment example')

    Config.init(rf_token=args.key, app_id=APP_ID, platform_id=PLATFORM_ID, max_workers=5)
    config = get_config()

    LOG.info('Recorded Future IOC Enrichment Lookup example started')

    # Mgr classes below will automatically use the token set by the GlobalConfigSingleton,
    # but you can also pass it as a parameter during INIT (rf_token='your_token)
    lookup_mgr = LookupMgr()
    soar_mgr = SoarMgr()

    ips = lookup_mgr.lookup_bulk(
        entity=['190.55.186.222', '206.189.28.199'],
        entity_type='IpAddress',
        max_workers=config.max_workers,
    )
    dom = lookup_mgr.lookup('cpejcogzznpudbsmaxxm.com', 'domain', fields=['intelCard'])
    entity_id = lookup_mgr.lookup('cwLCv5', 'vulnerability')

    for ip in ips:
        LOG.info(f'\tEntity: {ip.entity}')
        LOG.info(f'\tEntity Type: {ip.entity_type}')
        LOG.info(f'\tIs Enriched: {ip.is_enriched}')
        if isinstance(ip.content, str):
            LOG.info(f'\tRisk Score: {ip.content}\n')
        else:
            LOG.info(f'\tRisk Score: {ip.content.risk.score}\n')

    LOG.info(f'\tEntity: {dom.entity}')
    LOG.info(f'\tRisk Score: {dom.content.risk.score}\n')

    LOG.info(f'\tEntity: {entity_id.entity}')
    LOG.info(f'\tRisk Score: {entity_id.content.risk.score}\n')

    LOG.info('Recorded Future IOC Enrichment Lookup example completed')

    LOG.info('Recorded Future IOC Enrichment SOAR example started')

    data = soar_mgr.soar(
        ip=['1.1.1.1', '190.55.186.222'],
        domain=['google.com', 'albdfhln.com'],
        vulnerability=['CVE-2021-42013'],
        # companybydomain=['facebook.com'],
    )
    for d in data:
        LOG.info(f'\tEntity: {d.entity}')
        LOG.info(f'\tEntity Risk Score: {d.content.risk.score}\n')

    LOG.info('Recorded Future IOC Enrichment SOAR completed ')


if __name__ == '__main__':
    main()

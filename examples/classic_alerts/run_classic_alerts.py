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
from json import dumps
from pathlib import Path

from psengine.classic_alerts import ClassicAlertMgr
from psengine.classic_alerts.helpers import save_image, save_images
from psengine.config import Config
from psengine.constants import RF_TOKEN_ENV_VAR
from psengine.logger import RFLogger

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = 'classic-alerts-sample/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'Splunk/9.0.0'

# Initializes the logger
LOG = RFLogger().get_logger()

OUTPUT_DIR = Path(__file__).parent / 'alerts'


def parse_cmdline_args():
    """Parse arguments from the command line."""
    parser = argparse.ArgumentParser(description='Recorded Future Get Alerts example app')
    parser.add_argument(
        '-k',
        '--key',
        help='Recorded Future API key',
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
    LOG.info('Recorded Future Classic Alerts example')

    Config.init(rf_token=args.key, app_id=APP_ID, platform_id=PLATFORM_ID)

    # ClassicAlertMgr will  automatically use the token set by the GlobalConfigSingleton,
    # but you can also pass it as a parameter ClassicAlertMgr(rf_token='your_token)
    alert_mgr = ClassicAlertMgr()

    search_results = alert_mgr.search(triggered='-1d')
    LOG.info(f'Search returned {len(search_results)} alerts')

    one_alert = alert_mgr.fetch(search_results[0].id_, fields=['id'])
    # Write alert to file
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / 'one_alert.json').write_text(dumps(one_alert.json()))

    LOG.info(f'Fetched: {one_alert.id_} - {one_alert.title}')

    triggered_ids = [search_results[0].id_, search_results[1].id_]
    multiple_alerts = alert_mgr.fetch_bulk(ids=triggered_ids)
    for alert in multiple_alerts:
        LOG.info(f'Fetched: {alert.id_} - {alert.title}')
        (OUTPUT_DIR / alert.id_).write_text(dumps(alert.json()))

    two_hits = alert_mgr.fetch_hits(ids=triggered_ids)
    for alert in two_hits:
        (OUTPUT_DIR / alert.id_).write_text(dumps(alert.json()))

    rules = alert_mgr.fetch_rules(freetext=['leaked', 'domains'], max_results=21)
    LOG.info(f'Fetched {len(rules)} rules')
    for rule in rules:
        LOG.info(f'Rule ID: {rule.id_} Name: {rule.title}')

    raw_image = alert_mgr.fetch_image(id_='img:d4620c6a-c789-48aa-b652-b47e0d06d91a')

    save_image(image_bytes=raw_image, file_name='d4620c6a-c789-48aa-b652-b47e0d06d91a')

    alert = alert_mgr.fetch('xOTsae')
    alert_mgr.fetch_all_images(alert)

    results = save_images(alert)

    # Bulk update alerts to the same status
    update_resp = alert_mgr.update_status(['whAZiP', 'whz4Ya'], 'Dismissed')

    # Bulk update alerts with various statuses, notes, etc..
    updates = [
        {'id': 'w1KF1z', 'note': 'Changes from sample app', 'statusInPortal': 'Pending'},
        {
            'id': 'whz4Ya',
            'note': 'Comment from sample app!',
        },
    ]
    updates_resp = alert_mgr.update(updates)

    LOG.info('Recorded Future Classic Alerts example completed')


if __name__ == '__main__':
    main()

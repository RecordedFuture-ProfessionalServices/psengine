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
from datetime import datetime, timedelta
from time import sleep

from more_itertools import batched

from psengine.config import Config
from psengine.constants import RF_TOKEN_ENV_VAR, TIMESTAMP_STR
from psengine.identity import IdentityMgr
from psengine.logger import RFLogger

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = 'identity-sample/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'

# Initializes the logger
LOG = RFLogger().get_logger()


def parse_cmdline_args():
    """Parse arguments from the command line."""
    parser = argparse.ArgumentParser(description='Recorded Future Identity example app')
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
    LOG.info('Recorded Future Identity usage example')

    Config.init(rf_token=args.key, app_id=APP_ID, platform_id=PLATFORM_ID)

    identity_mgr = IdentityMgr()

    # get novel workforce detections from the last week
    created = (datetime.now() - timedelta(days=7)).strftime(TIMESTAMP_STR)
    detections = identity_mgr.fetch_detections(
        novel_only=True, detection_type='Workforce', created_gte=created
    )

    # get the most recent detection and pull the associated
    # incident report from the dump source with detail
    detections.detections.sort(key=lambda x: x.created, reverse=True)
    recent_detection = detections.detections[0]
    LOG.info(f'Most recent detection: {recent_detection.created}')

    source = 'identity-module-source-data/malware_log_hashed_output/ce46cf/ce46cf7845799a604fa8e324639c112f91cb583c328c40696bfac5ab69bbe667.zip'  # noqa: E501
    LOG.info(f'Fetching Incident Report for {source}')

    # fetch Incident Report
    incident_report = identity_mgr.fetch_incident_report(source=source, include_details=True)
    creds_count = len(incident_report.credentials)

    LOG.info(f'Incident Report associated Malware: {incident_report.details.malware_family}')

    LOG.info('Fetching the latest exposures')

    search = identity_mgr.search_credentials(
        domains='norsegods.online', domain_types='Email', first_downloaded_gte='-7d'
    )

    data = []
    # the sleep and batched combination here is to avoid rate limiting when the search high results
    for d in batched(search, 50):
        data.extend(
            identity_mgr.lookup_credentials(
                subjects_login=d, max_results=500, identities_per_page=50
            )
        )
        sleep(5)

    for identity in data:
        for cred in identity.credentials:
            LOG.info(cred)

    LOG.info('Recorded Future Identity usage example completed')


if __name__ == '__main__':
    main()

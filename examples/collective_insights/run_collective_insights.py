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
import datetime
import os

from psengine.collective_insights import (
    DETECTION_SUB_TYPE_SIGMA,
    DETECTION_TYPE_CORRELATION,
    DETECTION_TYPE_PLAYBOOK,
    DETECTION_TYPE_RULE,
    ENTITY_HASH,
    ENTITY_IP,
    ENTITY_URL,
    CollectiveInsights,
)
from psengine.config import Config
from psengine.constants import RF_TOKEN_ENV_VAR
from psengine.logger import RFLogger

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = 'ps-collective-insights/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'

# Initializes the logger
LOG = RFLogger().get_logger()


def parse_cmdline_args():
    """Parse arguments from the command line."""
    parser = argparse.ArgumentParser(description='Recorded Future Collective Insights')
    parser.add_argument(
        '-k',
        '--key',
        default=os.environ.get(RF_TOKEN_ENV_VAR),
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    )

    return parser.parse_args()


def main():
    args = parse_cmdline_args()
    LOG.setLevel(args.log_level)
    LOG.info('Recorded Future Collective Insights')

    Config.init(rf_token=args.key, app_id=APP_ID, platform_id=PLATFORM_ID)

    # CollectiveInsights will  automatically use the token set by the GlobalConfigSingleton,
    # but you can also pass it as a parameter CollectiveInsights(rf_token='your_token)
    ci = CollectiveInsights()

    # Get time now
    now = datetime.datetime.utcnow().isoformat()[:-3] + 'Z'

    insight1 = ci.create(
        ioc_value='fbee00cb1d1ea4d7e0604436d9a36def71a9f3be804f1e2b8d117fd5d35aeabc',
        ioc_type=ENTITY_HASH,
        detection_type=DETECTION_TYPE_RULE,
        detection_sub_type=DETECTION_SUB_TYPE_SIGMA,
        detection_id='doc:o6_lui',
        detection_name='Instance of Alleged New Wiper Malware',
        ioc_field='hash',
        ioc_source_type='symantec',
        timestamp=now,
        incident_id='Incident 001',
        incident_name='Malware detected',
        incident_type='RF Sigma Rule',
        mitre_codes=['T1542', 'T1485'],
        malwares=['Aesthetic Wiper'],
    )

    insight2 = ci.create(
        ioc_value='139.196.234.164',
        ioc_type=ENTITY_IP,
        detection_type=DETECTION_TYPE_PLAYBOOK,
        mitre_codes='T1542',
        malwares='Cobalt Strike',
        timestamp=now,
    )

    insight3 = ci.create(
        ioc_value='https://new2qt.firebaseapp.com/',
        ioc_type=ENTITY_URL,
        detection_type=DETECTION_TYPE_CORRELATION,
        detection_name='p_default_url_risklist',
        timestamp=now,
    )

    # The class also takes **kwargs, so you can add any additional properties
    # as soon as the API supports them. This is really meant to be a temporary
    # workaround until PSEngine adds official support for these properties.
    insight4 = ci.create(
        ioc_value='https://new2qt.firebaseapp.com/',
        ioc_type=ENTITY_URL,
        detection_type=DETECTION_TYPE_CORRELATION,
        detection_id='p_default_url_risklist',
        detection_name='p_default_url_risklist',
        wowza='apples',
        timestamp=now,
        cool_new_property_list=['apples', 'oranges', 'bananas'],
        some_new_dict={'key': 'oranges', 'key2': 'apples'},
    )

    insights = [insight1, insight2, insight3]

    # # Can submit a single insight or a list of insights
    # ci.submit(insight=insight1)
    ci.submit(insight=insights)

    LOG.info('Recorded Future Collective Insights completed')


if __name__ == '__main__':
    main()

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

from psengine.config import Config
from psengine.constants import RF_TOKEN_ENV_VAR
from psengine.detection import DetectionMgr, save_rule
from psengine.entity_match import EntityMatchMgr
from psengine.helpers import FileHelpers
from psengine.logger import RFLogger

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = 'detection-rules-sample/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'

# Initializes the logger
LOG = RFLogger().get_logger()

OUTDIR = Path(__file__).parent / 'detections'


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--key', default=os.environ.get(RF_TOKEN_ENV_VAR))
    parser.add_argument(
        '-f',
        '--file',
        help='Entity list file. Should only contain a single column of entity IDs',
        default=Path(__file__).absolute().parent / 'entitylist.csv',
    )
    parser.add_argument('-r', '--rule-type', choices=['yara', 'sigma', 'snort'])
    parser.add_argument('-l', '--limit', default=10)
    parser.add_argument('-s', '--start-date', help='Start date for rules to fetch')
    parser.add_argument(
        '--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    )

    return parser.parse_args()


def main():
    args = get_args()
    LOG.setLevel(args.log_level)
    Config.init(rf_token=args.key, app_id=APP_ID, platform_id=PLATFORM_ID)

    # Mgr classes below will automatically use the token set by the GlobalConfigSingleton,
    # but you can also pass it as a parameter during INIT (rf_token='your_token)
    detection_mgr = DetectionMgr()
    match_mgr = EntityMatchMgr()

    entitylist = []

    entitylist = FileHelpers.read_csv(csv_file=args.file, single_column=False)
    entity_ids = match_mgr.resolve_entity_ids(entitylist, limit=args.limit)
    entity_ids = (
        [entity.content.id_ for entity in entity_ids]
        if isinstance(entity_ids, list)
        else [entity_ids.content.id_]
    )

    rule_list = detection_mgr.search(
        entities=entity_ids,
        max_results=args.limit,
        created_before=args.start_date,
        detection_rule=args.rule_type,
    )

    for rule in rule_list:
        LOG.info(rule)
        save_rule(rule, output_directory=OUTDIR)

    LOG.info('Performing single lookup by detection ID')
    rule = detection_mgr.fetch('doc:jUYUmI')
    LOG.info(rule)


if __name__ == '__main__':
    main()

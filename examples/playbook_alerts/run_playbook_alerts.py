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

from psengine.config import Config
from psengine.constants import RF_TOKEN_ENV_VAR
from psengine.logger import RFLogger
from psengine.playbook_alerts import PACategory, PlaybookAlertMgr
from psengine.playbook_alerts.helpers import save_pba_images

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = 'playbook-alerts-sample/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'

# Initializes the logger
LOG = RFLogger().get_logger()

OUTPUT_DIR = Path(__file__).parent / 'playbook_alerts'


def parse_cmdline_args():
    """Parse arguments from the command line."""
    parser = argparse.ArgumentParser(description='Recorded Future Playbook Alerts example app')
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


def do_alerts(playbook_mgr: PlaybookAlertMgr):  # noqa: C901
    query = {
        'max_results': 2,
        'statuses': ['New', 'InProgress'],
        'filter_from': 0,
        'direction': 'asc',
        'category': ['domain_abuse'],
        'created_from': '2023-09-01',
        'created_until': '2023-09-05',
        'updated_from': '2023-09-01',
        'updated_until': '2023-09-05',
    }

    # search method accepts all the params from API /search endpoint
    # created_from/until, updated_from/until are special names for e.g. created_range.from
    results = playbook_mgr.fetch_bulk(**query)
    LOG.info(f'Search found {len(results)} alerts')

    OUTPUT_DIR.mkdir(exist_ok=True)
    for alert in results:
        (OUTPUT_DIR / f'{alert.playbook_alert_id}.json').write_text(dumps(alert.json()))
    save_pba_images(results)

    query_alerts = playbook_mgr.fetch_bulk(
        max_results=1, category=PACategory.THIRD_PARTY_RISK.value
    )

    # Returned PA alerts are objects of its own and you can access some values via attributes
    for alert in query_alerts:
        LOG.info(f'Alert ID: {alert.playbook_alert_id}')
        assessments = alert.panel_evidence_summary.assessments
        assessment_results = [f'{a.risk_rule}: {a.evidence.summary}' for a in assessments]
        LOG.info('Assessments {}'.format('\n'.join(assessment_results)))

    # Example showing how to get different values from alerts
    results = playbook_mgr.fetch_bulk(
        max_results=1, category=[PACategory.IDENTITY_NOVEL_EXPOSURES.value]
    )
    for alert in results:
        LOG.info(f'Alert ID: {alert.playbook_alert_id}')
        LOG.info(f'Subject: {alert.panel_evidence_summary.subject}')
        LOG.info(f'Assessments: {alert.assessment_names}')
        LOG.info('Dump:')
        LOG.info(f'  {alert.panel_evidence_summary.dump.name}')
        LOG.info(f'  {alert.panel_evidence_summary.dump.description}')
        LOG.info(f'Authorization URL: {alert.panel_evidence_summary.authorization_url}')
        LOG.info(
            f'Exfiltration Date: {alert.panel_evidence_summary.compromised_host.exfiltration_date}'
        )
        LOG.info(f'Exposed secret type: {alert.panel_evidence_summary.exposed_secret.type_}')
        LOG.info(
            f'Exposed secret effectively clear: '
            f'{alert.panel_evidence_summary.exposed_secret.effectively_clear}'
        )

    # Example how to bulk_fetch using alert id and category
    alerts_to_fetch = [
        ('task:5c25fb03-ddfe-48be-a43d-66a20a3c9aca', 'domain_abuse'),
        ('task:cec36358-4ba4-4aa9-b571-21a9a9eb1239', 'code_repo_leakage'),
    ]
    results = playbook_mgr.fetch_bulk(alerts=alerts_to_fetch)

    # Please see is psengine.playbook_alerts submodule
    # for the rest of the PA classes and their attributes

    # For demonstration purposes this Alert ID belongs to Professional Services Development
    # enterprise. Comment out the below or swap for an alert ID from your own enterprise.
    LOG.info('This is how to fetch an individual alert based on the alert ID & category')
    p_alert = playbook_mgr.fetch(
        alert_id='task:a35728f8-2410-49fa-ab92-7bcf2cba3b48',
        category=PACategory.DOMAIN_ABUSE,
    )

    p_alert = playbook_mgr.fetch(
        alert_id='task:7d3a43df-40d4-486e-bb4a-12f70f291df1',
        category=PACategory.CODE_REPO_LEAKAGE,
    )

    # You can also fetch without supplying an alert category
    p_alert = playbook_mgr.fetch(alert_id='task:30bdc39c-5e0d-4161-89ab-3bd78c726152')
    p_alert = playbook_mgr.fetch(alert_id='task:c641430b-9d9e-4722-abb6-fd7e6bbdcba7')

    # Example how to update a PBA Alert
    playbook_mgr.update(
        p_alert,
        priority='High',
        log_entry='Updating an alert from the sample app!',
        status='InProgress',
    )


def main():
    args = parse_cmdline_args()
    LOG.setLevel(args.log_level)
    LOG.info('Recorded Future: Playbook Alert Sample Application')

    Config.init(rf_token=args.key, app_id=APP_ID, platform_id=PLATFORM_ID)

    # PlaybookAlertMgr will  automatically use the token set by the GlobalConfigSingleton,
    # but you can also pass it as a parameter PlaybookAlertMgr(rf_token='your_token)
    playbook_mgr = PlaybookAlertMgr()

    do_alerts(playbook_mgr)

    LOG.info('Recorded Future: Playbook alert Sample Application completed')


if __name__ == '__main__':
    main()

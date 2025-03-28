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

from psengine.analyst_notes import AnalystNoteMgr
from psengine.config import Config
from psengine.constants import RF_TOKEN_ENV_VAR
from psengine.enrich import LookupMgr
from psengine.logger import RFLogger
from psengine.risklists import DefaultRiskList, RisklistMgr
from psengine.stix2 import ENTITY_TYPE_MAP, EnrichedIndicator, RFBundle

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = 'stix2-sample/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'

# Initializes the logger
LOG = RFLogger().get_logger()


def parse_cmdline_args():
    """Parse arguments from the command line."""
    parser = argparse.ArgumentParser(description='Recorded Future STIX2 example app')
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
    LOG.info('Recorded Future STIX2 usage example')
    Config.init(rf_token=args.key, app_id=APP_ID, platform_id=PLATFORM_ID)

    # Mgr classes below will automatically use the token set by the GlobalConfigSingleton,
    # but you can also pass it as a parameter during INIT (rf_token='your_token)
    rsm = RisklistMgr()
    rfem = LookupMgr()
    note_mgr = AnalystNoteMgr()

    save_path = Path(__file__).resolve().parent.joinpath('stix2')
    save_path.mkdir(exist_ok=True, parents=True)

    # tQHD_j - existing note without attachment
    # tPtLVw - existing note with PDF attachment
    # oJeqDP - existing note with yara attachment
    # o6_lui - existing note with sigma attachment
    # cynQie - existing note with snort attachment

    notes_to_lookup = ['tQHD_j', 'tPtLVw', 'oJeqDP', 'o6_lui', 'cynQie']
    for note_id in notes_to_lookup:
        note = note_mgr.lookup(note_id)
        attachment = None
        if note.attributes.attachment:
            attachment, attachment_type = note_mgr.fetch_attachment(note.id_)

        note_bundle = RFBundle.from_analyst_note(note, attachment, True)

        # write to file
        note_path = save_path / f'note_bundle_{note_id}.json'
        with note_path.open('w') as f:
            f.write(note_bundle.serialize())

    risklist = list(rsm.fetch_risklist('recentLinkedToAPT', 'ip', validate=DefaultRiskList))
    risklist_bundle = RFBundle.from_default_risklist(risklist, 'ip')

    # write to file
    risklist_path = save_path / 'risklist_ip_recentLinkedToAPT_bundle.json'
    with risklist_path.open('w') as f:
        f.write(risklist_bundle.serialize())

    iocs = [
        'avsvmcloud.com',
        'd6097e942dd0fdc1fb28ec1814780e6ecc169ec6d24f9954e71954eedbc4c70e',
        'http://adminsys.serveftp.com/nensa/fabio/ex/478632215/zer7855/nuns566623',
        '5.35.130.255',
    ]
    results = []
    for i, entity_type in enumerate(['domain', 'hash', 'url', 'ip']):
        results.append(
            rfem.lookup(
                entity=iocs[i],
                entity_type=entity_type,
                fields=['risk', 'links', 'riskMapping', 'aiInsights'],
            )
        )

    for res in results:
        LOG.info(f'Creating EnrichedIndicator for {res.entity}')
        enriched_indicator = EnrichedIndicator(
            name=res.entity,
            type_=ENTITY_TYPE_MAP[res.entity_type],
            evidence_details=res.content.risk.evidence_details,
            link_hits=res.content.links.hits,
            risk_mapping=res.content.risk_mapping,
            confidence=res.content.risk.score,
            ai_insights=res.content.ai_insights,
        )

        # write to file
        enrich_path = save_path / f'enriched_indicator_{res.entity_type}.json'
        with enrich_path.open('w') as f:
            f.write(enriched_indicator.bundle.serialize())

    # EnrichedIndicator has a bundle property that returns a STIX2 bundle
    enriched_indicator_bundle = enriched_indicator.bundle

    LOG.info('Recorded Future STIX2 usage example completed')


if __name__ == '__main__':
    main()

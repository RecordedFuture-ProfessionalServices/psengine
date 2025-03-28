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

from psengine.analyst_notes import AnalystNoteMgr, save_attachment, save_note
from psengine.config import Config
from psengine.constants import RF_TOKEN_ENV_VAR
from psengine.logger import RFLogger

# Name & version of the integration itself
# Below value is set for demo purposes
APP_ID = 'analyst-note-sample/1.0.0'

# Name & version of the tool this integrates with (Optional)
# Below value is set for demo purposes
PLATFORM_ID = 'PSE/1.0.0'

# Initializes the logger
LOG = RFLogger().get_logger()

OUTDIR = Path(__file__).parent / 'analyst_notes'


def parse_cmdline_args():
    """Parse arguments from the command line."""
    parser = argparse.ArgumentParser(description='Recorded Future Ananlyst Notes example app')
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
    LOG.info('Recorded Future Analyst Notes usage example')

    Config.init(rf_token=args.key, app_id=APP_ID, platform_id=PLATFORM_ID)

    note_mgr = AnalystNoteMgr()

    # tQHD_j - existing note without attachment
    # tPtLVw - existing note with PDF attachment
    # oJeqDP - existing note with yara attachment
    # o6_lui - existing note with sigma attachment
    # cynQie - existing note with snort attachment

    note = note_mgr.lookup('tQHD_j')

    LOG.info(f'{note} written by {note.source.name}')
    LOG.info(note.attributes.text)
    LOG.info(f'Notes entities: {note.attributes.note_entities}\n')

    save_note(note, OUTDIR)

    search_results = note_mgr.search(topic=['TXSFt2', 'UrMRnT'], published='-200d')
    LOG.info('Analyst notes returned by the search:')
    for note in search_results:
        LOG.info(f'  {note.attributes.title}')

    for note_id in ('tPtLVw', 'oJeqDP', 'o6_lui', 'cynQie'):
        content, ext = note_mgr.fetch_attachment(note_id)
        save_attachment(note_id, content, ext, OUTDIR)

    LOG.info('Example of using note preview')
    note_preview = note_mgr.preview(
        title='ernest test preview',
        text='wowza what a cool text this is ;)',
        # published='2021-01-01T00:00:00',
        # topic='UrMRnT',
        # context_entities=['idn:test.com'],
        # note_entities=['idn:google.com'],
    )
    LOG.info(f'Preview note: {note_preview}')

    LOG.info('Example of using note publish')
    note_preview = note_mgr.publish(
        title='ernest test publish',
        text='wowza what a cool text this is ;)',
        published='2021-01-01T00:00:00',
        topic='UrMRnT',
        context_entities=['idn:test.com'],
        note_entities=['idn:google.com'],
        # validation_urls=['idn:google.com'], # This should be fixed by API team
    )
    LOG.info(f'Published note ID: {note_preview.note_id}')

    LOG.info('Recorded Future Ananlyst Notes usage example completed')


if __name__ == '__main__':
    main()

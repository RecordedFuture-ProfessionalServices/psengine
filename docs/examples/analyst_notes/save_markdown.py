from pathlib import Path

from psengine.analyst_notes import AnalystNoteMgr, save_attachment

OUTPUT_DIR = Path(__file__).parent / 'attachments'
OUTPUT_DIR.mkdir(exist_ok=True)

mgr = AnalystNoteMgr()
notes = mgr.search(published='-1d', max_results=1000)

for note in notes:
    save_attachment(note.id_, note.markdown(), 'md', OUTPUT_DIR)

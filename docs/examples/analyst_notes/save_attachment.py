from pathlib import Path

from psengine.analyst_notes import AnalystNoteMgr, save_attachment

OUTPUT_DIR = Path(__file__).parent / 'attachments'
OUTPUT_DIR.mkdir(exist_ok=True)

mgr = AnalystNoteMgr()
notes = mgr.search(published='-1d', max_results=1000)

for note in notes:
    attachment, ext = mgr.fetch_attachment(note.id_)
    if attachment and ext:
        save_attachment(note.id_, attachment, ext, OUTPUT_DIR)

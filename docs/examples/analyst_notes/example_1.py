from pathlib import Path

from psengine.analyst_notes import (
    AnalystNoteMgr,
    save_attachment,
)

OUTPUT_DIR = Path.cwd() / 'attachments'
OUTPUT_DIR.mkdir(exist_ok=True)


mgr = AnalystNoteMgr()
notes = mgr.search(published='-1d')

for note in notes:
    if note.attributes.attachment:
        attachment, ext = mgr.fetch_attachment(note.id_)
        save_attachment(
            note.id_, attachment, ext, OUTPUT_DIR
        )

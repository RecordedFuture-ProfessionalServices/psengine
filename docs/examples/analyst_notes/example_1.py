import os

from psengine.analyst_notes import (
    AnalystNoteMgr,
    save_attachment,
)

OUTPUT_DIR = os.path.join(os.getcwd(), "attachments")
os.makedirs(OUTPUT_DIR, exist_ok=True)

mgr = AnalystNoteMgr()
notes = mgr.search(published="-1d")

for note in notes:
    if note.attributes.attachment:
        attachment, ext = mgr.fetch_attachment(note.id_)
        save_attachment(
            note.id_, attachment, ext, OUTPUT_DIR
        )

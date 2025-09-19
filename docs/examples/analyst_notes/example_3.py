import os

from psengine.analyst_notes import AnalystNoteMgr, save_note

OUTPUT_DIR = os.path.join(os.getcwd(), "attachments")
os.makedirs(OUTPUT_DIR, exist_ok=True)

mgr = AnalystNoteMgr()
notes = mgr.search(
    published="-1y", topic=["xG68dQ", "xG68dS"]
)

for note in notes:
    save_note(note, OUTPUT_DIR)

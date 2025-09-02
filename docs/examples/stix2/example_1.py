from pathlib import Path

from psengine.analyst_notes import AnalystNoteMgr
from psengine.stix2 import RFBundle

OUTPUT_DIR = Path(__file__).parent / "bundles"
OUTPUT_DIR.mkdir(exist_ok=True)

note_id = "o6_lui"
out_file = OUTPUT_DIR / f"note_bundle_{note_id}.json"

note_mgr = AnalystNoteMgr()

attachment = None
note = note_mgr.lookup(note_id)
if note.attributes.attachment:
    attachment, attachment_type = note_mgr.fetch_attachment(
        note.id_
    )

note_bundle = RFBundle.from_analyst_note(note, attachment)
out_file.write_text(note_bundle.serialize())

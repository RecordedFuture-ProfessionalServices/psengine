import os

from rich.console import Console

from psengine.analyst_notes import (
    AnalystNoteMgr,
    save_attachment,
)

OUTPUT_DIR = os.path.join(os.getcwd(), "attachments")
os.makedirs(OUTPUT_DIR, exist_ok=True)

mgr = AnalystNoteMgr()
console = Console()
notes = mgr.search(published="-1d", max_results=2)

for note in notes:
    markdown = note.markdown(diamond_model=True)
    save_attachment(note.id_, markdown, "md", OUTPUT_DIR)

    console.print(markdown)
    console.print("---------------------------")

from pathlib import Path

from psengine.analyst_notes import (
    AnalystNoteMgr,
    save_attachment,
)
from rich.console import Console

OUTPUT_DIR = Path.cwd() / 'attachments'
OUTPUT_DIR.mkdir(exist_ok=True)

mgr = AnalystNoteMgr()
console = Console()
notes = mgr.search(published='-1d', max_results=2)

for note in notes:
    markdown = note.markdown(diamond_model=True)
    save_attachment(note.id_, markdown, 'md', OUTPUT_DIR)

    console.print(markdown)
    console.print('---------------------------')

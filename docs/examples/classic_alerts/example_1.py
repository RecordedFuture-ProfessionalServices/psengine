from pathlib import Path

from psengine.classic_alerts import ClassicAlertMgr

OUTPUT_DIR = Path.cwd() / 'alerts'
OUTPUT_DIR.mkdir(exist_ok=True)

mgr = ClassicAlertMgr()
alerts = mgr.search(triggered='-1d', status='New', fields=['url'])

for alert in alerts:
    markdown = alert.markdown(
        ai_insights=False,
        triggered_by=False,
        defang_iocs=True,
    )
    (OUTPUT_DIR / f'{alert.id_}.md').write_text(markdown)

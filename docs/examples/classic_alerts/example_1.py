import os
from pathlib import Path

from psengine.classic_alerts import ClassicAlertMgr
from psengine.classic_alerts.constants import ALL_CA_FIELDS

OUTPUT_DIR = os.path.join(os.getcwd(), "alerts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

mgr = ClassicAlertMgr()
alerts = mgr.search(
    triggered="-1d", status="New", fields=ALL_CA_FIELDS
)

for alert in alerts:
    markdown = alert.markdown(
        ai_insights=False,
        triggered_by=False,
        defang_iocs=True,
    )
    Path(os.path.join(OUTPUT_DIR, f"{alert.id_}.md")).write_text(markdown)

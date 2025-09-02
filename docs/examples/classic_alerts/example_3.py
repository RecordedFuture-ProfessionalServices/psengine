import json
from collections import defaultdict
from pathlib import Path

from psengine.classic_alerts import ClassicAlertMgr

OUTPUT_DIR = Path(__file__).parent / "alerts"
OUTPUT_DIR.mkdir(exist_ok=True)

ALERT_IDS = ["9Z0ts8", "9Z0ttT"]

data = defaultdict(list)
mgr = ClassicAlertMgr()
hits = mgr.fetch_hits(ALERT_IDS)

for hit in hits:
    data[hit.alert_id].append(hit.json())

for alert_id, hits in data.items():
    (OUTPUT_DIR / f"{alert_id}.json").write_text(
        json.dumps(hits, indent=4)
    )

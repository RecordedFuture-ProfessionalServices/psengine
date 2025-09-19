import os

from psengine.classic_alerts import ClassicAlertMgr
from psengine.classic_alerts.helpers import save_images

OUTPUT_DIR = os.path.join(os.getcwd(), "alerts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ALERT_IDS = ["9Z0ts8", "9Z0ttT"]

mgr = ClassicAlertMgr()
alerts = mgr.fetch_bulk(ALERT_IDS, max_workers=2)

for alert in alerts:
    mgr.fetch_all_images(alert)
    save_images(alert, OUTPUT_DIR)

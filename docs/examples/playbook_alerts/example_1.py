import os

from psengine.playbook_alerts import (
    PACategory,
    PlaybookAlertMgr,
)
from psengine.playbook_alerts.helpers import save_pba_images

OUTPUT_DIR = os.path.join(os.getcwd(), "alerts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

mgr = PlaybookAlertMgr()
alert = mgr.fetch(
    alert_id="task:a35728f8-2410-49fa-ab92-7bcf2cba3b48",
    category=PACategory.DOMAIN_ABUSE,
    fetch_images=True,
)

save_pba_images(alert, OUTPUT_DIR)

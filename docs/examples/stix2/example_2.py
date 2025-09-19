import os
from pathlib import Path

from psengine.risklists import DefaultRiskList, RisklistMgr
from psengine.stix2 import RFBundle

OUTPUT_DIR = os.path.join(os.getcwd(), "bundles")
os.makedirs(OUTPUT_DIR, exist_ok=True)

rsm = RisklistMgr()
risklist = list(
    rsm.fetch_risklist(
        "recentLinkedToAPT", "ip", validate=DefaultRiskList
    )
)
risklist_bundle = RFBundle.from_default_risklist(
    risklist, "ip"
)

out_file = Path(
    os.path.join(OUTPUT_DIR, "risklist_ip_recentLinkedToAPT_bundle.json")
)
out_file.write_text(risklist_bundle.serialize())

import json
import os
from pathlib import Path

from psengine.risklists import RisklistMgr
from psengine.risklists.models import DefaultRiskList

OUTPUT_DIR = os.path.join(os.getcwd(), "risklists")
os.makedirs(OUTPUT_DIR, exist_ok=True)

mgr = RisklistMgr()

risklist = list(
    mgr.fetch_risklist(
        "default", "domain", validate=DefaultRiskList
    )
)

out_file = Path(
    os.path.join(OUTPUT_DIR, "default_domain_risklist_validated.json")
)
out_file.write_text(
    json.dumps(
        [entry.json() for entry in risklist], indent=4
    )
)

import json
from pathlib import Path

from psengine.risklists import RisklistMgr

OUTPUT_DIR = Path(__file__).parent / 'risklists'
OUTPUT_DIR.mkdir(exist_ok=True)

mgr = RisklistMgr()

risklist = list(mgr.fetch_risklist('default', 'domain'))

out_file = OUTPUT_DIR / 'default_domain_risklist.json'
out_file.write_text(json.dumps(risklist, indent=4))

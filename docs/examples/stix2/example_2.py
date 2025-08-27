from pathlib import Path

from psengine.risklists import DefaultRiskList, RisklistMgr
from psengine.stix2 import RFBundle

OUTPUT_DIR = Path(__file__).parent / 'bundles'
OUTPUT_DIR.mkdir(exist_ok=True)

rsm = RisklistMgr()
risklist = list(rsm.fetch_risklist('recentLinkedToAPT', 'ip', validate=DefaultRiskList))
risklist_bundle = RFBundle.from_default_risklist(risklist, 'ip')

out_file = OUTPUT_DIR / 'risklist_ip_recentLinkedToAPT_bundle.json'
out_file.write_text(risklist_bundle.serialize())

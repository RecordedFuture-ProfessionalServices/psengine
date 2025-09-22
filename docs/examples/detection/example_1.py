from pathlib import Path

from psengine.detection import DetectionMgr
from psengine.detection.helpers import save_rule

OUTPUT_DIR = Path.cwd() / 'rules'
OUTPUT_DIR.mkdir(exist_ok=True)

mgr = DetectionMgr()
rule = mgr.fetch('doc:aqofps')
save_rule(rule, OUTPUT_DIR)

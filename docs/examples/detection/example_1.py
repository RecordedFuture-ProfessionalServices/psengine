import os

from psengine.detection import DetectionMgr
from psengine.detection.helpers import save_rule

OUTPUT_DIR = os.path.join(os.getcwd(), "rules")
os.makedirs(OUTPUT_DIR, exist_ok=True)

mgr = DetectionMgr()
rule = mgr.fetch("doc:aqofps")
save_rule(rule, OUTPUT_DIR)

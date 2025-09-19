import os

from psengine.detection import DetectionMgr
from psengine.detection.helpers import save_rule

OUTPUT_DIR = os.path.join(os.getcwd(), "rules")
os.makedirs(OUTPUT_DIR, exist_ok=True)

mgr = DetectionMgr()
rules = mgr.search(
    detection_rule="yara", entities=["mitre:T1071"]
)
for rule in rules:
    save_rule(rule, OUTPUT_DIR)

from pathlib import Path

from psengine.detection import DetectionMgr

OUTPUT_DIR = Path.cwd() / 'rules'
OUTPUT_DIR.mkdir(exist_ok=True)
mgr = DetectionMgr()
rules = mgr.search(created_after='-1d')
for rule in rules:
    print(rule)

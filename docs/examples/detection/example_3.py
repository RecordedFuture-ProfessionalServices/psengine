from pathlib import Path

from psengine.detection import DetectionMgr
from psengine.detection.helpers import save_rule
from psengine.entity_match import EntityMatchMgr

OUTPUT_DIR = Path(__file__).parent / 'rules'
OUTPUT_DIR.mkdir(exist_ok=True)

mgr = DetectionMgr()
entity_mgr = EntityMatchMgr()

match_entities = entity_mgr.match('CVE-2021-44228', entity_type='CyberVulnerability', limit=1)
cve = match_entities[0]

if cve.is_found:
    rules = mgr.search(entities=[cve.content.id_])
    for rule in rules:
        save_rule(rule, OUTPUT_DIR)

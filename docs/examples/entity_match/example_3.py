from psengine.entity_match import EntityMatchMgr
from pprint import pprint

mgr = EntityMatchMgr()
data = mgr.resolve_entity_id('wannacry', 'Malware')

pprint(data.model_dump(), indent=4)

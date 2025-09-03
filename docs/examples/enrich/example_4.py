from psengine.enrich import LookupMgr
from pprint import pprint

mgr = LookupMgr()
data = mgr.lookup('CVE-999', 'vulnerability')

pprint(data.model_dump(), indent=4)

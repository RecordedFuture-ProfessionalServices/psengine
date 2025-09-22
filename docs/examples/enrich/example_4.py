from psengine.enrich import LookupMgr

mgr = LookupMgr()
data = mgr.lookup('CVE-999', 'vulnerability')

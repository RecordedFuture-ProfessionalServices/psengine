from psengine.enrich import LookupMgr

mgr = LookupMgr()
cve = mgr.lookup(
    "CVE-2012-1535", "vulnerability", fields=["cvssv3"]
)
if cve.is_enriched:
    print(cve.content.cvssv3.json())

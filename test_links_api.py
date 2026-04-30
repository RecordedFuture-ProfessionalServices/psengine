from psengine.links.links_mgr import LinksMgr
from psengine.links.requests import LinksFilterObjects
lm = LinksMgr()
try:
    res = lm.search(entities=["kvXvR5"], filters=LinksFilterObjects(sources=["technical"]))
    print(f"Success with kvXvR5: {len(res.data[0].links)} links")
except Exception as e:
    print(f"Failed with kvXvR5: {e}")

try:
    res = lm.search(entities=["CyberVulnerability:CVE-2021-44228"], filters=LinksFilterObjects(sources=["technical"]))
    print(f"Success with CyberVulnerability:CVE...: {len(res.data[0].links)} links")
except Exception as e:
    print(f"Failed with CyberVulnerability:CVE...: {e}")


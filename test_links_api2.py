from psengine.links.links_mgr import LinksMgr
from psengine.links.requests import LinksFilterObjects
lm = LinksMgr()
try:
    res = lm.search(entities=["kvXvR5"], filters=LinksFilterObjects(sources=["insikt"]))
    print(f"Success with kvXvR5 (insikt): {len(res.data[0].links)} links")
except Exception as e:
    print(f"Failed with kvXvR5 (insikt): {e}")


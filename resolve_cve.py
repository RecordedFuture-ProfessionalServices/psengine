from psengine.entity_match.entity_match_mgr import EntityMatchMgr
em = EntityMatchMgr()
res = em.resolve_entity_id("CVE-2021-44228")
print(res)

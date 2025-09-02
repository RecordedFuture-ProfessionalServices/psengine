from psengine.entity_match import EntityMatchMgr

CVE = "CVE-2022-0847"

mgr = EntityMatchMgr()
entity = mgr.resolve_entity_id(CVE, "CyberVulnerability")

if entity.is_found:
    print(entity.content.id_)

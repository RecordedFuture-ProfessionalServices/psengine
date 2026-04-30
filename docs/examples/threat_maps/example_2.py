from psengine.threat_maps import ThreatMapMgr

mgr = ThreatMapMgr()
actors = mgr.search_threat_actor(name="Lazarus", max_results=10)

for actor in actors:
    print(actor.attributes.name)
    print(actor.attributes.alias)
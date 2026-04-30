from psengine.threat_maps import ThreatMapMgr

mgr = ThreatMapMgr()
maps = mgr.fetch_available_maps()

for map in maps:
    print(map.name)
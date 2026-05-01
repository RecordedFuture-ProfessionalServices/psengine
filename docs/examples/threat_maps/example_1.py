from psengine.threat_maps import ThreatMapMgr

mgr = ThreatMapMgr()
threat_maps = mgr.fetch_available_maps()

for threat_map in threat_maps:
    print(threat_map.name)

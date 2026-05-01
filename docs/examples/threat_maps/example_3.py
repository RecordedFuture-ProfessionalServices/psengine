from psengine.threat_maps import ThreatMapMgr

mgr = ThreatMapMgr()
malware_map = mgr.fetch_map(
    map_type='malware', categories=['0fK7b', 'RTkDB2']
)

for malware in malware_map.threat_map:
    if (
        malware.opportunity >= 65
        and malware.prevalence >= 65
    ):
        print(malware)

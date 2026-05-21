from psengine.links import LinksMgr

mgr = LinksMgr()

results = mgr.search(entities=['QCwdoU'])

for result in results.data:
    if result.error:
        print(f'Failed: {result.error.message}')
        continue

    print(f'Entity: {result.entity.name}')

    print('\nIOCs grouped by type:')
    for ioc_type, iocs in result.iocs().items():
        print(f'  {ioc_type}: {len(iocs)}')
        for ioc in iocs[:3]:
            print(
                f'    - {ioc.name} score:{ioc.risk_score}'
            )

    print('\nTTPs:')
    for ttp in result.ttps()[:5]:
        print(f'  - {ttp.name} ({ttp.display_name})')

    print('\nMalwares:')
    for malware in result.malwares()[:5]:
        print(f'  - {malware.name}')

    print('\nThreat actors:')
    for threat_actor in result.threat_actors()[:5]:
        print(f'  - {threat_actor.name}')

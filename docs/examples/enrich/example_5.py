from psengine.enrich import LookupMgr

mgr = LookupMgr()
ip = mgr.lookup('45.83.236.105', 'ip', fields=['links'])
malwares = ip.links(from_section='Actors, Tools & TTPs', entity_type='Malware')

print(', '.join(malwares))

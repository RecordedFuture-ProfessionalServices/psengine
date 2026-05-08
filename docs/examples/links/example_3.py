from psengine.links import LinksMgr

mgr = LinksMgr()

print('Sections:')
for section in mgr.list_sections():
    print(f'  {section.id_}: {section.name}')

print('\nEvent types:')
for event in mgr.list_events():
    print(f'  {event.id_}: {event.name}')

print('\nEntity types:')
for entity_type in mgr.list_entity_types():
    print(f'  {entity_type.id_}: {entity_type.name}')

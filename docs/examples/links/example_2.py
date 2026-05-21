from psengine.links import LinksMgr

mgr = LinksMgr()

results = mgr.search(
    entities=['QCwdoU'],
    sources=['technical'],
    entity_types=['type:Malware'],
    timeframe='-30d',
    search_scope='small',
    per_entity_type=50,
)

for result in results:
    if result.error:
        print(f'Failed: {result.error.message}')
        continue

    for link in result.links:
        print(f'{link.name} ({link.type_})')

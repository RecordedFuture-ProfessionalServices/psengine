from psengine.links import LinksMgr

mgr = LinksMgr()

results = mgr.search(entities=['QCwdoU'])

for result in results.data:
    if result.error:
        print(f'Failed: {result.error.message}')
        continue
    entity = result.entity
    print(f'Entity: {entity.name} ({entity.type_})')
    for link in result.links:
        print(
            f'  -> {link.name} '
            f'({link.type_}) source={link.source}'
        )

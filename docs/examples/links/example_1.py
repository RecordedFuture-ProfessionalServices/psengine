from psengine.links import LinksMgr

mgr = LinksMgr()

results = mgr.search(entities=['QCwdoU'])

for result in results:
    if result.error:
        print(f'Failed: {result.error.message}')
        continue

    entity = result.entity
    print(f'Entity: {entity.name}')

    for link in result.links[:5]:
        print(f'  -> {link.name} source:{link.source}')

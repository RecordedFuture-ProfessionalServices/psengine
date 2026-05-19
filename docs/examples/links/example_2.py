from psengine.links import (
    FilterTechnical,
    LinksFilterObjects,
    LinksLimitsObjects,
    LinksMgr,
)

mgr = LinksMgr()

filters = LinksFilterObjects(
    sources=['technical'],
    entity_types=['Malware'],
    technical=FilterTechnical(timeframe='-30d'),
)
limits = LinksLimitsObjects(
    search_scope='small', per_entity_type=50
)

results = mgr.search(
    entities=['QCwdoU'], filters=filters, limits=limits
)

for result in results.data:
    for link in result.links:
        print(f'{link.name} ({link.type_})')

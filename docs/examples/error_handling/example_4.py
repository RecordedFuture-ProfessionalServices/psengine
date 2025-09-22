from psengine.enrich import EnrichmentLookupError, LookupMgr
from pydantic import ValidationError

try:
    mgr = LookupMgr()
except ValueError as ve:
    print(
        'Possible token issue check environment variable.',
        ve,
    )
    exit(1)

entities = {
    '8.8.8.8': 'ip',
    'example.com': 'domain',
    1: 'example',
    'example2.com': 'domain',
}

for entity, entity_type in entities.items():
    try:
        enriched_data = mgr.lookup(entity, entity_type)
    except ValidationError:
        print(
            f'{entity} or {entity_type} type are wrong.',
        )
        continue
    except EnrichmentLookupError as ele:
        print(
            'Authentication issue, or some API issues.\n',
            ele,
        )
        exit(2)

    if enriched_data.is_enriched:
        print(enriched_data)

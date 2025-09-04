from psengine.enrich import LookupMgr, EnrichmentLookupError
from pydantic import ValidationError


try:
    mgr = LookupMgr()
except ValueError as ve:
    print(
        "There might be a token issue check the environment variable.\n",
        ve,
    )
    exit(1)

entities = {
    "8.8.8.8": "ip",
    "example.com": "domain",
    1: "example",
    "example2.com": "domain",
}

for entity, entity_type in entities.items():
    try:
        enriched_data = mgr.lookup(entity, entity_type)
    except ValidationError:
        print(
            f'\n\nWARNING: The entity "{entity}", or the entity_type "{entity_type}" are wrong. I will ignore it.\n\n',
        )
        continue
    except EnrichmentLookupError as ele:
        print(
            "There is an authentication issue, or some API issues.\n",
            ele,
        )
        exit(2)

    if enriched_data.is_enriched:
        print(enriched_data)

import os

from psengine.enrich import LookupMgr
from psengine.stix2 import (
    ENTITY_TYPE_MAP,
    EnrichedIndicator,
)

OUTPUT_DIR = os.path.join(os.getcwd(), "bundles")
os.makedirs(OUTPUT_DIR, exist_ok=True)
mgr = LookupMgr()

iocs = [
    ("example.com", "domain"),
    (
        "d6097e942dd0fdc1fb28ec1814780e6ecc169ec6d24f9954e71954eedbc4c70e",
        "hash",
    ),
    ("http://example.com/asd", "url"),
    ("5.35.130.255", "ip"),
]

results = [
    mgr.lookup(
        entity,
        entity_type,
        fields=["links", "riskMapping", "aiInsights"],
    )
    for entity, entity_type in iocs
]

for res in results:
    if res.is_enriched:
        enriched_indicator = EnrichedIndicator(
            name=res.entity,
            type_=ENTITY_TYPE_MAP[res.entity_type],
            evidence_details=res.content.risk.evidence_details,
            link_hits=res.content.links.hits,
            risk_mapping=res.content.risk_mapping,
            confidence=res.content.risk.score,
            ai_insights=res.content.ai_insights,
        )

        out_file = (
            OUTPUT_DIR
            / f"enriched_indicator_{res.entity_type}.json"
        )
        out_file.write_text(
            enriched_indicator.bundle.serialize()
        )

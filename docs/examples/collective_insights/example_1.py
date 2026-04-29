from datetime import UTC, datetime

from psengine.collective_insights import (
    DETECTION_SUB_TYPE_SIGMA,
    DETECTION_TYPE_RULE,
    ENTITY_HASH,
    CollectiveInsights,
)

ci = CollectiveInsights()

now = datetime.now(UTC).isoformat()

insight1 = ci.create(
    ioc_value='fbee00cb1d1ea4d7e0604436d9a36def71a9f3be804f1e2b8d117fd5d35aeabc',
    ioc_type=ENTITY_HASH,
    detection_type=DETECTION_TYPE_RULE,
    detection_sub_type=DETECTION_SUB_TYPE_SIGMA,
    detection_id='doc:o6_lui',
    detection_name='Instance of Alleged New Wiper Malware',
    ioc_field='hash',
    ioc_source_type='symantec',
    timestamp=now,
    incident_id='Incident 001',
    incident_name='Malware detected',
    incident_type='RF Sigma Rule',
    mitre_codes=['T1542', 'T1485'],
    malwares=['Aesthetic Wiper'],
)

insights = [insight1]
ci.submit(insight=insights)

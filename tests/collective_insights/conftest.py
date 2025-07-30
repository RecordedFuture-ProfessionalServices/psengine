import pytest

from psengine.collective_insights import (
    DETECTION_TYPE_RULE,
    ENTITY_HASH,
    CollectiveInsights,
    Insight,
)

TEST_HASH = 'fbee00cb1d1ea4d7e0604436d9a36def71a9f3be804f1e2b8d117fd5d35aeabc'
FORMAT_RESULT = {
    'ioc': {
        'type': 'hash',
        'value': 'fbee00cb1d1ea4d7e0604436d9a36def71a9f3be804f1e2b8d117fd5d35aeabc',
    },
    'detection': {'id': 'doc:test', 'type': 'detection_rule', 'sub_type': 'sigma'},
}


@pytest.fixture
def ci() -> CollectiveInsights:
    return CollectiveInsights()


@pytest.fixture
def insight(ci: CollectiveInsights) -> Insight:
    return ci.create(
        ioc_type=ENTITY_HASH,
        ioc_value=TEST_HASH,
        timestamp='2024-09-11 15:13:29',
        detection_type=DETECTION_TYPE_RULE,
        detection_id='doc:test',
        detection_sub_type='sigma',
    )

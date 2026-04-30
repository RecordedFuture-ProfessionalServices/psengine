from pathlib import Path

import pytest

from psengine.threat_maps import ThreatMapMgr

MOCK_DIR = Path(__file__).parent / 'mocks'


@pytest.fixture
def threat_map_mgr():
    return ThreatMapMgr()

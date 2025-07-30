from pathlib import Path

import pytest

from psengine.classic_alerts import ClassicAlertMgr

MOCK_DIR = Path(__file__).parent / 'mocks'


@pytest.fixture
def ca_mgr():
    return ClassicAlertMgr()

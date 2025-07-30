from pathlib import Path

import pytest

from psengine.risklists import RisklistMgr

MOCK_DIR = Path(__file__).parent / 'mocks'


@pytest.fixture
def risklist_mgr():
    return RisklistMgr()

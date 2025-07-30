from pathlib import Path

import pytest

from psengine.detection import DetectionMgr

MOCK_DIR = Path(__file__).parent / 'mocks'


@pytest.fixture
def detection_mgr():
    return DetectionMgr()

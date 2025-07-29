from pathlib import Path

import pytest

from psengine.identity import IdentityMgr


@pytest.fixture
def identity_mgr():
    return IdentityMgr()


MOCK_DIR = Path(__file__).parent / 'mocks'

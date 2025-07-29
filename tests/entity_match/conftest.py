import pytest

from psengine.entity_match.entity_match_mgr import EntityMatchMgr


@pytest.fixture
def match_mgr():
    return EntityMatchMgr()

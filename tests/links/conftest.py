import pytest

from psengine.links import LinksMgr


@pytest.fixture
def links_mgr():
    return LinksMgr()

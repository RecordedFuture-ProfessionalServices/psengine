import pytest

from psengine.fusion.fusion_mgr import FusionMgr


@pytest.fixture
def fusion_mgr():
    return FusionMgr()

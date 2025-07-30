import pytest

from psengine.enrich import LookupMgr, SoarMgr


@pytest.fixture
def lookup_mgr():
    return LookupMgr()


@pytest.fixture
def soar_mgr():
    return SoarMgr()

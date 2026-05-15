import pytest

from psengine.sandbox import SandboxMgr


@pytest.fixture
def sandbox_mgr():
    return SandboxMgr(sandbox_choice='eu')

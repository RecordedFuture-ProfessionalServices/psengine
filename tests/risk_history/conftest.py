import pytest
from psengine.risk_history.risk_history_mgr import RiskHistoryMgr


@pytest.fixture
def riskhistory_mgr():
    return RiskHistoryMgr()

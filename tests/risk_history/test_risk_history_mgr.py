from datetime import datetime
from pathlib import Path

from psengine.risk_history.models import RiskHistory
from psengine.risk_history.risk_history_mgr import RiskHistoryMgr

MOCK_DIR = Path(__file__).parent / 'mocks'


class Test_RiskHistoryMgr:
    def test_get_risk_history_one_entity(
        self, riskhistory_mgr: RiskHistoryMgr, mocker, mock_request
    ):
        mock_file = MOCK_DIR / 'sudo.json'
        mock = mock_request(mock_file)
        mocked_request = mocker.patch.object(
            riskhistory_mgr.rf_client, 'request', return_value=mock
        )

        reports = riskhistory_mgr.search(
            entities='gVd1R',
            from_='-20d',
            to='-1d',
        )

        assert all(isinstance(r, RiskHistory) for r in reports)
        assert mocked_request.call_args[0] == (
            'post',
            'https://api.recordedfuture.com/risk/history',
        )
        assert mocked_request.call_args[1]['data']['entities'] == ['gVd1R']
        assert datetime.fromisoformat(mocked_request.call_args[1]['data']['from'])
        assert datetime.fromisoformat(mocked_request.call_args[1]['data']['to'])

    def test_get_risk_history_multiple_entities(
        self, riskhistory_mgr: RiskHistoryMgr, mocker, mock_request
    ):
        mock_file = MOCK_DIR / 'redhat_and_sudo.json'
        mock = mock_request(mock_file)
        mocked_request = mocker.patch.object(
            riskhistory_mgr.rf_client, 'request', return_value=mock
        )

        reports = riskhistory_mgr.search(entities=['gVd1R', 'EJXkx'])

        assert all(isinstance(r, RiskHistory) for r in reports)
        assert mocked_request.call_args[0] == (
            'post',
            'https://api.recordedfuture.com/risk/history',
        )
        assert mocked_request.call_args[1]['data'] == {'entities': ['gVd1R', 'EJXkx']}
        assert all(report.entity.name in ('Sudo', 'Red Hat Enterprise Linux') for report in reports)
        assert (
            str(reports[0])
            == 'Entity Red Hat Enterprise Linux: Risk Score Changes: 6, Risk Rule Changes: 184'
        )
        assert str(reports[1]) == 'Entity Sudo: Risk Score Changes: 5, Risk Rule Changes: 67'

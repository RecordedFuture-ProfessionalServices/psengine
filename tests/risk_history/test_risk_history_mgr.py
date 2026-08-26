from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from tests.conftest import validation_match

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

    def test_risk_history_validation_error_names_entity(
        self, riskhistory_mgr: RiskHistoryMgr, mocker, make_response
    ):
        good = {
            'entity': {'id': 'gVd1R', 'provided_id': 'gVd1R', 'type': 'Product', 'name': 'Sudo'},
            'scores': [],
            'levels': [],
            'risk_rules': [],
        }
        bad = {
            'entity': {'id': 'broken-id', 'provided_id': 'broken-id', 'type': 42, 'name': 'Nope'},
            'scores': [],
            'levels': [],
            'risk_rules': [],
        }
        mocker.patch.object(
            riskhistory_mgr.rf_client, 'request', return_value=make_response({'data': [good, bad]})
        )
        with pytest.raises(ValidationError, match=validation_match('entity.id=broken-id', 'string_type')):
            riskhistory_mgr.search(entities='gVd1R')

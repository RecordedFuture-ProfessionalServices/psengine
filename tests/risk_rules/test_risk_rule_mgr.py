import json

import pytest
from pydantic import ValidationError
from requests import ConnectionError, ConnectTimeout, HTTPError, ReadTimeout  # noqa: A004
from requests.models import Response

from psengine.endpoints import EP_RISK_RULES
from psengine.risk_rules import RiskRule, RiskRuleEntityType, RiskRuleFetchError, RiskRuleMgr
from tests.risk_rules.constants import MOCK_DIR

ENTITY_TYPES = ['ip', 'domain', 'hash', 'vulnerability', 'url']


@pytest.fixture
def rr_mgr():
    return RiskRuleMgr()


class Test_RiskRuleMgr:
    @pytest.mark.parametrize('entity_type', ENTITY_TYPES)
    def test_fetch_risk_rule_ok(self, rr_mgr: RiskRuleMgr, entity_type: str, mock_request, mocker):
        mock_file = MOCK_DIR / f'riskrules_{entity_type}.json'
        mock = mock_request(mock_file)
        spy = mocker.patch.object(rr_mgr.rf_client, 'request', return_value=mock)

        rules = rr_mgr.fetch(RiskRuleEntityType(entity_type))

        expected_count = len(json.loads(mock_file.read_text())['data']['results'])
        assert isinstance(rules, list)
        assert len(rules) == expected_count
        assert all(isinstance(r, RiskRule) for r in rules)
        assert spy.call_args.args == ('get', EP_RISK_RULES.format(entity_type))

    def test_fetch_risk_rule_accepts_enum_or_str(self, rr_mgr: RiskRuleMgr, mock_request, mocker):
        mock = mock_request(MOCK_DIR / 'riskrules_ip.json')
        mocker.patch.object(rr_mgr.rf_client, 'request', return_value=mock)
        rr_mgr.fetch(RiskRuleEntityType.IP)
        rr_mgr.fetch('ip')

    def test_fetch_risk_rule_invalid_entity_type(self, rr_mgr: RiskRuleMgr):
        with pytest.raises(ValidationError):
            rr_mgr.fetch('not-a-type')

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_fetch_risk_rule_raises_RiskRuleFetchError(
        self, rr_mgr: RiskRuleMgr, exception, mocker
    ):
        response = Response()
        response.status_code = 500
        excp_obj = exception('Error')
        excp_obj.response = response
        mocker.patch.object(rr_mgr.rf_client, 'request', side_effect=excp_obj)
        with pytest.raises(RiskRuleFetchError):
            rr_mgr.fetch(RiskRuleEntityType.IP)

    def test_fetch_risk_rule_unwraps_data_results(self, rr_mgr: RiskRuleMgr, make_response, mocker):
        payload = {
            'data': {
                'results': [
                    {
                        'name': 'sampleRule',
                        'description': 'A sample',
                        'criticality': 3,
                        'criticalityLabel': 'Malicious',
                        'count': 42,
                        'categories': [],
                        'relatedEntities': [],
                    }
                ]
            }
        }
        mocker.patch.object(rr_mgr.rf_client, 'request', return_value=make_response(payload))
        rules = rr_mgr.fetch(RiskRuleEntityType.IP)
        assert len(rules) == 1
        assert rules[0].name == 'sampleRule'
        assert rules[0].criticality == 3

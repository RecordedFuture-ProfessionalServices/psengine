import re
from typing import Optional

import pytest
from pydantic import BaseModel

from psengine.risklists.models import DefaultRiskList
from tests.risklists.conftest import MOCK_DIR


class Test_RFRiskListMgr:
    @pytest.mark.parametrize('entity_type', ['domain', 'ip', 'hash', 'url', 'vulnerability'])
    def test_default_risklist(self, risklist_mgr, entity_type, mocker, make_csv_response, request):
        node_id = request.node.callspec.id
        mocks = make_csv_response(
            MOCK_DIR / f'test_default_risklist[{re.escape(node_id)}]_0.csv', gzip_compress=False
        )
        mocker.patch.object(risklist_mgr.rf_client, 'request', return_value=mocks)

        data = risklist_mgr.fetch_risklist('default', entity_type, validate=DefaultRiskList)
        assert all(isinstance(d, DefaultRiskList) for d in data)

    def test_stix_risklist(self, risklist_mgr, mocker, make_csv_response):
        mocks = make_csv_response(MOCK_DIR / 'test_stix_risklist_0.csv', gzip_compress=False)
        mocker.patch.object(risklist_mgr.rf_client, 'request', return_value=mocks)

        data = risklist_mgr.fetch_risklist('analystNote', 'hash', 'xml/stix/1.2')
        assert all(isinstance(d, dict) for d in data)

    def test_default_risklist_empty(self, risklist_mgr, mocker, make_csv_response):
        mocks = make_csv_response(
            MOCK_DIR / 'test_default_risklist_empty_0.csv', gzip_compress=False
        )
        mocker.patch.object(risklist_mgr.rf_client, 'request', return_value=mocks)
        data = risklist_mgr.fetch_risklist('recentValidatedCnc', 'ip')
        assert list(data) == []

    def test_default_risklist_empty_without_validate(self, risklist_mgr, mocker, make_csv_response):
        mocks = make_csv_response(
            MOCK_DIR / 'test_default_risklist_empty_without_validate_0.csv', gzip_compress=False
        )
        mocker.patch.object(risklist_mgr.rf_client, 'request', return_value=mocks)

        data = risklist_mgr.fetch_risklist('recentValidatedCnc', 'ip')
        assert list(data) == []

    def test_fusion_file_csv(self, risklist_mgr, mocker, make_csv_response):
        mocks = make_csv_response(MOCK_DIR / 'test_fusion_file_csv_0.csv', gzip_compress=False)
        mocker.patch.object(risklist_mgr.rf_client, 'request', return_value=mocks)
        headers_name = [
            'IP',
            'Risk',
            'RiskString',
            'TriggeredRules',
            'ASN',
            'Organization',
            'Country',
            'IntelCardURL',
        ]

        data = risklist_mgr.fetch_risklist('/home/ipReputationCheckOutput.csv', headers=True)
        first_item = next(data)
        assert all(x in headers_name for x in first_item)
        assert first_item == {
            'IP': '8.8.8.8',
            'Risk': '0',
            'RiskString': '0/64',
            'TriggeredRules': '',
            'ASN': 'ASN1111',
            'Organization': '',
            'Country': 'United States',
            'IntelCardURL': 'https://app.recordedfuture.com/live/sc/entity/ip%3A8.8.8.8',
        }

    def test_fusion_file_json_validate(self, risklist_mgr, mocker, mock_request):
        mocks = mock_request(MOCK_DIR / 'test_fusion_file_json_validate_0.json')
        mocker.patch.object(risklist_mgr.rf_client, 'request', return_value=mocks)

        class JsonFusionModel(BaseModel):
            TorNode: Optional[str] = None
            Risk: Optional[str] = None
            TorFlags: Optional[str] = None
            Name: Optional[str] = None

        data = risklist_mgr.fetch_risklist('/home/moise_ip_tors.json', validate=JsonFusionModel)
        assert next(data) == JsonFusionModel(
            TorNode=None, Risk='8', TorFlags='ABC', Name='136.33.11.117'
        )

        assert all(isinstance(d, JsonFusionModel) for d in data)

    def test_fusion_file_json_without_validate(self, risklist_mgr, mocker, mock_request):
        mocks = mock_request(MOCK_DIR / 'test_fusion_file_json_without_validate_0.json')
        mocker.patch.object(risklist_mgr.rf_client, 'request', return_value=mocks)

        data = risklist_mgr.fetch_risklist('/home/moise_ip_tors.json', validate=None)
        assert next(data) == {
            'Name': '21.183.3.170',
            'Risk': '8',
            'TorFlags': 'ABC',
            'TorName': None,
        }

    def test_fetch_risklist_raises_ValueError_not_pydantic_model(self, risklist_mgr):
        class MyModel:
            x: int

        with pytest.raises(
            ValueError, match='`validate` should be a subclass of Pydantic BaseModel or None'
        ):
            list(risklist_mgr.fetch_risklist('default', 'ip', validate=MyModel))

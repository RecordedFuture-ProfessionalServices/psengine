import re
from pathlib import Path

import pytest

from psengine.detection import DetectionMgr, DetectionRule, DetectionRuleSearchOut
from psengine.detection.helpers import save_rule
from tests.detection.conftest import MOCK_DIR


class Test_DetectionRule_Models:
    @pytest.mark.parametrize(
        'rule_type',
        ['sigma', 'yara', 'snort'],
    )
    def test_validate_detection_rule(
        self, detection_mgr: DetectionMgr, rule_type: str, mocker, mock_request
    ):
        pattern = re.compile(rf'^test_validate_detection_rule\[{rule_type}]_\d+\.json$')
        files = [f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name)]
        mocks = [mock_request(MOCK_DIR / f) for f in files]
        mocker.patch.object(detection_mgr.rf_client, 'request', side_effect=mocks)

        rules = detection_mgr.search(max_results=1000, detection_rule=rule_type)
        [DetectionRule.model_validate(rule) for rule in rules]

    query = [
        {
            'filter': {
                'types': ['yara'],
                'entities': ['mitre:T1486', 'kK5UbE'],
                'created': {
                    'after': '2022-02-10T12:00:00.000Z',
                    'before': '2022-03-10T00:00:00.000Z',
                },
                'doc_id': 'doc:lmRPGB',
                'title': 'Ransomware',
            }
        },
        {'tagged_entities': False},
        {
            'filter': {
                'types': ['yara'],
                'entities': ['mitre:T1486', 'kK5UbE'],
                'created': {
                    'after': '2022-02-10T12:00:00.000Z',
                    'before': '2022-03-10T00:00:00.000Z',
                },
                'doc_id': 'doc:lmRPGB',
                'title': 'Ransomware',
            },
            'tagged_entities': False,
            'limit': 10,
            'offset': '87dstyghnbsfg78546',
        },
        {'limit': 10, 'offset': '87dstyghnbsfg78546'},
        {
            'filter': {
                'types': ['yara'],
                'created': {
                    'before': '2022-03-10T00:00:00.000Z',
                },
                'title': 'Ransomware',
            }
        },
    ]

    @pytest.mark.parametrize('query', query)
    def test_validate_detection_rule_search(self, query):
        DetectionRuleSearchOut.model_validate(query)

    def test_no_file_name(self, detection_mgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'test_no_file_name.json')

        mocker.patch.object(detection_mgr.rf_client, 'request', return_value=mock)
        data = detection_mgr.fetch('doc:fYqe4x')
        DetectionRule.model_validate(data)

    def test_hash(self, detection_mgr: DetectionMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_hash_0.json'),
            mock_request(MOCK_DIR / 'test_hash_1.json'),
            mock_request(MOCK_DIR / 'test_hash_2.json'),
            mock_request(MOCK_DIR / 'test_hash_3.json'),
        ]

        mocker.patch.object(detection_mgr.rf_client, 'request', side_effect=mocks)

        rule1 = detection_mgr.fetch(doc_id='doc:lmRPGB')
        rule2 = detection_mgr.fetch(doc_id='doc:fYqe4x')
        rule1 = DetectionRule.model_validate(rule1)
        rule1_twin = DetectionRule.model_validate(rule1)
        rule2 = DetectionRule.model_validate(rule2)
        rule2_twin = DetectionRule.model_validate(rule2)
        rules = [rule1, rule2, rule1_twin, rule2_twin]

        assert rule1 == rule1_twin
        assert rule2 == rule2_twin
        assert rule1 != rule2
        assert hash(rule1) == hash(rule1_twin)
        assert set(rules) == {rule1, rule2}

    def test_ordering(self, detection_mgr: DetectionMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_ordering_0.json'),
            mock_request(MOCK_DIR / 'test_ordering_1.json'),
            mock_request(MOCK_DIR / 'test_ordering_2.json'),
            mock_request(MOCK_DIR / 'test_ordering_3.json'),
            mock_request(MOCK_DIR / 'test_ordering_4.json'),
            mock_request(MOCK_DIR / 'test_ordering_5.json'),
        ]

        mocker.patch.object(detection_mgr.rf_client, 'request', side_effect=mocks)

        rule1 = detection_mgr.fetch(doc_id='doc:lmRPGB')  # 2023-09-02T17:23:22.108Z
        rule2 = detection_mgr.fetch(doc_id='doc:ui5Ke3')  # 2024-02-16T19:03:01.907Z
        rule3 = detection_mgr.fetch(doc_id='doc:cynQie')  # 2022-03-25T18:00:30.553Z

        rules = [rule1, rule2, rule3]
        assert sorted(rules) == [rule2, rule3, rule1]
        assert rule2 < rule1
        assert rule1 >= rule3
        assert rule1 <= rule1
        assert rule1 != rule2

    def test_save_file_without_filename(
        self, detection_mgr: DetectionMgr, tmp_path, mocker, mock_request
    ):
        mock = mock_request(MOCK_DIR / 'test_save_file_without_filename.json')
        mocker.patch.object(detection_mgr.rf_client, 'request', return_value=mock)

        rule = detection_mgr.fetch(doc_id='doc:6DWzsX')
        save_rule(rule, tmp_path)
        assert (tmp_path / 'doc_6DWzsX_0').exists()

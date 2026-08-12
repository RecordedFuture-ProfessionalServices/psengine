from copy import deepcopy

import pytest
from pydantic import ValidationError

from psengine.collective_insights import (
    Insight,
    InsightsOut,
    SearchEntry,
)
from psengine.collective_insights.models import RequestDetection, RequestIOC

REQUEST_DETECTION_OK = [
    {'name': 'moise', 'type': 'correlation'},
    {'id': 'abc', 'name': 'pytest_detection', 'type': 'detection_rule', 'sub_type': 'sigma'},
    {'id': 'abc', 'name': 'pytest_detection', 'type': 'detection_rule', 'sub_type': 'snort'},
    {'id': 'abc', 'name': 'pytest_detection', 'type': 'detection_rule', 'sub_type': 'yara'},
    {'name': 'moise', 'type': 'correlation', 'id': 'abc'},
]

REQUEST_DETECTION_NOT_OK = [
    {'name': 'pytest_detection', 'type': 'detection_rule'},
    {'id': 'abc', 'name': 'pytest_detection', 'type': 'detection_rule'},
    {'id': 'abc', 'name': 'pytest_detection', 'type': 'detection_rule', 'sub_type': 'wrong'},
    {'id': 'abc', 'name': 'pytest_detection'},
]

REAL_PAYLOAD = {
    'data': [
        {
            'timestamp': '2023-01-01T10:00:00Z',
            'ioc': {
                'type': 'ip',
                'value': '1.2.3.4',
                'field': 'dstip',
                'source_type': 'netscreen:firewall',
            },
            'incident': {
                'id': '28548e09-63e8-4f8b-abd4-be86207b1583',
                'name': 'Triggered Detection Rule',
                'type': 'splunk-detection-rule',
            },
            'mitre_codes': ['T1055'],
            'malwares': ['Stuxnet'],
            'detection': {
                'id': 'doc:XYZA',
                'name': 'string',
                'type': 'detection_rule',
                'sub_type': 'sigma',
            },
        }
    ],
}


class Test_CollectiveInsight_Models:
    @pytest.mark.parametrize('data', REQUEST_DETECTION_OK)
    def test_validate_request_detection_model_ok(self, data):
        RequestDetection.model_validate(data)

    @pytest.mark.parametrize('data', REQUEST_DETECTION_NOT_OK)
    def test_validate_request_detection_model_fail(self, data):
        with pytest.raises(ValidationError):
            RequestDetection.model_validate(data)

    @pytest.mark.parametrize('values', [(True, False), (True, True), (False, False), (False, True)])
    def test_request(self, values):
        REAL_PAYLOAD['options'] = {'debug': values[0], 'summary': values[1]}
        InsightsOut.model_validate(REAL_PAYLOAD)

    def test_hash(self):
        insight1 = Insight(
            ioc=RequestIOC(type='ip', value='8.8.8.8'),
            timestamp='2023-01-01T10:00:00Z',
            detection=RequestDetection(type='correlation'),
        )
        insight1 = Insight.model_validate(insight1)

        insight2 = Insight(
            ioc=RequestIOC(type='domain', value='google.com'),
            timestamp='2023-01-02T10:00:00Z',
            detection=RequestDetection(type='correlation'),
        )
        insight2 = Insight.model_validate(insight2)

        insight1_twin = Insight.model_validate(insight1)
        insight2_twin = Insight.model_validate(insight2)

        insights = [insight1, insight2, insight1_twin, insight2_twin]

        assert insight1 == insight1_twin
        assert insight2 == insight2_twin

        assert insight1 != insight2

        assert hash(insight1) == hash(insight1_twin)
        assert set(insights) == {insight1, insight2}

    def test_ordering(self):
        base = {
            'ioc': {'type': 'ip', 'value': '8.8.8.8'},
            'detection': {'type': 'correlation'},
            'timestamp': '2023-01-01T10:00:00Z',
        }

        insight = deepcopy(base)
        insight['timestamp'] = '2023-09-01T13:31:56.878Z'
        insight1 = Insight.model_validate(insight)

        insight = deepcopy(base)
        insight['timestamp'] = '2022-11-23T13:31:56.878Z'
        insight2 = Insight.model_validate(insight)

        insight = deepcopy(base)
        insight['timestamp'] = '2024-11-10T13:31:56.878Z'
        insight3 = Insight.model_validate(insight)

        insight = deepcopy(base)
        insight['timestamp'] = '2025-11-01T13:31:56.878Z'
        insight['ioc']['value'] = '9.9.9.9'
        insight4 = Insight.model_validate(insight)

        insight = deepcopy(base)
        insight['timestamp'] = '2025-12-03T13:31:56.878Z'
        insight['ioc']['value'] = '10.10.10.10'
        insight5 = Insight.model_validate(insight)

        notes = [insight1, insight2, insight3, insight4, insight5]
        assert sorted(notes) == [insight2, insight1, insight3, insight4, insight5]
        assert insight2 < insight1
        assert insight1 <= insight3
        assert insight1 <= insight1
        assert insight1 != insight2

    def test_search_entry_str(self):
        entry = SearchEntry.model_validate(
            {
                'id': 'abc',
                'detection_time': '2025-12-15T13:05:23Z',
                'detection_type': 'sandbox',
                'indicator': {'type': 'ip', 'value': '1.2.3.4'},
            },
        )
        assert str(entry) == (
            'Event ID: abc, IOC: 1.2.3.4, Detection Time: 2025-12-15 13:05:23, '
            'Detection Type: sandbox'
        )

    def test_search_entry_str_defaults_when_fields_missing(self):
        entry = SearchEntry.model_validate({'id': 'abc'})
        assert str(entry) == (
            'Event ID: abc, IOC: N/A, Detection Time: N/A, Detection Type: N/A'
        )

    def test_search_entry_hash_and_equality(self):
        payload = {
            'id': 'abc',
            'detection_time': '2025-12-15T13:05:23Z',
            'indicator': {'type': 'ip', 'value': '1.2.3.4'},
        }
        e1 = SearchEntry.model_validate(payload)
        e1_twin = SearchEntry.model_validate(payload)
        e2 = SearchEntry.model_validate(
            {
                'id': 'def',
                'detection_time': '2025-12-16T13:05:23Z',
                'indicator': {'type': 'domain', 'value': 'evil.com'},
            },
        )
        assert e1 == e1_twin
        assert e1 != e2
        assert hash(e1) == hash(e1_twin)
        assert {e1, e1_twin, e2} == {e1, e2}

    def test_search_entry_ordering(self):
        e1 = SearchEntry.model_validate(
            {'id': 'a', 'detection_time': '2025-09-01T13:31:56Z'},
        )
        e2 = SearchEntry.model_validate(
            {'id': 'b', 'detection_time': '2022-11-23T13:31:56Z'},
        )
        e3 = SearchEntry.model_validate(
            {'id': 'c', 'detection_time': '2024-11-10T13:31:56Z'},
        )
        e4 = SearchEntry.model_validate(
            {'id': 'a', 'detection_time': '2025-11-01T13:31:56Z'},
        )
        e5 = SearchEntry.model_validate(
            {'id': 'z', 'detection_time': '2025-11-01T13:31:56Z'},
        )

        assert sorted([e1, e2, e3, e4, e5]) == [e2, e3, e1, e4, e5]
        assert e2 < e1
        assert e1 <= e4
        assert e1 <= e1
        assert e1 != e2

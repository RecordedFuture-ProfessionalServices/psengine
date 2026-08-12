import pytest
from pydantic import ValidationError
from requests import ConnectionError, ConnectTimeout, HTTPError, ReadTimeout, Response  # noqa: A004

from psengine.collective_insights import (
    CollectiveInsights,
    CollectiveInsightsError,
    CollectiveInsightsSearchError,
    Insight,
    InsightsIn,
    SearchEntry,
)


class Test_CollectiveInsights:
    @pytest.mark.parametrize('bad_insight', [1, 'insight', None])
    def test_submit_raises_ValidationError(self, bad_insight, ci: CollectiveInsights):
        with pytest.raises(ValidationError):
            ci.submit(insight=bad_insight)

    def test_submit_raises_ValueError(self, ci: CollectiveInsights):
        with pytest.raises(ValueError, match='Insight cannot be empty'):
            ci.submit(insight=[])

    def test_submit_insight_list(
        self, insight: Insight, ci: CollectiveInsights, mocker, make_response
    ):
        data = {
            'result': {
                'status': 'OK',
                'debug': True,
                'summary': {
                    'processed': {
                        'ip': 0,
                        'domain': 0,
                        'hash': 1,
                        'vulnerability': 0,
                        'url': 0,
                    },
                },
            },
        }
        side_effect = [
            make_response(data),
            make_response(data),
            make_response(data),
            make_response(data),
        ]
        mocker.patch.object(ci.rf_client, 'request', side_effect=side_effect)
        spy = mocker.spy(ci.rf_client, 'request')

        for rfins in (insight, [insight], [insight, insight]):
            data = ci.submit(insight=rfins)
            assert isinstance(data, InsightsIn)
            assert spy.call_args[0][0] == 'post'
            assert isinstance(spy.call_args[1]['data']['data'], list)

    @pytest.mark.parametrize(
        'exc',
        [
            ConnectionError('Connection Error'),
            ConnectTimeout('Connection Timed Out'),
            ReadTimeout('Read Timed Out'),
            HTTPError('HTTP Error'),
        ],
    )
    def test_submit_raise_CollectiveInsightsError(
        self,
        mocker,
        exc,
        insight: Insight,
        ci: CollectiveInsights,
    ):
        mocker.patch.object(ci.rf_client, 'request', side_effect=exc)
        with pytest.raises(CollectiveInsightsError):
            ci.submit(insight)

    def test_submit_raise_CollectiveInsightsError_2(
        self,
        mocker,
        insight: Insight,
        ci: CollectiveInsights,
    ):
        mocker.patch.object(
            ci.rf_client,
            'request',
            side_effect=HTTPError('error!'),
        )
        with pytest.raises(CollectiveInsightsError):
            ci.submit(insight)

    @pytest.mark.parametrize('value', [['uhash:1234'], None, ['a', 'b']], ids=str)
    def test_prepare_ci_request_organization_ids(
        self,
        value,
        insight: Insight,
        ci: CollectiveInsights,
    ):
        ci_data = ci._prepare_ci_request(
            [insight],
            True,
            organization_ids=value,
        )
        assert ci_data.organization_ids == value
        assert ci_data.options.summary

    def test_prepare_ci_request_organization_ids_is_None(
        self,
        insight: Insight,
        ci: CollectiveInsights,
    ):
        ci_data = ci._prepare_ci_request(
            [insight],
            True,
            organization_ids=None,
        )
        assert ci_data.organization_ids is None
        assert ci_data.options.summary

    def test_prepare_ci_request_organization_ids_raises_ValidationError(
        self,
        insight: Insight,
        ci: CollectiveInsights,
    ):
        with pytest.raises(ValidationError):
            ci._prepare_ci_request(
                [insight],
                organization_ids='invalid_org_ids',
            )

    @pytest.mark.parametrize('debug', [False, True])
    def test_prepare_params_for_submission_debug(
        self,
        debug,
        insight: Insight,
        ci: CollectiveInsights,
    ):
        ci_data = ci._prepare_ci_request([insight], debug=debug)
        assert ci_data.options.debug == debug
        assert ci_data.options.summary

    def test_prepare_params_for_submission_insight_list(
        self,
        insight: Insight,
        ci: CollectiveInsights,
    ):
        for rfins in ([insight], [insight, insight]):
            ci_data = ci._prepare_ci_request(insight=rfins)
            data = ci_data.data
            assert isinstance(data, list)

    def test_create(self, ci: CollectiveInsights):
        insight = ci.create(
            ioc_type='hash',
            ioc_value='fbee00cb1d1ea4d7e0604436d9a36def71a9f3be804f1e2b8d117fd5d35aeabc',
            detection_type='detection_rule',
            detection_id='doc:test',
            detection_sub_type='sigma',
            timestamp='2023-01-01T10:00:00Z',
            malwares='Cobalt Strike',
        )
        assert insight.ioc.type_.value == 'hash'
        assert (
            insight.ioc.value == 'fbee00cb1d1ea4d7e0604436d9a36def71a9f3be804f1e2b8d117fd5d35aeabc'
        )
        assert insight.detection.type_.value == 'detection_rule'
        assert insight.detection.id_ == 'doc:test'
        assert insight.detection.sub_type.value == 'sigma'

    @pytest.mark.parametrize('malware', ['Cobalt', ['Cobalt', 'Loki'], ['Cobalt'], None])
    def test_create_malware_validator(self, ci: CollectiveInsights, malware):
        insight = ci.create(
            ioc_type='hash',
            ioc_value='fbee00cb1d1ea4d7e0604436d9a36def71a9f3be804f1e2b8d117fd5d35aeabc',
            detection_type='detection_rule',
            detection_id='doc:test',
            detection_sub_type='sigma',
            timestamp='2023-01-01T10:00:00Z',
            malwares=malware,
        )
        expected = (malware if isinstance(malware, list) else [malware]) if malware else None
        assert insight.malwares == expected

    @pytest.mark.parametrize('mitre_codes', ['T123', ['T123', 'T124'], ['T123'], None])
    def test_create_mitre_codes_validator(self, ci: CollectiveInsights, mitre_codes):
        insight = ci.create(
            ioc_type='hash',
            ioc_value='fbee00cb1d1ea4d7e0604436d9a36def71a9f3be804f1e2b8d117fd5d35aeabc',
            detection_type='detection_rule',
            detection_id='doc:test',
            detection_sub_type='sigma',
            timestamp='2023-01-01T10:00:00Z',
            mitre_codes=mitre_codes,
        )
        expected = (
            (mitre_codes if isinstance(mitre_codes, list) else [mitre_codes])
            if mitre_codes
            else None
        )
        assert insight.mitre_codes == expected

    def test_submit_raises_ValidationError_on_bad_response(
        self, insight: Insight, ci: CollectiveInsights, mocker
    ):
        r = Response()
        r._content = b'{"bad": "response"}'
        r.status_code = 200
        mocker.patch.object(ci.rf_client, 'request', return_value=r)
        with pytest.raises(ValidationError):
            ci.submit(insight)


SEARCH_ENTRY_SAMPLE = {
    'id': '16046941d44a85e4748a9e9a',
    'organizations': ['uhash:4uwFvB7QsB'],
    'submission_method': 'api',
    'detection_type': 'sandbox',
    'detection_time': '2025-12-15T13:05:23Z',
    'indicator': {'type': 'ip', 'value': '1.2.3.4', 'risk': {'score': {'at_detection': 75}}},
    'associated_threats': {
        'malware': [{'id': 'lStsKc', 'type': 'Malware', 'name': 'WhisperGate'}],
    },
}


class Test_CollectiveInsightsSearch:
    def test_search_returns_search_entries(
        self, ci: CollectiveInsights, mocker,
    ):
        mocker.patch.object(
            ci.rf_client, 'request_paged', return_value=[SEARCH_ENTRY_SAMPLE],
        )
        results = ci.search(indicator_type='ip')
        assert len(results) == 1
        assert isinstance(results[0], SearchEntry)
        assert results[0].id_ == '16046941d44a85e4748a9e9a'
        assert results[0].indicator.value == '1.2.3.4'
        assert results[0].indicator.risk.score.at_detection == 75
        assert results[0].associated_threats.malware[0].name == 'WhisperGate'

    def test_search_returns_empty_when_no_matches(
        self, ci: CollectiveInsights, mocker,
    ):
        mocker.patch.object(ci.rf_client, 'request_paged', return_value=[])
        assert ci.search(indicator_type='ip') == []

    def test_search_builds_full_nested_payload(self, ci: CollectiveInsights, mocker):
        spy = mocker.patch.object(ci.rf_client, 'request_paged', return_value=[])
        ci.search(
            indicator_type='ip',
            submission_method=['api', 'integration'],
            organizations='uhash:4uwFvB7QsB',
            detection_rule_id=['15zvq', 'w89Y0'],
            detection_type='sandbox',
            detection_time_from='2025-10-24T12:00:01Z',
            detection_time_to='2025-10-25T12:00:01Z',
            malware_id='present',
            mitre_code_id=['mitre:T1059.013'],
            threat_actor_id='absent',
            atop_use_case='present',
            atop_profile_id=['d290f1ee-6c54-4b01-90e6-d701748f0851'],
            atop_job_id='present',
            integration_type_id=['ho3spe'],
            indicator_risk_score={'gte': 50, 'lt': 90},
            max_results=5,
            page_size=100,
        )
        payload = spy.call_args.kwargs['data']
        assert payload['limit'] == 5
        filters = payload['filters']
        assert filters['indicator_type'] == ['ip']
        assert filters['submission_method'] == ['api', 'integration']
        assert filters['organizations'] == ['uhash:4uwFvB7QsB']
        assert filters['detection_rule'] == {'id': ['15zvq', 'w89Y0']}
        assert filters['detection_type'] == ['sandbox']
        assert filters['detection_time'] == {
            'from': '2025-10-24T12:00:01Z',
            'to': '2025-10-25T12:00:01Z',
        }
        assert filters['associated_threats'] == {
            'malware': {'id': 'present'},
            'mitre_code': {'id': ['mitre:T1059.013']},
            'threat_actor': {'id': 'absent'},
        }
        assert filters['autonomous_threat_operations'] == {
            'use_case': 'present',
            'profile': {'id': ['d290f1ee-6c54-4b01-90e6-d701748f0851']},
            'job': {'id': 'present'},
        }
        assert filters['integration_type'] == {'id': ['ho3spe']}
        assert filters['indicator'] == {'risk': {'score': {'at_detection': {'gte': 50, 'lt': 90}}}}

    @pytest.mark.parametrize(
        ('supplied', 'expected'),
        [
            ('4uwFvB7QsB', ['uhash:4uwFvB7QsB']),
            ('uhash:4uwFvB7QsB', ['uhash:4uwFvB7QsB']),
            (['4uwFvB7QsB', 'uhash:XYZ1234567'], ['uhash:4uwFvB7QsB', 'uhash:XYZ1234567']),
        ],
    )
    def test_search_organizations_uhash_normalized(
        self, ci: CollectiveInsights, mocker, supplied, expected,
    ):
        spy = mocker.patch.object(ci.rf_client, 'request_paged', return_value=[])
        ci.search(organizations=supplied)
        assert spy.call_args.kwargs['data']['filters']['organizations'] == expected

    def test_search_omits_unset_filters(self, ci: CollectiveInsights, mocker):
        spy = mocker.patch.object(ci.rf_client, 'request_paged', return_value=[])
        ci.search(indicator_type='ip')
        payload = spy.call_args.kwargs['data']
        assert payload['filters'] == {'indicator_type': ['ip']}

    def test_search_no_filters_sends_empty_body(self, ci: CollectiveInsights, mocker):
        spy = mocker.patch.object(ci.rf_client, 'request_paged', return_value=[])
        ci.search()
        payload = spy.call_args.kwargs['data']
        assert 'filters' not in payload

    @pytest.mark.parametrize(
        'presence_value', ['present', 'absent'],
    )
    def test_search_presence_string_passthrough(
        self, ci: CollectiveInsights, mocker, presence_value,
    ):
        spy = mocker.patch.object(ci.rf_client, 'request_paged', return_value=[])
        ci.search(indicator_type=presence_value, malware_id=presence_value)
        filters = spy.call_args.kwargs['data']['filters']
        assert filters['indicator_type'] == presence_value
        assert filters['associated_threats']['malware']['id'] == presence_value

    def test_search_indicator_risk_score_presence(self, ci: CollectiveInsights, mocker):
        spy = mocker.patch.object(ci.rf_client, 'request_paged', return_value=[])
        ci.search(indicator_risk_score='present')
        filters = spy.call_args.kwargs['data']['filters']
        assert filters['indicator'] == {'risk': {'score': {'at_detection': 'present'}}}

    def test_search_forwards_pagination_args(self, ci: CollectiveInsights, mocker):
        spy = mocker.patch.object(ci.rf_client, 'request_paged', return_value=[])
        ci.search(max_results=25)
        kwargs = spy.call_args.kwargs
        assert kwargs['method'] == 'post'
        assert kwargs['results_path'] == 'data'
        assert kwargs['offset_key'] == 'offset'
        assert kwargs['max_results'] == 25

    def test_search_limit_capped_by_max_results(self, ci: CollectiveInsights, mocker):
        spy = mocker.patch.object(ci.rf_client, 'request_paged', return_value=[])
        ci.search(max_results=3, page_size=100)
        assert spy.call_args.kwargs['data']['limit'] == 3

    @pytest.mark.parametrize(
        'exc',
        [
            ConnectionError('Connection Error'),
            ConnectTimeout('Connection Timed Out'),
            ReadTimeout('Read Timed Out'),
            HTTPError('HTTP Error'),
        ],
    )
    def test_search_raises_CollectiveInsightsSearchError(
        self, ci: CollectiveInsights, mocker, exc,
    ):
        mocker.patch.object(ci.rf_client, 'request_paged', side_effect=exc)
        with pytest.raises(CollectiveInsightsSearchError):
            ci.search(indicator_type='ip')

    @pytest.mark.parametrize(
        'kwargs',
        [
            {'indicator_type': 123},
            {'max_results': 0},
            {'page_size': 5000},
            {'detection_time_from': 'not-a-date'},
        ],
    )
    def test_search_raises_ValidationError(self, ci: CollectiveInsights, kwargs):
        with pytest.raises(ValidationError):
            ci.search(**kwargs)

    def test_search_raises_ValidationError_on_bad_response(
        self, ci: CollectiveInsights, mocker,
    ):
        mocker.patch.object(
            ci.rf_client,
            'request_paged',
            return_value=[{'no_id_field': True}],
        )
        with pytest.raises(ValidationError):
            ci.search(indicator_type='ip')

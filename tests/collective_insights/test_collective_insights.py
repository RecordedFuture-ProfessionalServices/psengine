import pytest
from pydantic import ValidationError
from requests import ConnectionError, ConnectTimeout, HTTPError, ReadTimeout, Response  # noqa: A004

from psengine.collective_insights import (
    CollectiveInsights,
    CollectiveInsightsError,
    Insight,
    InsightsIn,
)


class Test_CollectiveInsights:
    @pytest.mark.parametrize('bad_insight', [1, 'insight', None])
    def test_submit_raises_ValidationError(self, bad_insight, ci: CollectiveInsights):
        with pytest.raises(ValidationError):
            ci.submit(insight=bad_insight)

    def test_submit_raises_ValueError(self, ci: CollectiveInsights):
        with pytest.raises(ValueError):
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

    @pytest.mark.parametrize('value', [['uhash:1234'], None, ['a', 'b']], ids=lambda v: str(v))
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

    def test_submit_raises_ValidationError_on_bad_response(
        self, insight: Insight, ci: CollectiveInsights, mocker
    ):
        r = Response()
        r._content = b'{"bad": "response"}'
        r.status_code = 200
        mocker.patch.object(ci.rf_client, 'request', return_value=r)
        with pytest.raises(ValidationError):
            ci.submit(insight)

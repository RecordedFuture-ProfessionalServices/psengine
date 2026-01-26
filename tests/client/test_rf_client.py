import json
import logging
import os
import re
from unittest import mock
from unittest.mock import patch

import jsonpath_ng
import pytest
import requests
from pydantic import ValidationError
from requests.models import HTTPError

from psengine import (
    BaseHTTPClient,
    RFClient,
)
from psengine.endpoints import (
    EP_CLASSIC_ALERTS_RULES,
    EP_PLAYBOOK_ALERT_SEARCH,
)
from psengine.logger import RFLogger
from tests.client.conftest import MOCK_DIR


def build_incident_report_page(*, credentials, details, next_offset=None):
    """
    Minimal payload shape for request_paged(results_path=['credentials','details'])
    that exercises the POST 'next_offset' pagination branch.
    """
    payload = {
        'credentials': credentials,
        'details': details,
    }
    if next_offset is not None:
        payload['next_offset'] = next_offset
    return payload


def build_counts_page(*, results, returned=None, total=None, root=('data', 'results')):
    """
    Build a minimal RF-like response with `counts` and results under root path.
    root=("data","results") corresponds to JSONPath 'data.results'.
    """
    returned = len(results) if returned is None else returned
    total = returned if total is None else total

    payload = {'counts': {'returned': returned, 'total': total}}
    cur = payload
    for k in root[:-1]:
        cur = cur.setdefault(k, {})
    cur[root[-1]] = results
    return payload


def build_next_offset_page(*, results, next_offset=None, root=('data', 'results')):
    payload = {}
    cur = payload
    for k in root[:-1]:
        cur = cur.setdefault(k, {})
    cur[root[-1]] = results
    if next_offset is not None:
        payload['next_offset'] = next_offset
    return payload


class Test_RFClientPagedGet:
    def test_request_paged(self, rfc, make_response, mocker, make_request_side_effect):
        p1 = build_counts_page(
            results=[{'id': 1}, {'id': 2}], returned=2, total=5, root=('data', 'results')
        )
        p2 = build_counts_page(
            results=[{'id': 3}, {'id': 4}], returned=2, total=5, root=('data', 'results')
        )
        p3 = build_counts_page(results=[{'id': 5}], returned=1, total=5, root=('data', 'results'))

        responses = iter([make_response(p1), make_response(p2), make_response(p3)])
        side_effect, captured_params = make_request_side_effect(responses, capture_params=True)
        spy = mocker.patch.object(rfc, 'request', side_effect=side_effect)

        out = rfc.request_paged(
            method='get',
            url='https://example/rf',
            params={'limit': 2},
            results_path='data.results',
            offset_key='from',
            max_results=5,
        )

        assert [x['id'] for x in out] == [1, 2, 3, 4, 5]
        assert spy.call_count == 3
        captured_params = captured_params['params']

        assert captured_params[0] == {'limit': 2}
        assert captured_params[1]['from'] == 2
        assert captured_params[1]['limit'] == 2
        assert captured_params[2]['from'] == 4
        assert captured_params[2]['limit'] == 1

    def test_paged_request_max_results(self, rfc, make_response, mocker, make_request_side_effect):
        max_results = 100
        page_size = 10
        total_available = 500

        responses = []
        for page_idx in range(max_results // page_size):
            start = page_idx * page_size
            results = [{'id': i} for i in range(start, start + page_size)]
            responses.append(
                make_response(
                    build_counts_page(
                        results=results,
                        total=total_available,
                        root=('data', 'results'),
                    )
                )
            )

        responses = iter(responses)
        side_effect, captured_params = make_request_side_effect(responses, capture_params=True)
        spy = mocker.patch.object(rfc, 'request', side_effect=side_effect)

        response = rfc.request_paged(
            method='get',
            url='https://api.recordedfuture.com/v2/alert/search',
            max_results=max_results,
            params={'limit': 10, 'triggered': '-10d'},
            results_path='data.results',
            offset_key='from',
        )

        assert len(response) == 100
        assert spy.call_count == 10
        captured_params = captured_params['params']

        assert captured_params[0]['limit'] == 10
        assert captured_params[1]['from'] == 10
        assert captured_params[-1]['from'] == 90

    def test_request_paged_empty_results(self, rfc, mocker, make_response):
        empty_page = build_counts_page(
            results=[],
            returned=0,
            total=0,
            root=('data', 'results'),
        )

        mocker.patch.object(rfc, 'request', return_value=make_response(empty_page))

        params = {'limit': 10, 'q': 'no-results-expected'}
        result = rfc.request_paged(
            method='get',
            url='https://api.recordedfuture.com/v2/alert/search',
            params=params,
            results_path='data.results',
            offset_key='from',
        )

        assert result == []

    def test_request_paged_bad_results_path_raises_ValueError(self, rfc):
        data = {'name': 'Fancy', 'limit': 10}
        with pytest.raises(ValueError, match=r'Invalid results_path: invalid_jsonpath\[\]\[\]\[\]'):
            rfc.request_paged(
                method='get',
                url='https://api.recordedfuture.com/threat/actor/search',
                data=data,
                results_path='invalid_jsonpath[][][]',
                offset_key='offset',
            )

    def test_request_paged_wrong_results_path(self, rfc, mocker, make_response):
        payload = build_counts_page(
            results=[{'id': 'x'}],
            returned=1,
            total=1,
            root=('data', 'results'),
        )

        mocker.patch.object(rfc, 'request', return_value=make_response(payload))

        params = {'limit': 10}

        with pytest.raises(KeyError):
            rfc.request_paged(
                method='get',
                url='https://api.recordedfuture.com/v2/alert/search',
                params=params,
                results_path='non_existing.path',
                offset_key='from',
            )

        with pytest.raises(KeyError):
            rfc.request_paged(
                method='get',
                url='https://api.recordedfuture.com/v2/alert/search',
                params=params,
                results_path='data.results[*].not_exists',
                offset_key='from',
            )


class Test_RFClientPagedPost:
    def test_request_paged(self, rfc, make_response, mocker, make_request_side_effect):
        p1 = build_next_offset_page(
            results=[{'id': 1}, {'id': 2}], next_offset='t1', root=('data', 'results')
        )
        p2 = build_next_offset_page(
            results=[{'id': 3}, {'id': 4}], next_offset='t2', root=('data', 'results')
        )
        p3 = build_next_offset_page(results=[{'id': 5}], next_offset=None, root=('data', 'results'))

        responses = iter([make_response(p1), make_response(p2), make_response(p3)])

        side_effect, captured_data = make_request_side_effect(responses, capture_data=True)
        spy = mocker.patch.object(rfc, 'request', side_effect=side_effect)

        out = rfc.request_paged(
            method='post',
            url='https://example/rf',
            data={'limit': 2},
            results_path='data.results',
            offset_key='next_offset',
            max_results=5,
        )

        assert [x['id'] for x in out] == [1, 2, 3, 4, 5]
        assert spy.call_count == 3
        captured_data = captured_data['data']

        assert captured_data[0] == {'limit': 2}
        assert captured_data[1]['next_offset'] == 't1'
        assert captured_data[2]['next_offset'] == 't2'

    def test_paged_request_max_results(self, rfc, make_response, mocker, make_request_side_effect):
        max_results = 1565
        total_available = 2000
        page_size = 100

        responses = []
        for page_idx in range(max_results // page_size):
            start = page_idx * page_size
            results = [{'id': i} for i in range(start, start + page_size)]
            responses.append(
                make_response(
                    build_counts_page(
                        results=results,
                        total=total_available,
                        root=('identities',),
                    )
                )
            )

        # final partial page of 65
        start = 15 * page_size
        results = [{'id': i} for i in range(start, start + (max_results - 15 * page_size))]
        responses.append(
            make_response(
                build_counts_page(
                    results=results,
                    total=total_available,
                    root=('identities',),
                )
            )
        )

        responses = iter(responses)
        side_effect, captured_data = make_request_side_effect(responses, capture_data=True)
        spy = mocker.patch.object(rfc, 'request', side_effect=side_effect)

        response = rfc.request_paged(
            method='post',
            url='https://api.recordedfuture.com/identity/credentials/search',
            max_results=max_results,
            data={
                'domains': ['norsegods.online'],
                'filter': {'first_downloaded_gte': '2024-01-01T23:40:47.034Z'},
                'limit': 100,
            },
            results_path='identities',
            offset_key='offset',
        )

        assert len(response) == 1565
        assert spy.call_count == 16
        captured_data = captured_data['data']

        assert captured_data[0]['limit'] == 100
        assert captured_data[1]['offset'] == 100
        assert captured_data[2]['offset'] == 200
        assert captured_data[-1]['offset'] == 1500
        assert captured_data[-1]['limit'] == 65

    def test_request_paged_empty_results(self, rfc, mocker, make_response):
        empty_page = build_counts_page(
            results=[],
            returned=0,
            total=0,
            root=('data',),  # results_path in the call is data[*].id, but empty "data" is enough
        )

        mocker.patch.object(rfc, 'request', return_value=make_response(empty_page))

        data = {'name': 'not_an_actual_threat_actor_name', 'limit': 10}
        result = rfc.request_paged(
            method='post',
            url='https://api.recordedfuture.com/threat/actor/search',
            data=data,
            results_path='data[*].id',
            offset_key='offset',
        )

        assert result == []

    def test_request_paged_bad_results_path_raises_ValueError(self, rfc):
        data = {'name': 'Fancy', 'limit': 10}
        with pytest.raises(ValueError, match=r'Invalid results_path: invalid_jsonpath\[\]\[\]\[\]'):
            rfc.request_paged(
                method='post',
                url='https://api.recordedfuture.com/threat/actor/search',
                data=data,
                results_path='invalid_jsonpath[][][]',
                offset_key='offset',
            )

    def test_request_paged_wrong_results_path(self, rfc, mocker, make_response):
        payload_ok_shape = build_counts_page(
            results=[{'id': 'ta-1'}],
            returned=1,
            total=1,
            root=('data',),
        )

        mocker.patch.object(rfc, 'request', return_value=make_response(payload_ok_shape))
        data = {'name': 'Fancy', 'limit': 10}

        with pytest.raises(KeyError):
            rfc.request_paged(
                method='post',
                url='https://api.recordedfuture.com/threat/actor/search',
                data=data,
                results_path='non_existing.path',
                offset_key='offset',
            )

        payload_missing_field = build_counts_page(
            results=[{'id': 'ta-1'}],
            returned=1,
            total=1,
            root=('data',),
        )

        mocker.patch.object(rfc, 'request', return_value=make_response(payload_missing_field))

        with pytest.raises(KeyError):
            rfc.request_paged(
                method='post',
                url='https://api.recordedfuture.com/threat/actor/search',
                data=data,
                results_path='data[*].not_exists',
                offset_key='offset',
            )

    @pytest.mark.parametrize('include_details', [True, False])
    def test_request_paged_multiple_keys_post_next_offset(
        self, rfc, mocker, include_details, make_response, make_request_side_effect
    ):
        creds_p1 = [{'id': i} for i in range(20)]
        creds_p2 = [{'id': i} for i in range(20, 40)]
        creds_p3 = [{'id': i} for i in range(40, 50)]

        if include_details:
            details_p1 = [{'d': i} for i in range(20)]
            details_p2 = [{'d': i} for i in range(20, 40)]
            details_p3 = [{'d': i} for i in range(40, 50)]
        else:
            details_p1 = []
            details_p2 = []
            details_p3 = []

        responses = iter(
            [
                make_response(
                    build_incident_report_page(
                        credentials=creds_p1, details=details_p1, next_offset='t1'
                    )
                ),
                make_response(
                    build_incident_report_page(
                        credentials=creds_p2, details=details_p2, next_offset='t2'
                    )
                ),
                make_response(
                    build_incident_report_page(
                        credentials=creds_p3, details=details_p3, next_offset=None
                    )
                ),
            ]
        )

        side_effect, captured_data = make_request_side_effect(responses, capture_data=True)
        spy = mocker.patch.object(rfc, 'request', side_effect=side_effect)

        source = 'identity-moduleasdlfk'
        payload = {
            'source': source,
            'include_details': include_details,
            'organization_id': None,
            'limit': 20,
            'offset': 0,
        }

        resp = rfc.request_paged(
            'post',
            url='https://example/identity/incident-report',
            data=payload,
            max_results=50,
            results_path=['credentials', 'details'],
            offset_key='offset',  # gets overwritten with next_offset tokens during paging
        )

        assert isinstance(resp, dict)
        assert len(resp['credentials']) == 50
        assert isinstance(resp['credentials'], list)

        if include_details:
            assert len(resp['details']) == 50
        else:
            assert resp['details'] == []

        captured_data = captured_data['data']

        assert spy.call_count == 3
        assert captured_data[0]['limit'] == 20
        assert captured_data[1]['offset'] == 't1'
        assert captured_data[2]['offset'] == 't2'
        assert captured_data[2]['limit'] == 10


class Test_RFClient:
    def test_init_RFClient(self, rf_token):
        rfc = RFClient(api_token=rf_token)
        assert isinstance(rfc, RFClient)

        rfc = RFClient()
        assert isinstance(rfc, RFClient)

    def test_is_authorized_success(self, rfc, mock_request, mocker):
        mocks = [
            mock_request(MOCK_DIR / 'test_is_authorized_success_0.json'),
        ]
        mocker.patch.object(rfc, 'request', side_effect=mocks)

        assert rfc.is_authorized('get', 'https://api.recordedfuture.com/v2/ip/2.5.29.1') is True

    urls = [
        'https://api.recordedfuture.com/v2/something/2.5.29.1',
        'https://api.recordedfuture.com/gw/xsoar/domain/google.com',
    ]

    @pytest.mark.parametrize('url', urls, ids=(i for i in range(len(urls))))
    def test_is_authorized_failure(self, rfc, url, mocker):
        response = requests.Response()
        response.status_code = 403
        excp_obj = HTTPError('error')
        excp_obj.response = response
        mocker.patch.object(rfc, 'request', side_effect=excp_obj)

        assert rfc.is_authorized('get', url) is False

    def test_proxies(self, mock_request, mocker):
        rfc = RFClient(https_proxy='https://localhost:8080', verify=False)
        mocks = [
            mock_request(MOCK_DIR / 'test_proxies_0.json'),
        ]
        mocker.patch.object(rfc, 'request', side_effect=mocks)

        response = rfc.request(method='get', url=EP_CLASSIC_ALERTS_RULES, params={'limit': 1})

        assert response.status_code == 200
        assert response.json()['counts']['returned'] > 0

    def test_proxies_https_config_is_picked_up(self, rf_token):
        rfc = RFClient(
            api_token=rf_token,
            retries=0,
            timeout=1,
            https_proxy='https://localhost:8080',
            verify=False,
        )

        # We are not able to test on a real/fake proxy so we can say that the proxy config
        # works if we are gettinga proxy error. RFClient tries to connect to the proxy but since
        # we dont have one it will fail - hence not going direct against the API
        with pytest.raises(requests.exceptions.ProxyError):
            rfc.request('get', EP_CLASSIC_ALERTS_RULES)

    params = [
        ('data', 'data'),
        ('data.path', 'data'),
        ('data[*].path', 'data'),
        ('data.results[*].path', 'data'),
    ]

    @pytest.mark.parametrize(('path', 'expected'), params)
    def test_get_root_key(self, rfc, path, expected):
        path_expr = jsonpath_ng.parse(path)
        assert rfc._get_root_key(path_expr) == expected

    def test_is_api_token_valid(self, rf_token):
        with pytest.raises(ValidationError):
            RFClient(api_token=123)
        with pytest.raises(
            ValueError,
            match=re.escape('Invalid Recorded Future API token: must match regex ^[a-z0-9]{32}$'),
        ):
            RFClient(api_token='123')  # noqa: S106
        with pytest.raises(
            ValueError,
            match=re.escape('Invalid Recorded Future API token: must match regex ^[a-z0-9]{32}$'),
        ):
            RFClient(api_token='opiubouib1o5uiybvuioyv5i---898hg')  # noqa: S106

        # Now give it a valid token
        RFClient(api_token=rf_token)

    def test_prepare_headers_with_token(self, rf_token, mocker: mock):
        mocker.patch('psengine.base_http_client.OSHelpers.os_platform', return_value='Linux')
        mocker.patch('psengine.base_http_client.SDK_ID', 'SDK_ID')
        client = RFClient(api_token=rf_token)
        headers = client._prepare_headers()

        expected_headers = {
            'User-Agent': 'app_id unknown (Linux) SDK_ID platform_id unknown',
            'Content-Type': 'application/json',
            'accept': 'application/json',
            'X-RFToken': rf_token,
        }

        assert headers == expected_headers

    def test_prepare_headers_without_token(self, caplog, rfc, mocker: mock):
        mocker.patch('psengine.base_http_client.OSHelpers.os_platform', return_value='Linux')
        mocker.patch('psengine.base_http_client.SDK_ID', 'SDK_ID')

        RFLogger()
        rfc._api_token = None
        headers = rfc._prepare_headers()

        expected_headers = {
            'User-Agent': 'app_id unknown (Linux) SDK_ID platform_id unknown',
            'Content-Type': 'application/json',
            'accept': 'application/json',
        }

        with caplog.at_level(logging.WARNING, logger='psengine'):
            assert headers == expected_headers
            assert 'Request being made with no Recorded Future API key set' in caplog.text

    def test_paged_request_response_not_JSON(self, rfc, make_csv_response, mocker):
        mock = make_csv_response('a,b,c,d\n1,2,3,4')
        mocker.patch.object(rfc, 'request', return_value=mock)
        mock.json.side_effect = requests.exceptions.JSONDecodeError('Expecting value', mock.text, 0)
        with pytest.raises(requests.exceptions.JSONDecodeError):
            rfc.request_paged(
                method='head',
                url='https://api.recordedfuture.com/v2/fusion/files',
                params={'path': '/home/william_md5_risklist_2.csv'},
                results_path='data',
                offset_key='offset',
            )

    def test_cert_auth(self, tests_dir, rfc, mock_request, mocker):
        rfc = RFClient(
            auth=('elastic', 'password'),
            cert=(
                os.path.join(tests_dir, 'static', 'certs', 'es01.crt'),
                os.path.join(tests_dir, 'static', 'certs', 'es01.key'),
            ),
            verify=os.path.join(tests_dir, 'static', 'certs', 'ca.crt'),
        )
        mocks = [
            mock_request(MOCK_DIR / 'test_cert_auth_0.json'),
        ]
        mocker.patch.object(rfc, 'call', side_effect=mocks)

        r = rfc.call(method='get', url='https://localhost:9200')
        assert r.status_code == 200

    def test_max_results_queries_only_required_pages(self, rfc):
        def create_mock_response(status_code, json_data):
            response = requests.Response()
            response.status_code = status_code
            response._content = json.dumps(json_data).encode('utf-8')

            return response

        with patch.object(
            BaseHTTPClient,
            'call',
            side_effect=[
                create_mock_response(200, {'data': {'results': [1, 2, 3]}, 'next_offset': 'abcde'}),
                create_mock_response(200, {'data': {'results': [4, 5, 6]}, 'next_offset': 'fghij'}),
                create_mock_response(200, {'data': {'results': [7, 8, 9]}, 'next_offset': 'klmno'}),
                create_mock_response(
                    200, {'data': {'results': [10, 11, 12]}, 'next_offset': 'pqrst'}
                ),
                create_mock_response(200, {'data': {'results': [13, 14, 15]}}),
            ],
        ) as mock_method:
            response = rfc.request_paged(
                method='post',
                url=EP_PLAYBOOK_ALERT_SEARCH,
                data={'limit': 100},
                results_path='data.results',
                offset_key='next_offset',
                max_results=4,
            )
            assert len(response) == 4
            assert mock_method.call_count == 2

import json
import logging
import os
import re
from pathlib import Path
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
    EP_CLASSIC_ALERTS_SEARCH,
    EP_PLAYBOOK_ALERT_SEARCH,
)
from psengine.identity import IdentityMgr
from psengine.logger import RFLogger
from tests.client.conftest import MOCK_DIR

ENDPOINTS_TO_PAGE = [
    (
        'get',
        EP_CLASSIC_ALERTS_RULES,
        None,
        {'limit': 1, 'freetext': 'leaked'},
        'data.results',
        'from',
        5,
    ),
    ('get', EP_CLASSIC_ALERTS_RULES, None, None, 'data.results', 'from', 141),
    (
        'get',
        EP_CLASSIC_ALERTS_SEARCH,
        None,
        {'limit': 7, 'triggered': '-20d', 'alertRule': 'mf0rAZ', 'fields': 'id'},
        'data',
        'from',
        15,
    ),
    (
        'get',
        'https://api.recordedfuture.com/v2/ip/search',
        None,
        {'limit': 100, 'fields': 'entity', 'riskRule': 'dnsAbuse'},
        'data.results',
        'from',
        1000,
    ),
    (
        'post',
        'https://api.recordedfuture.com/threat/actor/search',
        {'name': 'Fancy', 'limit': 10},
        None,
        'data',
        'offset',
        49,
    ),
    (
        'post',
        'https://api.recordedfuture.com/identity/credentials/search',
        {
            'domains': ['norsegods.online'],
            'filter': {'first_downloaded_gte': '2024-01-01T23:40:47.034Z'},
            'limit': 10,
        },
        None,
        'identities',
        'offset',
        1000,
    ),
    (
        'post',
        'https://api.recordedfuture.com/detection-rule/search',
        {'filter': {'created': {'after': '2024-08-10T12:00:00.000Z'}}, 'limit': 10},
        None,
        'result',
        'offset',
        70,
    ),
    (
        'post',
        'https://api.recordedfuture.com/analyst-note/search',
        {'published': '-2d', 'topic': 'TXSFt3', 'limit': 10},
        None,
        'data',
        'from',
        21,
    ),
    (
        'post',
        'https://api.recordedfuture.com/playbook-alert/search',
        {
            'limit': 10,
            'category': ['domain_abuse'],
            'created_range': {'from': '2025-06-10T07:32:28Z'},
        },
        None,
        'data',
        'from',
        102,
    ),
]


class Test_RFClient:
    def test_init_RFClient(self, rf_token):
        rfc = RFClient(api_token=rf_token)
        assert isinstance(rfc, RFClient)

    @pytest.mark.parametrize(
        ('method', 'url', 'data', 'params', 'results_path', 'offset_key', 'expected'),
        ENDPOINTS_TO_PAGE,
        ids=(f'{i[0]}-{i[4]}-{i[6]}' for i in ENDPOINTS_TO_PAGE),
    )
    def test_request_paged(
        self,
        rf_token,
        method,
        url,
        data,
        params,
        results_path,
        offset_key,
        expected,
        mocker,
        mock_request,
        request,
    ):
        node_id = request.node.callspec.id
        rfc = RFClient(api_token=rf_token)
        pattern = re.compile(rf'^test_request_paged\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name))
        mocks = [mock_request(f) for f in files]
        mocker.patch.object(rfc, 'request', side_effect=mocks)

        response = rfc.request_paged(
            method=method,
            url=url,
            data=data,
            params=params,
            results_path=results_path,
            offset_key=offset_key,
            max_results=expected,
        )

        assert len(response) == expected

    def test_paged_request_max_results(self, rf_token, mocker, mock_request):
        rfc = RFClient(api_token=rf_token)
        mocks = [
            *[
                mock_request(MOCK_DIR / f'test_paged_request_max_results_{i}.json')
                for i in range(6)
            ],
            *[
                mock_request(MOCK_DIR / f'test_paged_request_max_results_{i}.json')
                for i in range(7, 17)
            ],
        ]
        mocker.patch.object(rfc, 'request', side_effect=mocks)

        response = rfc.request_paged(
            method='post',
            url='https://api.recordedfuture.com/identity/credentials/search',
            max_results=1565,
            data={
                'domains': ['norsegods.online'],
                'filter': {'first_downloaded_gte': '2024-01-01T23:40:47.034Z'},
                'limit': 100,
            },
            results_path='identities',
            offset_key='offset',
        )

        assert len(response) == 1565

        response = rfc.request_paged(
            method='get',
            url='https://api.recordedfuture.com/v2/alert/search',
            max_results=100,
            params={'limit': 10, 'triggered': '-10d'},
            results_path='data.results',
            offset_key='from',
        )

        assert len(response) == 100

    def test_request_paged_empty_results(self, rf_token, mock_request, mocker):
        rfc = RFClient(api_token=rf_token)
        mocks = mock_request(MOCK_DIR / 'test_request_paged_empty_results_0.json')
        mocker.patch.object(rfc, 'request', return_value=mocks)

        data = {'name': 'not_an_actual_threat_actor_name', 'limit': 10}
        result = rfc.request_paged(
            method='post',
            url='https://api.recordedfuture.com/threat/actor/search',
            data=data,
            results_path='data[*].id',
            offset_key='offset',
        )
        assert result == []

    def test_request_paged_bad_results_path_raises_ValueError(self, rf_token):
        rfc = RFClient(api_token=rf_token)
        data = {'name': 'Fancy', 'limit': 10}
        with pytest.raises(ValueError, match=r'Invalid results_path: invalid_jsonpath\[\]\[\]\[\]'):
            rfc.request_paged(
                method='post',
                url='https://api.recordedfuture.com/threat/actor/search',
                data=data,
                results_path='invalid_jsonpath[][][]',
                offset_key='offset',
            )

    def test_request_paged_wrong_results_path(self, rf_token, mock_request, mocker):
        rfc = RFClient(api_token=rf_token)
        mocks = [
            mock_request(MOCK_DIR / 'test_request_paged_wrong_results_path_0.json'),
            mock_request(MOCK_DIR / 'test_request_paged_wrong_results_path_1.json'),
        ]
        mocker.patch.object(rfc, 'request', side_effect=mocks)

        data = {'name': 'Fancy', 'limit': 10}
        with pytest.raises(KeyError):
            rfc.request_paged(
                method='post',
                url='https://api.recordedfuture.com/threat/actor/search',
                data=data,
                results_path='non_existing.path',
                offset_key='offset',
            )
        with pytest.raises(KeyError):
            rfc.request_paged(
                method='post',
                url='https://api.recordedfuture.com/threat/actor/search',
                data=data,
                results_path='data[*].meow',
                offset_key='offset',
            )

    def test_is_authorized_success(self, rf_token, mock_request, mocker):
        rfc = RFClient(api_token=rf_token)
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
    def test_is_authorized_failure(self, rf_token, url, mocker):
        rfc = RFClient(api_token=rf_token)
        response = requests.Response()
        response.status_code = 403
        excp_obj = HTTPError('error')
        excp_obj.response = response
        mocker.patch.object(rfc, 'request', side_effect=excp_obj)

        assert rfc.is_authorized('get', url) is False

    def test_proxies(self, rf_token, mock_request, mocker):
        rfc = RFClient(api_token=rf_token, https_proxy='https://localhost:8080', verify=False)
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
    def test_get_root_key(self, rf_token, path, expected, mock_request, mocker):
        rfc = RFClient(api_token=rf_token)
        mocks = [
            mock_request(MOCK_DIR / 'test_request_paged_wrong_results_path_0.json'),
            mock_request(MOCK_DIR / 'test_request_paged_wrong_results_path_1.json'),
        ]
        mocker.patch.object(rfc, 'request', return_value=mocks)

        path_expr = jsonpath_ng.parse(path)
        assert rfc._get_root_key(path_expr) == expected

    def test_is_api_token_valid(self, rf_token):
        with pytest.raises(ValidationError):
            RFClient(api_token=123)
        with pytest.raises(
            ValueError,
            match=re.escape('Invalid Recorded Future API token: must match regex ^[a-f0-9]{32}$'),
        ):
            RFClient(api_token='123')  # noqa: S106
        with pytest.raises(
            ValueError,
            match=re.escape('Invalid Recorded Future API token: must match regex ^[a-f0-9]{32}$'),
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

    def test_prepare_headers_without_token(self, caplog, rf_token, mocker: mock):
        mocker.patch('psengine.base_http_client.OSHelpers.os_platform', return_value='Linux')
        mocker.patch('psengine.base_http_client.SDK_ID', 'SDK_ID')

        client = RFClient(api_token=rf_token)
        RFLogger()
        client._api_token = None
        headers = client._prepare_headers()

        expected_headers = {
            'User-Agent': 'app_id unknown (Linux) SDK_ID platform_id unknown',
            'Content-Type': 'application/json',
            'accept': 'application/json',
        }

        with caplog.at_level(logging.WARNING, logger='psengine'):
            assert headers == expected_headers
            assert 'Request being made with no Recorded Future API key set' in caplog.text

    def test_paged_request_response_not_JSON(self, rf_token, make_csv_response, mocker):
        rfc = RFClient(api_token=rf_token)
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

    def test_cert_auth(self, tests_dir, rf_token, mock_request, mocker):
        rfc = RFClient(
            api_token=rf_token,
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

    def create_mock_response(self, status_code, json_data):
        response = requests.Response()
        response.status_code = status_code
        response._content = json.dumps(json_data).encode('utf-8')

        return response

    def test_max_results_queries_only_required_pages(self, rf_token):
        with patch.object(
            BaseHTTPClient,
            'call',
            side_effect=[
                self.create_mock_response(
                    200, {'data': {'results': [1, 2, 3]}, 'next_offset': 'abcde'}
                ),
                self.create_mock_response(
                    200, {'data': {'results': [4, 5, 6]}, 'next_offset': 'fghij'}
                ),
                self.create_mock_response(
                    200, {'data': {'results': [7, 8, 9]}, 'next_offset': 'klmno'}
                ),
                self.create_mock_response(
                    200, {'data': {'results': [10, 11, 12]}, 'next_offset': 'pqrst'}
                ),
                self.create_mock_response(200, {'data': {'results': [13, 14, 15]}}),
            ],
        ) as mock_method:
            client = RFClient(api_token=rf_token)
            response = client.request_paged(
                method='post',
                url=EP_PLAYBOOK_ALERT_SEARCH,
                data={'limit': 100},
                results_path='data.results',
                offset_key='next_offset',
                max_results=4,
            )
            assert len(response) == 4
            assert mock_method.call_count == 2

    @pytest.mark.parametrize('details', [True, False])
    def test_multiple_keys_paged_request(self, details, mock_request, mocker, request):
        mgr = IdentityMgr()
        node_id = request.node.callspec.id
        pattern = re.compile(
            rf'^test_multiple_keys_paged_request\[{re.escape(node_id)}\]_\d+\.json$'
        )
        files = sorted(f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name))
        mocks = [mock_request(f) for f in files]

        mocker.patch.object(mgr.rf_client, 'request', side_effect=mocks)

        source = 'identity-moduleasdlfk'
        resp = mgr.fetch_incident_report(source, include_details=details, max_results=50)

        assert isinstance(resp.credentials, list)
        if details:
            assert resp.details is not None
        else:
            assert resp.details is None

        assert len(resp.credentials) == 50

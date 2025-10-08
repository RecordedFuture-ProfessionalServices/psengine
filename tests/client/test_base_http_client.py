import logging
import os
from unittest import mock

import pytest
from pydantic import ValidationError
from requests import Response
from requests.exceptions import HTTPError, ProxyError

from psengine.base_http_client import BaseHTTPClient
from psengine.endpoints import BASE_URL
from psengine.logger.rf_logger import RFLogger
from tests.client.conftest import MOCK_DIR

TEST_DATA_OK = [
    ('get', 'https://httpbin.org/get', None, 200),
    ('post', 'https://httpbin.org/post', {'key': 'value'}, 200),
    ('put', 'https://httpbin.org/put', {'key': 'value'}, 200),
    ('delete', 'https://httpbin.org/delete', None, 200),
    ('patch', 'https://httpbin.org/patch', {'key': 'value'}, 200),
]
TEST_DATA_FAIL = [
    ('get', 'https://httpbin.org/status/404', None, 404),
    ('get', 'https://httpbin.org/status/500', None, 500),
    ('post', 'https://httpbin.org/status/500', {'key': 'value'}, 500),
    ('post', 'https://httpbin.org/status/404', {'key': 'value'}, 404),
    ('put', 'https://httpbin.org/status/404', {'key': 'value'}, 404),
    ('put', 'https://httpbin.org/status/500', {'key': 'value'}, 500),
    ('delete', 'https://httpbin.org/status/500', None, 500),
    ('delete', 'https://httpbin.org/status/404', None, 404),
    ('patch', 'https://httpbin.org/status/404', {'key': 'value'}, 404),
    ('patch', 'https://httpbin.org/status/500', {'key': 'value'}, 500),
]


class Test_BaseHTTPClient:
    @pytest.mark.parametrize(
        ('method', 'url', 'data', 'expected_status_code'),
        TEST_DATA_OK,
        ids=(f'{i[0]}-{i[3]}' for i in TEST_DATA_OK),
    )
    def test_call_ok(
        self, base_client, method, url, data, expected_status_code, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        mocks = mock_request(MOCK_DIR / f'test_call_ok[{node_id}]_0.json')
        mocker.patch.object(base_client, 'call', return_value=mocks)

        response = base_client.call(method=method, url=url, data=data)
        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        ('method', 'url', 'data', 'expected_status_code'),
        TEST_DATA_FAIL,
        ids=(f'{i[0]}-{i[3]}' for i in TEST_DATA_FAIL),
    )
    def test_call_fail(self, base_client, method, url, data, expected_status_code, mocker):
        response = Response()
        response.status_code = expected_status_code
        excp_obj = HTTPError('error')
        excp_obj.response = response
        mocker.patch.object(base_client, 'call', side_effect=excp_obj)

        with pytest.raises(HTTPError):
            base_client.call(method=method, url=url, data=data)

    def test_headers(self, base_client, mocker, mock_request):
        mocks = mock_request(MOCK_DIR / 'test_headers_0.json')
        mocker.patch.object(base_client, 'call', return_value=mocks)

        headers = {'X-Test': 'test', 'X-Rftoken': 'token123'}
        response = base_client.call(
            method='get',
            url='https://httpbin.org/headers',
            headers=headers,
        )
        assert response.status_code == 200
        assert len(response.json()['headers']) == 7
        assert 'psengine-py/' in response.json()['headers']['User-Agent']
        assert response.json()['headers']['X-Test'] == 'test'
        assert response.json()['headers']['X-Rftoken'] == 'token123'

    def test_can_connect_True(self, base_client, mocker, make_response):
        mocks = make_response({})
        mocker.patch.object(base_client, 'call', return_value=mocks)

        assert base_client.can_connect(method='get', url='https://api.recordedfuture.com') is True

    def test_can_connect_False(self, mocker):
        response = Response()
        response.status_code = 500
        excp_obj = ConnectionError('error')
        excp_obj.response = response

        client = BaseHTTPClient(timeout=1, retries=0)
        mocker.patch.object(client, 'call', side_effect=excp_obj)

        res = client.can_connect(method='get', url='https://api.recordedfutureiasfhjfadja.com')
        assert res is False

    def test_proxies(self, mocker, mock_request):
        client = BaseHTTPClient(https_proxy='https://localhost:8080', verify=False)
        mocks = mock_request(MOCK_DIR / 'test_proxies_0.json')
        mocker.patch.object(client, 'call', return_value=mocks)

        response = client.call(method='get', url=BASE_URL)
        assert response.status_code == 200

    def test_proxies_http_config_is_picked_up(self, mocker):
        response = Response()
        response.status_code = 500
        excp_obj = ProxyError('error')
        excp_obj.response = response

        client = BaseHTTPClient(https_proxy='https://localhost:8080', verify=False)
        mocker.patch.object(client, 'call', side_effect=excp_obj)

        client = BaseHTTPClient(
            retries=0,
            timeout=1,
            http_proxy='http://localhost:8080',
            verify=False,
        )

        with pytest.raises(ProxyError):
            client.call(method='get', url='http://google.com')

    def test_call_bad_payload_raises_exception(self, rf_token, base_client):
        # TODO - atm it just send the payload. need check to make sure its a dict
        # that can be json dumped
        with pytest.raises(ValidationError):
            base_client.call(
                method='post',
                url='https://api.recordedfuture.com/threat/actor/search',
                data='not a dict',
                headers={'X-RFToken': rf_token},
            )

    def test_call_unknown_http_method_raises_ValueError(self, base_client):
        with pytest.raises(ValueError, match='Unknown HTTP method: getit'):
            base_client.call(method='getit', url='wow')

    def test_call_method_or_url_missing(self, base_client):
        with pytest.raises(ValidationError):
            base_client.call(method='get', url=None)

        with pytest.raises(ValidationError):
            base_client.call(method=None, url='https://httpbin.org/get')

    def test_set_urllib_log_level_valid_levels(self, base_client):
        valid_levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']

        for level in valid_levels:
            base_client.set_urllib_log_level(level)
            assert logging.getLogger('urllib3').level == getattr(logging, level)

    def test_set_urllib_log_level_invalid_level(self, caplog, base_client):
        invalid_level = 'INVALID'
        RFLogger()
        with caplog.at_level(logging.WARNING, logger='psengine'):
            base_client.set_urllib_log_level(invalid_level)
            assert 'Log level is empty or not valid' in caplog.text
            assert logging.getLogger('urllib3').level != getattr(logging, invalid_level, None)

    def test_set_urllib_log_level_empty_level(self, caplog, base_client):
        empty_level = ''
        RFLogger()
        with caplog.at_level(logging.WARNING, logger='psengine'):
            base_client.set_urllib_log_level(empty_level)
            assert 'Log level is empty or not valid' in caplog.text
            assert logging.getLogger('urllib3').level != getattr(logging, empty_level, None)

    def test_get_user_agent_header(self, mocker: mock, base_client):
        sdk_id = 'SDK_ID'  # Replace with the actual SDK_ID if it's defined elsewhere

        mocker.patch('psengine.helpers.OSHelpers.os_platform', return_value='Linux')
        mocker.patch('psengine.base_http_client.SDK_ID', sdk_id)

        user_agent = base_client._get_user_agent_header()
        assert user_agent == 'app_id unknown (Linux) SDK_ID platform_id unknown'

        mocker.patch('psengine.helpers.OSHelpers.os_platform', return_value=None)
        mocker.patch('psengine.base_http_client.SDK_ID', sdk_id)

        user_agent = base_client._get_user_agent_header()
        assert user_agent == 'app_id unknown SDK_ID platform_id unknown'

    def test_cert_auth(self, tests_dir, mocker, mock_request):
        client = BaseHTTPClient(
            auth=('elastic', 'password'),
            cert=(
                os.path.join(tests_dir, 'static', 'certs', 'es01.crt'),
                os.path.join(tests_dir, 'static', 'certs', 'es01.key'),
            ),
            verify=os.path.join(tests_dir, 'static', 'certs', 'ca.crt'),
        )

        mocks = mock_request(MOCK_DIR / 'test_proxies_0.json')
        mocker.patch.object(client, 'call', return_value=mocks)

        r = client.call(method='get', url='https://localhost:9200')
        assert r.status_code == 200

    def test_call_raises_ValueError(self, base_client):
        with pytest.raises(ValidationError):
            base_client.call(data={'a': 2})

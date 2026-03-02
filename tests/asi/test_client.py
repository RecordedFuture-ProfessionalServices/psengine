import logging
from copy import deepcopy

import pytest
from requests import Response
from requests.exceptions import JSONDecodeError

from psengine.asi.client import ASIClient, is_api_token_format_valid
from psengine.config import Config


def _build_page(ids, next_cursor) -> dict:
    return {
        'data': [{'id': x} for x in ids],
        'meta': {'pagination': {'next_cursor': next_cursor}},
    }


@pytest.fixture
def asi_client():
    return ASIClient(api_token='a' * 32)


def test_request_paged_get_uses_expected_query_params(asi_client, mocker, make_response):
    params = {'query': 'example.com'}
    page1 = _build_page([1, 2, 3], 'cursor-1')
    page2 = _build_page([4, 5, 6], 'cursor-2')
    responses = iter([make_response(page1), make_response(page2)])
    captured = []

    def side_effect(*args, **kwargs):  # noqa: ARG001
        captured.append(
            {
                'params': dict(kwargs.get('params') or {}),
                'data': deepcopy(kwargs.get('data')),
            }
        )
        return next(responses)

    spy = mocker.patch.object(asi_client, 'request', side_effect=side_effect)

    result = asi_client.request_paged(
        method='get',
        url='https://example.test/asi',
        params=params,
        max_results=5,
        objects_per_page=3,
    )

    assert [x['id'] for x in result['data']] == [1, 2, 3, 4, 5]
    assert spy.call_count == 2
    assert captured[0]['params'] == {'query': 'example.com', 'limit': 3}
    assert captured[1]['params'] == {'query': 'example.com', 'limit': 2, 'cursor': 'cursor-1'}
    assert captured[0]['data'] is None
    assert captured[1]['data'] is None
    assert params == {'query': 'example.com'}


def test_request_paged_get_keeps_existing_limit(asi_client, mocker, make_response):
    params = {'query': 'example.com', 'limit': 99}
    page = _build_page([1, 2, 3], 'cursor-1')
    captured = []

    def side_effect(*args, **kwargs):  # noqa: ARG001
        captured.append(dict(kwargs.get('params') or {}))
        return make_response(page)

    mocker.patch.object(asi_client, 'request', side_effect=side_effect)

    result = asi_client.request_paged(
        method='get',
        url='https://example.test/asi',
        params=params,
        max_results=2,
        objects_per_page=3,
    )

    assert [x['id'] for x in result['data']] == [1, 2]
    assert captured[0] == {'query': 'example.com', 'limit': 2}
    assert params == {'query': 'example.com', 'limit': 99}


def test_request_paged_post_uses_expected_data_and_cursor_params(asi_client, mocker, make_response):
    data = {'filter': {'name': 'example.com'}}
    page1 = _build_page([1, 2], 'cursor-1')
    page2 = _build_page([3, 4], 'cursor-2')
    responses = iter([make_response(page1), make_response(page2)])
    captured = []

    def side_effect(*args, **kwargs):  # noqa: ARG001
        captured.append(
            {
                'params': dict(kwargs.get('params') or {}),
                'data': deepcopy(kwargs.get('data')),
            }
        )
        return next(responses)

    spy = mocker.patch.object(asi_client, 'request', side_effect=side_effect)

    result = asi_client.request_paged(
        method='post',
        url='https://example.test/asi',
        data=data,
        max_results=3,
        objects_per_page=2,
    )

    assert [x['id'] for x in result['data']] == [1, 2, 3]
    assert spy.call_count == 2
    assert captured[0]['params'] == {}
    assert captured[1]['params'] == {'cursor': 'cursor-1'}
    assert captured[0]['data'] == {'filter': {'name': 'example.com'}, 'pagination': {'limit': 2}}
    assert captured[1]['data'] == {'filter': {'name': 'example.com'}, 'pagination': {'limit': 1}}
    assert data == {'filter': {'name': 'example.com'}}


def test_request_paged_post_keeps_existing_pagination_limit(asi_client, mocker, make_response):
    data = {'filter': {'type': 'domain'}, 'pagination': {'limit': 77, 'order': 'desc'}}
    params = {'project_id': 'p-1'}
    page = _build_page([1], 'cursor-1')
    captured = []

    def side_effect(*args, **kwargs):  # noqa: ARG001
        captured.append(
            {
                'params': dict(kwargs.get('params') or {}),
                'data': deepcopy(kwargs.get('data')),
            }
        )
        return make_response(page)

    mocker.patch.object(asi_client, 'request', side_effect=side_effect)

    result = asi_client.request_paged(
        method='post',
        url='https://example.test/asi',
        params=params,
        data=data,
        max_results=1,
        objects_per_page=2,
    )

    assert result == {'data': [{'id': 1}], 'meta': None}
    assert captured[0]['params'] == {'project_id': 'p-1'}
    assert captured[0]['data'] == {
        'filter': {'type': 'domain'},
        'pagination': {'limit': 1, 'order': 'desc'},
    }
    assert data == {'filter': {'type': 'domain'}, 'pagination': {'limit': 77, 'order': 'desc'}}
    assert params == {'project_id': 'p-1'}


def test_request_paged_get_uses_remaining_results_for_last_request_limit(
    asi_client, mocker, make_response
):
    params = {'query': 'example.com'}
    pages = [
        _build_page(range(1, 11), 'cursor-1'),
        _build_page(range(11, 21), 'cursor-2'),
        _build_page(range(21, 31), 'cursor-3'),
        _build_page(range(31, 34), None),
    ]
    responses = iter([make_response(page) for page in pages])
    captured_params = []

    def call_side_effect(*args, **kwargs):  # noqa: ARG001
        captured_params.append(deepcopy(kwargs.get('params') or {}))
        return next(responses)

    mocker.patch.object(asi_client, 'call', side_effect=call_side_effect)
    request_spy = mocker.spy(asi_client, 'request')

    result = asi_client.request_paged(
        method='get',
        url='https://example.test/asi',
        params=params,
        max_results=33,
        objects_per_page=10,
    )

    assert request_spy.call_count == 4
    assert [item['limit'] for item in captured_params] == [10, 10, 10, 3]
    assert [item.get('cursor') for item in captured_params] == [
        None,
        'cursor-1',
        'cursor-2',
        'cursor-3',
    ]
    assert [x['id'] for x in result['data']] == list(range(1, 34))


def test_request_paged_post_uses_remaining_results_for_last_request_limit(
    asi_client, mocker, make_response
):
    data = {'filter': {'name': 'example.com'}}
    pages = [
        _build_page(range(1, 11), 'cursor-1'),
        _build_page(range(11, 21), 'cursor-2'),
        _build_page(range(21, 31), 'cursor-3'),
        _build_page(range(31, 34), None),
    ]
    responses = iter([make_response(page) for page in pages])
    captured_params = []
    captured_data = []

    def call_side_effect(*args, **kwargs):  # noqa: ARG001
        captured_params.append(deepcopy(kwargs.get('params') or {}))
        captured_data.append(deepcopy(kwargs.get('data') or {}))
        return next(responses)

    mocker.patch.object(asi_client, 'call', side_effect=call_side_effect)
    request_spy = mocker.spy(asi_client, 'request')

    result = asi_client.request_paged(
        method='post',
        url='https://example.test/asi',
        data=data,
        max_results=33,
        objects_per_page=10,
    )

    assert request_spy.call_count == 4
    assert [item['pagination']['limit'] for item in captured_data] == [10, 10, 10, 3]
    assert [item.get('cursor') for item in captured_params] == [
        None,
        'cursor-1',
        'cursor-2',
        'cursor-3',
    ]
    assert [x['id'] for x in result['data']] == list(range(1, 34))


def test_request_paged_forwards_headers_and_kwargs(asi_client, mocker, make_response):
    page = _build_page([1], 'cursor-1')
    spy = mocker.patch.object(asi_client, 'request', return_value=make_response(page))

    asi_client.request_paged(
        method='get',
        url='https://example.test/asi',
        params={'query': 'example.com'},
        headers={'x-test': '1'},
        timeout=17,
        max_results=1,
    )

    assert spy.call_args.kwargs['headers'] == {'x-test': '1'}
    assert spy.call_args.kwargs['timeout'] == 17


def test_request_paged_invalid_method_raises_ValueError(asi_client, mocker):
    spy = mocker.patch.object(asi_client, 'request')

    with pytest.raises(ValueError, match='Invalid method for paged request'):
        asi_client.request_paged('delete', 'https://example.test/asi')

    spy.assert_not_called()


def test_request_paged_raises_on_invalid_json(asi_client, mocker):
    response = mocker.Mock(spec=Response)
    response.text = 'not-json'
    response.json.side_effect = JSONDecodeError('Expecting value', 'not-json', 0)

    mocker.patch.object(asi_client, 'request', return_value=response)

    with pytest.raises(JSONDecodeError):
        asi_client.request_paged(
            method='get',
            url='https://example.test/asi',
            params={'query': 'example.com'},
            max_results=1,
        )


def test_request_paged_raises_when_data_key_is_missing(asi_client, mocker, make_response):
    payload = {'meta': {'pagination': {'next_cursor': 'cursor-1'}}}
    spy = mocker.patch.object(asi_client, 'request', return_value=make_response(payload))

    with pytest.raises(KeyError):
        asi_client.request_paged(
            method='get',
            url='https://example.test/asi',
            params={'query': 'example.com'},
            max_results=1,
        )

    assert spy.call_count == 1


def test_initialize_paged_request_get_copies_params_and_sets_limit(asi_client):
    params = {'query': 'example.com'}
    data = {'a': {'b': 1}}

    request_params, request_data = asi_client._initialize_paged_request(
        method='GET',
        params=params,
        data=data,
        limit=25,
    )

    assert request_params == {'query': 'example.com', 'limit': 25}
    assert request_data == {'a': {'b': 1}}

    request_params['cursor'] = 'cursor-1'
    request_data['a']['b'] = 2
    assert params == {'query': 'example.com'}
    assert data == {'a': {'b': 1}}


def test_initialize_paged_request_post_raises_on_non_dict_pagination(asi_client):
    with pytest.raises(
        ValueError, match=r"`data\['pagination'\]` must be a dictionary when provided"
    ):
        asi_client._initialize_paged_request(
            method='POST',
            params=None,
            data={'pagination': 'invalid'},
            limit=25,
        )


@pytest.mark.parametrize(
    ('token', 'expected'),
    [
        ('a' * 32, True),
        ('A1' * 16, True),
        ('a' * 31, False),
        ('a' * 31 + '-', False),
    ],
)
def test_is_api_token_format_valid(token, expected):
    assert is_api_token_format_valid(token) is expected


def test_asi_client_init_rejects_invalid_api_token():
    with pytest.raises(ValueError, match='Invalid Recorded Future API token'):
        ASIClient(api_token='invalid-token')  # noqa: S106


def test_asi_client_init_rejects_missing_token_from_config(monkeypatch):
    monkeypatch.delenv('RF_ASI_TOKEN', raising=False)
    Config.reset_instance()
    Config.init(asi_token='')

    try:
        with pytest.raises(
            ValueError, match='Missing Recorded Future Recorded Future ASI API token'
        ):
            ASIClient(api_token=None)
    finally:
        Config.reset_instance()


def test_asi_client_init_uses_config_token_when_api_token_not_provided():
    config_token = 'b' * 32
    Config.reset_instance()
    Config.init(asi_token=config_token)

    try:
        client = ASIClient(api_token=None)
        assert client._api_token == config_token
    finally:
        Config.reset_instance()


def test_prepare_headers_with_token(asi_client, mocker):
    mocker.patch('psengine.base_http_client.OSHelpers.os_platform', return_value='Linux')
    mocker.patch('psengine.base_http_client.SDK_ID', 'SDK_ID')

    headers = asi_client._prepare_headers()

    assert headers == {
        'User-Agent': 'app_id unknown (Linux) SDK_ID platform_id unknown',
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'apikey': 'a' * 32,
    }


def test_prepare_headers_without_token_logs_warning(asi_client, mocker, caplog):
    mocker.patch('psengine.base_http_client.OSHelpers.os_platform', return_value='Linux')
    mocker.patch('psengine.base_http_client.SDK_ID', 'SDK_ID')
    asi_client._api_token = None

    with caplog.at_level(logging.WARNING, logger='psengine.base_http_client'):
        headers = asi_client._prepare_headers()

    assert headers == {
        'User-Agent': 'app_id unknown (Linux) SDK_ID platform_id unknown',
        'Content-Type': 'application/json',
        'accept': 'application/json',
    }
    assert 'Request being made with no Recorded Future ASI API key set' in caplog.text


def test_request_uses_prepare_headers_and_forwards_data_params_and_kwargs(asi_client, mocker):
    response = mocker.Mock(spec=Response)
    mock_headers = {'apikey': 'test-key'}
    prepare_headers_spy = mocker.patch.object(
        asi_client, '_prepare_headers', return_value=mock_headers
    )
    call_spy = mocker.patch.object(asi_client, 'call', return_value=response)

    result = asi_client.request(
        method='post',
        url='https://example.test/asi',
        data={'hello': 'world'},
        params={'limit': 10},
        timeout=33,
    )

    assert result == response
    prepare_headers_spy.assert_called_once_with()
    call_spy.assert_called_once_with(
        method='post',
        url='https://example.test/asi',
        headers=mock_headers,
        data={'hello': 'world'},
        params={'limit': 10},
        timeout=33,
    )


def test_request_uses_explicit_headers_and_skips_prepare_headers(asi_client, mocker):
    response = mocker.Mock(spec=Response)
    prepare_headers_spy = mocker.patch.object(asi_client, '_prepare_headers')
    call_spy = mocker.patch.object(asi_client, 'call', return_value=response)
    custom_headers = {'x-test': '1'}

    result = asi_client.request(
        method='get',
        url='https://example.test/asi',
        headers=custom_headers,
        params={'q': 'abc'},
    )

    assert result == response
    prepare_headers_spy.assert_not_called()
    call_spy.assert_called_once_with(
        method='get',
        url='https://example.test/asi',
        headers=custom_headers,
        data=None,
        params={'q': 'abc'},
    )

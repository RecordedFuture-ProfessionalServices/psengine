import re
from datetime import datetime
from glob import glob
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from requests import Response
from requests.exceptions import HTTPError

from psengine.detection import (
    DetectionMgr,
    DetectionRule,
    DetectionRuleFetchError,
    DetectionRuleSearchError,
)
from psengine.detection.helpers import save_rule
from psengine.endpoints import EP_DETECTION_RULES
from tests.detection.conftest import MOCK_DIR


def test_search_returns_model(detection_mgr: DetectionMgr, mocker, mock_request):
    mocks = [
        mock_request(MOCK_DIR / 'test_search_returns_model_0.json'),
        mock_request(MOCK_DIR / 'test_search_returns_model_1.json'),
    ]

    mocker.patch.object(detection_mgr.rf_client, 'request', side_effect=mocks)

    result = detection_mgr.search(detection_rule='yara', max_results=2)
    assert isinstance(result, list)
    assert all(isinstance(res, DetectionRule) for res in result)


@pytest.mark.parametrize('detections', ['yara', ['yara', 'sigma'], None])
def test_search_detection(detection_mgr: DetectionMgr, detections, mocker, mock_request, request):
    node_id = request.node.callspec.id
    pattern = re.compile(rf'^test_search_detection\[{re.escape(node_id)}\]_\d+\.json$')
    files = sorted(f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name))
    mocks = [mock_request(f) for f in files]
    mocker.patch.object(detection_mgr.rf_client, 'request', side_effect=mocks)

    result = detection_mgr.search(detection_rule=detections, max_results=2)
    assert isinstance(result, list)
    assert all(isinstance(res, DetectionRule) for res in result)


def test_spy_called_without_arguments(detection_mgr: DetectionMgr, mocker):
    mock_post_request = mocker.patch.object(
        detection_mgr.rf_client,
        'request_paged',
        return_value=MagicMock(json=lambda: {'result': []}),
    )
    detection_mgr.search()
    call_args, params = mock_post_request.call_args
    assert call_args[0] == 'post'
    assert call_args[1] == EP_DETECTION_RULES
    assert params == {
        'data': {'filter': {'created': {}, 'updated': {}}, 'limit': 100},
        'max_results': 10,
        'offset_key': 'offset',
        'results_path': 'result',
    }


def test_spy_called_with_rel_date(detection_mgr: DetectionMgr, mocker):
    mock_post_request = mocker.patch.object(
        detection_mgr.rf_client,
        'request_paged',
        return_value=MagicMock(json=lambda: {'result': []}),
    )
    detection_mgr.search(created_after='-7d')
    call_args, params = mock_post_request.call_args
    assert call_args[0] == 'post'
    assert call_args[1] == EP_DETECTION_RULES
    assert datetime.fromisoformat(params['data']['filter']['created']['after'])


def test_spy_called_pagination_argument(detection_mgr: DetectionMgr, mocker):
    mock_post_request = mocker.patch.object(
        detection_mgr.rf_client,
        'request_paged',
        return_value=MagicMock(json=lambda: {'result': []}),
    )
    detection_mgr.search()
    call_args, params = mock_post_request.call_args
    assert call_args[0] == 'post'
    assert call_args[1] == EP_DETECTION_RULES
    assert params == {
        'data': {'filter': {'created': {}, 'updated': {}}, 'limit': 100},
        'offset_key': 'offset',
        'results_path': 'result',
        'max_results': 10,
    }


timeranges = [
    {'created_before': '2022-03-10T00:00:00.000Z'},
    {'created_after': '2022-03-10T00:00:00.000Z'},
    {'updated_before': '2022-03-10T00:00:00.000Z'},
    {'updated_after': '2022-03-10T00:00:00.000Z'},
    {'created_before': '2022-03-10T00:00:00.000Z', 'updated_after': '2022-03-11T00:00:00.000Z'},
    {'updated_before': '2022-03-10T00:00:00.000Z', 'updated_after': '2022-03-11T00:00:00.000Z'},
]


@pytest.mark.parametrize('timeranges', timeranges)
def test_search_timeranges(detection_mgr: DetectionMgr, timeranges, mocker, mock_request, request):
    node_id = request.node.callspec.id
    pattern = re.compile(rf'^test_search_timeranges\[{re.escape(node_id)}\]_\d+\.json$')
    files = sorted(f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name))

    mocks = [mock_request(f) for f in files]

    mocker.patch.object(detection_mgr.rf_client, 'request', side_effect=mocks)
    result = detection_mgr.search(max_results=2, **timeranges)
    assert isinstance(result, list)
    assert all(isinstance(res, DetectionRule) for res in result)


def test_search_zero_results(detection_mgr: DetectionMgr, mocker, make_response):
    data = {'count': 0, 'total_count': 0, 'result': []}
    mock = make_response(data)
    mocker.patch.object(detection_mgr.rf_client, 'request', return_value=mock)

    result = detection_mgr.search(doc_id='doc:moise')
    assert result == []


def test_search_return_limited_detections(detection_mgr: DetectionMgr, mocker, mock_request):
    mocks = [
        mock_request(MOCK_DIR / 'test_search_return_limited_detections_0.json'),
        mock_request(MOCK_DIR / 'test_search_return_limited_detections_1.json'),
    ]

    mocker.patch.object(detection_mgr.rf_client, 'request', side_effect=mocks)

    result = detection_mgr.search(max_results=40)
    assert len(result) == 40


def test_search_return_all_detections_snort(detection_mgr: DetectionMgr, mocker, mock_request):
    mocks = [
        mock_request(MOCK_DIR / 'test_search_return_all_detections_snort_0.json'),
        mock_request(MOCK_DIR / 'test_search_return_all_detections_snort_1.json'),
    ]

    mocker.patch.object(detection_mgr.rf_client, 'request', side_effect=mocks)

    result = detection_mgr.search(detection_rule='snort', max_results=40)
    assert len(result) == 40


def test_search_raises_DetectionRuleSearchError(detection_mgr: DetectionMgr, mocker):
    mocker.patch.object(detection_mgr.rf_client, 'request', side_effect=HTTPError)
    with pytest.raises(DetectionRuleSearchError):
        detection_mgr.search()


@pytest.mark.parametrize(
    ('detection_id', 'expected_type'),
    [('doc:cynQie', DetectionRule), ('doc:moise', type(None))],
    ids=list(range(2)),
)
def test_fetch_return_expected_value(
    detection_mgr: DetectionMgr, detection_id, expected_type, mocker, mock_request, request
):
    node_id = request.node.callspec.id
    pattern = re.compile(rf'^test_fetch_return_expected_value\[{re.escape(node_id)}\]_\d+\.json$')
    files = sorted(f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name))
    mocks = [mock_request(f) for f in files]
    mocker.patch.object(detection_mgr.rf_client, 'request', side_effect=mocks)
    result = detection_mgr.fetch(doc_id=detection_id)
    assert isinstance(result, expected_type)


def test_fetch_raises_DetectionRuleFetchError(detection_mgr: DetectionMgr, mocker):
    response = Response()
    response.status_code = 500
    excp_obj = HTTPError('error')
    excp_obj.response = response
    mocker.patch.object(detection_mgr.rf_client, 'request', side_effect=excp_obj)

    with pytest.raises(DetectionRuleFetchError):
        detection_mgr.fetch('moise')


def test_write_rule_to_one_file(detection_mgr: DetectionMgr, tmp_path, mocker, mock_request):
    mocks = [
        mock_request(MOCK_DIR / 'test_write_rule_to_one_file_0.json'),
        mock_request(MOCK_DIR / 'test_write_rule_to_one_file_1.json'),
    ]

    mocker.patch.object(detection_mgr.rf_client, 'request', side_effect=mocks)

    result = detection_mgr.fetch(doc_id='doc:cynQie')
    save_rule(result, tmp_path)
    assert len(list(glob((tmp_path / '*').as_posix()))) == 1


def test_write_rule_without_file(tmp_path):
    data = {
        'id': 'doc:o6_lui',
        'type': 'sigma',
        'title': 'long title',
        'description': 'long description',
        'created': '2022-11-23T22:47:39.858Z',
        'updated': '2022-11-23T22:47:39.858Z',
        'rules': [
            {'entities': [], 'content': 'contentone', 'file_name': 'mal_aesthetic_wiper1.yml'},
            {'entities': [], 'content': 'contenttwo', 'file_name': 'mal_aesthetic_wiper2.yml'},
        ],
    }
    detection = DetectionRule(**data)
    save_rule(detection, tmp_path)
    g = list(glob((tmp_path / '*').as_posix()))
    assert len(g) == 2
    assert any(file.endswith('mal_aesthetic_wiper1.yml') for file in g)
    assert any(file.endswith('mal_aesthetic_wiper2.yml') for file in g)

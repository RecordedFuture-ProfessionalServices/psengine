from pathlib import Path

import pytest

from psengine.entity_lists import EntityList, EntityListMgr
from psengine.entity_match import EntityMatchMgr
from psengine.rf_client import RFClient

TEST_LIST_NAME = 'test-list-pls-ignore'
MOCK_DIR = Path(__file__).parent / 'mocks'


@pytest.fixture
def list_mgr():
    return EntityListMgr()


def list_obj():
    return EntityList()


@pytest.fixture
def fresh_list(mocker, make_response):
    rfclient = RFClient()
    match_mgr = EntityMatchMgr()
    body = {'name': TEST_LIST_NAME, 'type': 'custom'}
    mock = make_response(
        [
            {
                'id': 'report:5BjoI2',
                'name': 'test-list-pls-ignore',
                'type': 'entity',
                'created': '2025-04-07T10:13:02.044Z',
                'updated': '2025-04-07T10:22:45.725Z',
                'owner_id': 'uhash:6dCcPQn3uO',
                'owner_name': 'Connect & RAW - TESTING',
                'organisation_id': 'uhash:5zQaSyRpA1',
                'organisation_name': 'Professional Services Development',
                'owner_organisation_details': {
                    'owner_id': 'uhash:6dCcPQn3uO',
                    'owner_name': 'Connect & RAW - TESTING',
                    'organisations': [],
                    'enterprise_id': 'uhash:5zQaSyRpA1',
                    'enterprise_name': 'Professional Services Development',
                },
            }
        ]
    )
    mocker.patch.object(rfclient, 'request', return_value=mock)
    res = rfclient.request('post', 'https://api.recordedfuture.com/list/search', data=body)
    lists = list(filter(lambda x: x['name'] == TEST_LIST_NAME, res.json()))
    list_data = lists[0]

    return EntityList(rf_client=rfclient, match_mgr=match_mgr, **list_data)

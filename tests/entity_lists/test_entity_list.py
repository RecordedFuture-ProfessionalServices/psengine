import pytest
from requests import Response
from requests.models import HTTPError

from psengine.entity_lists import EntityList, EntityListMgr, ListApiError, ListEntity
from psengine.entity_match.errors import MatchApiError
from tests.entity_lists.conftest import MOCK_DIR

TEST_LIST = 'psengine-test-list-do-not-delete'
TEST_LIST_ID = 'report:oVuVZX'
EMPTY_LIST_NAME = 'psengine-test-empty-list-do-not-delete'
EMPTY_LIST_ID = 'report:xLSrTL'
TEST_LIST_TEXT_ENTRIES = 'psengine-test-list-text-entries-do-not-delete'
TEST_LIST_TEXT_ENTRIES_ID = '1oVnJy'

ADD_OP = 'add'
REMOVE_OP = 'remove'


class Test_List:
    def test_fetch_list(self, list_mgr: EntityListMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'test_fetch_list_0.json')

        mocker.patch.object(list_mgr.rf_client, 'request', return_value=mock)
        list_ = list_mgr.fetch(TEST_LIST_ID)

        assert isinstance(list_, EntityList) is True
        assert list_.id_ == TEST_LIST_ID
        assert list_.name == TEST_LIST
        assert list_.type_ == 'entity'
        assert list_.created is not None
        assert list_.updated is not None
        assert list_.organisation_id is not None
        assert list_.organisation_name is not None

    def test_info(self, list_mgr: EntityListMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_info_0.json'),
            mock_request(MOCK_DIR / 'test_info_1.json'),
            mock_request(MOCK_DIR / 'test_info_2.json'),
            mock_request(MOCK_DIR / 'test_info_3.json'),
        ]

        mocker.patch.object(list_mgr.rf_client, 'request', side_effect=mocks)

        list_ = list_mgr.fetch(TEST_LIST_ID)
        info = list_.info()
        assert info.id_ == TEST_LIST_ID
        assert info.name == TEST_LIST
        assert info.type_ == 'entity'
        assert info.created is not None
        assert info.updated is not None
        assert info.organisation_id is not None
        assert info.organisation_name is not None

        empty_list = list_mgr.fetch(EMPTY_LIST_ID)
        info = empty_list.info()
        assert info.id_ == EMPTY_LIST_ID
        assert info.name == EMPTY_LIST_NAME
        assert info.type_ == 'entity'
        assert info.created is not None
        assert info.updated is not None
        assert info.organisation_id is not None
        assert info.organisation_name is not None

    def test_status(self, list_mgr: EntityListMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_status_0.json'),
            mock_request(MOCK_DIR / 'test_status_1.json'),
        ]

        mocker.patch.object(list_mgr.rf_client, 'request', side_effect=mocks)

        list_ = list_mgr.fetch(TEST_LIST_ID)
        response = list_.status()
        assert response.status == 'ready'

    def test_entities(self, list_mgr: EntityListMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_entities_0.json'),
            mock_request(MOCK_DIR / 'test_entities_1.json'),
        ]

        mocker.patch.object(list_mgr.rf_client, 'request', side_effect=mocks)

        list_ = list_mgr.fetch(TEST_LIST_ID)
        entities = list_.entities()
        assert len(entities) == 10
        for entity in entities:
            assert isinstance(entity, ListEntity)

    def test_text_entries(self, list_mgr: EntityListMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_text_entries_0.json'),
            mock_request(MOCK_DIR / 'test_text_entries_1.json'),
        ]

        mocker.patch.object(list_mgr.rf_client, 'request', side_effect=mocks)

        list_ = list_mgr.fetch(TEST_LIST_TEXT_ENTRIES_ID)
        entries = list_.text_entries()
        assert len(entries) == 5
        for entry in entries:
            assert isinstance(entry, str)

    def test_entity_add(self, fresh_list, mocker, make_response):
        mocks = [
            make_response({'result': 'added'}),
            make_response({'result': 'unchanged'}),
            make_response({'result': 'added'}),
        ]
        mocker.patch.object(fresh_list.rf_client, 'request', side_effect=mocks)

        entity = 'ip:8.8.8.8'
        res = fresh_list.add(entity)
        assert res.result == 'added'
        res = fresh_list.add(entity)
        assert res.result == 'unchanged'

        res = fresh_list.add('ip:9.9.9.9', context={'number': 2})
        assert res.result == 'added'

    def test_invalid_entity_add(self, fresh_list, mocker):
        response = Response()
        response.status_code = 400
        excp_obj = HTTPError('error')
        excp_obj.response = response
        mocker.patch.object(fresh_list.rf_client, 'request', side_effect=excp_obj)

        with pytest.raises(ListApiError):
            fresh_list.add('ip:256.256.256.256')

    def test_entity_remove(self, fresh_list: EntityList, mocker, make_response):
        response = Response()
        response.status_code = 400
        excp_obj = HTTPError('error')
        excp_obj.response = response

        mocks = [
            make_response({'result': 'added'}),
            make_response(
                [
                    {
                        'entity': {
                            'id': 'ip:8.8.8.8',
                            'type': 'IpAddress',
                            'name': '8.8.8.8',
                        },
                        'status': 'added',
                        'added': '2025-07-21T15:11:18.069Z',
                    }
                ]
            ),
            make_response({'result': 'removed'}),
            make_response([]),
            make_response({'result': 'unchanged'}),
            excp_obj,
        ]
        mocker.patch.object(fresh_list.rf_client, 'request', side_effect=mocks)

        entity = 'ip:8.8.8.8'
        fresh_list.add(entity)
        entities = fresh_list.entities()
        assert len(entities) == 1
        res = fresh_list.remove(entity)
        entities = fresh_list.entities()
        assert len(entities) == 0
        assert res.result == 'removed'
        # Entity not in the list has result "unchanged"
        res = fresh_list.remove('ip:8.8.8.8')
        assert res.result == 'unchanged'

        # Entity that doesn't exist raises ListApiError
        with pytest.raises(ListApiError):
            fresh_list.remove('ip:256.256.256.256')

    def test_add_and_remove(self, list_mgr: EntityListMgr, mocker, mock_request, make_response):
        mocks = [
            make_response(
                {
                    'id': 'report:oVuVZX',
                    'name': 'psengine-test-list-do-not-delete',
                    'type': 'entity',
                    'created': '2022-10-14T02:51:46.478Z',
                    'updated': '2024-12-17T16:55:22.528Z',
                    'owner_id': 'uhash:1MXCEIeMbi',
                    'owner_name': 'User',
                    'organisation_id': 'uhash:5zQaSyRpA1',
                    'organisation_name': 'Professional Services Development',
                    'owner_organisation_details': {
                        'owner_id': 'uhash:1MXCEIeMbi',
                        'owner_name': 'User',
                        'organisations': [],
                        'enterprise_id': 'uhash:5zQaSyRpA1',
                        'enterprise_name': 'Professional Services Development',
                    },
                }
            ),
            mock_request(MOCK_DIR / 'test_add_and_remove_1.json'),
            make_response({'result': 'added'}),
            mock_request(MOCK_DIR / 'test_add_and_remove_3.json'),
            make_response({'result': 'removed'}),
            mock_request(MOCK_DIR / 'test_add_and_remove_5.json'),
        ]

        mocker.patch.object(list_mgr.rf_client, 'request', side_effect=mocks)

        list_ = list_mgr.fetch(TEST_LIST_ID)
        entities = list_.entities()
        original_length = len(entities)
        list_.add('ip:8.8.8.8')
        entities = list_.entities()
        assert len(entities) == original_length + 1
        list_.remove('ip:8.8.8.8')
        entities = list_.entities()
        assert len(entities) == original_length

    def test_bulk_op_MatchApiError(self, fresh_list: EntityList, mocker, make_response):
        mock = [make_response({'size': 0, 'status': 'ready'}), make_response([])]

        mocker.patch.object(fresh_list.rf_client, 'request', side_effect=mock)

        mocker.patch.object(
            fresh_list.match_mgr,
            'resolve_entity_id',
            side_effect=MatchApiError('Error from pytest'),
        )
        result = fresh_list.bulk_add([('8.8.8.8', 'IpAddress')])
        assert result == {
            'added': [],
            'error': [{'id': ('8.8.8.8', 'IpAddress'), 'message': 'Error from pytest'}],
            'unchanged': [],
        }

    def test_bulk_add_ips(self, fresh_list: EntityList, mocker, mock_request):
        mock = [mock_request(MOCK_DIR / f'test_bulk_add_ips_{x}.json') for x in range(1, 19)]
        entities = ['ip:8.8.8.8', 'ip:9.9.9.9', 'ip:10.10.10.10', 'ip:11.11.11.11']

        mocker.patch.object(fresh_list.rf_client, 'request', side_effect=mock)

        bulk_result = fresh_list.bulk_add(entities)
        assert 'added' in bulk_result
        assert 'unchanged' in bulk_result
        assert 'error' in bulk_result
        assert len(bulk_result['added']) == len(entities)

    def test_bulk_remove_domains(self, fresh_list: EntityList, mocker, mock_request):
        mock_1 = [
            mock_request(MOCK_DIR / f'test_bulk_remove_domains_{x}.json') for x in range(1, 5)
        ]
        mock_2 = [
            mock_request(MOCK_DIR / f'test_bulk_remove_domains_{x}.json') for x in range(6, 14)
        ]

        entities = ['idn:google.com', 'idn:facebook.com', 'idn:recordedfuture.com']

        mocker.patch.object(fresh_list.rf_client, 'request', side_effect=mock_1 + mock_2)

        bulk_result = fresh_list.bulk_add(entities)
        bulk_result = fresh_list.bulk_remove(entities)
        assert 'removed' in bulk_result
        assert 'unchanged' in bulk_result
        assert 'error' in bulk_result
        assert len(bulk_result['removed']) == len(entities)

        entities = fresh_list.entities()
        assert len(entities) == 0

        bulk_result = fresh_list.bulk_remove(entities)
        assert len(bulk_result['unchanged']) == len(entities)

    def test_str(self, list_mgr: EntityListMgr, mocker, make_response):
        mock = [
            make_response(
                {
                    'id': 'report:oVuVZX',
                    'name': 'psengine-test-list-do-not-delete',
                    'type': 'entity',
                    'created': '2022-10-14T02:51:46.478Z',
                    'updated': '2024-12-17T16:55:22.528Z',
                    'owner_id': 'uhash:1MXCEIeMbi',
                    'owner_name': 'User',
                    'organisation_id': 'uhash:5zQaSyRpA1',
                    'organisation_name': 'Professional Services Development',
                    'owner_organisation_details': {
                        'owner_id': 'uhash:1MXCEIeMbi',
                        'owner_name': 'User',
                        'organisations': [],
                        'enterprise_id': 'uhash:5zQaSyRpA1',
                        'enterprise_name': 'Professional Services Development',
                    },
                }
            ),
            make_response(
                {
                    'id': 'report:xLSrTL',
                    'name': 'psengine-test-empty-list-do-not-delete',
                    'type': 'entity',
                    'created': '2024-07-23T20:08:51.655Z',
                    'updated': '2025-07-15T08:11:43.792Z',
                    'owner_id': 'uhash:1MXCEIeMbi',
                    'owner_name': 'User',
                    'organisation_id': 'uhash:5zQaSyRpA1',
                    'organisation_name': 'Professional Services Development',
                    'owner_organisation_details': {
                        'owner_id': 'uhash:1MXCEIeMbi',
                        'owner_name': 'User',
                        'organisations': [],
                        'enterprise_id': 'uhash:5zQaSyRpA1',
                        'enterprise_name': 'Professional Services Development',
                    },
                }
            ),
        ]
        mocker.patch.object(list_mgr.rf_client, 'request', side_effect=mock)

        list_ = list_mgr.fetch(TEST_LIST_ID)
        list_str = str(list_)
        assert 'id:' in list_str
        assert 'name:' in list_str
        assert 'type:' in list_str
        assert 'created:' in list_str
        assert 'last updated:' in list_str
        assert 'organisation id:' in list_str
        assert 'organisation name:' in list_str

        list_ = list_mgr.fetch(EMPTY_LIST_ID)
        list_str = str(list_)
        assert 'id:' in list_str
        assert 'name:' in list_str
        assert 'type:' in list_str
        assert 'created:' in list_str
        assert 'last updated:' in list_str
        assert 'organisation id:' in list_str
        assert 'organisation name:' in list_str

    def test_json(self, list_mgr: EntityListMgr, mocker, mock_request):
        mock = [mock_request(MOCK_DIR / f'test_json_{x}.json') for x in range(2)]
        mocker.patch.object(list_mgr.rf_client, 'request', side_effect=mock)

        list_ = list_mgr.fetch(TEST_LIST_ID)
        json = list_.json()
        assert 'id' in json
        assert 'name' in json
        assert 'type' in json
        assert 'created' in json
        assert 'updated' in json
        assert 'organisation_id' in json
        assert 'organisation_name' in json
        assert 'owner_id' in json
        assert 'owner_name' in json
        assert 'owner_organisation_details' in json
        assert 'rf_client' not in json
        assert 'match_mgr' not in json
        assert 'log' not in json

import pytest
from pydantic import ValidationError
from requests import Response
from requests.models import HTTPError

from psengine.endpoints import EP_LIST_ENTITIES_WITH_TAGS, EP_LIST_ENTITY_TAGS
from tests.conftest import validation_match
from psengine.entity_lists import (
    EntityList,
    EntityListMgr,
    EntityNotResolvedOperation,
    ListApiError,
    ListEntity,
    ListEntityTag,
    ListEntityWithTags,
    ListTagName,
    ReplaceEntityTagsOut,
    TagsUnchangedOperation,
    TagsUpdatedOperation,
)
from psengine.entity_match.errors import MatchApiError
from tests.entity_lists.conftest import MOCK_DIR

TEST_LIST = 'psengine-test-list-do-not-delete'
TEST_LIST_ID = 'report:oVuVZX'
EMPTY_LIST_NAME = 'psengine-test-empty-list-do-not-delete'
EMPTY_LIST_ID = 'report:xLSrTL'
TEST_LIST_TEXT_ENTRIES = 'psengine-test-list-text-entries-do-not-delete'
TEST_LIST_TEXT_ENTRIES_ID = '1oVnJy'
TEST_COMPANY_LIST_ID = 'report:FNESDXu2WZ4'

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

    def test_entities_with_tags(self, list_mgr: EntityListMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_entities_with_tags_0.json'),
            mock_request(MOCK_DIR / 'test_entities_with_tags_1.json'),
        ]

        request = mocker.patch.object(list_mgr.rf_client, 'request', side_effect=mocks)

        list_ = list_mgr.fetch(TEST_COMPANY_LIST_ID)
        entities = list_.entities_with_tags()

        verb, url = request.call_args.args
        assert verb == 'get'
        assert url == EP_LIST_ENTITIES_WITH_TAGS.format(TEST_COMPANY_LIST_ID)
        assert url.endswith(f'/list/{TEST_COMPANY_LIST_ID}/entitiesWithTags')

        assert len(entities) == 3
        for entity in entities:
            assert isinstance(entity, ListEntityWithTags)
            assert isinstance(entity, ListEntity)
            assert all(isinstance(tag, ListEntityTag) for tag in entity.tags)

        tagged, with_context, untagged = entities

        assert tagged.entity.id_ == 'FNESDXsdSEM'
        assert tagged.entity.type_ == 'Company'
        assert tagged.entity.name == 'Northwind Components AB'
        assert tagged.status == 'ready'
        assert tagged.added is not None
        assert tagged.context is None
        assert [tag.name for tag in tagged.tags] == ['tier1', 'critical', 'financial']
        assert [tag.id_ for tag in tagged.tags] == [
            'enum:EntityListTag:tier1',
            'enum:EntityListTag:critical',
            'enum:EntityListTag:financial',
        ]

        assert with_context.context == {'onboarding_ticket': 'TPR-4821'}
        assert with_context.status == 'pending'
        assert [tag.name for tag in with_context.tags] == ['most_critical_supplier']

        assert untagged.tags == []

    def test_entities_validation_error_names_entity(
        self, fresh_list: EntityList, mocker, make_response
    ):
        good = {
            'entity': {'id': 'ip:8.8.8.8', 'type': 'IpAddress', 'name': '8.8.8.8'},
            'status': 'ready',
            'added': '2026-07-21T15:11:18.069Z',
        }
        bad = {
            'entity': {'id': 'ip:1.1.1.1', 'type': 'IpAddress', 'name': 'broken-ip'},
            'status': 'ready',
        }
        mocker.patch.object(
            fresh_list.rf_client, 'request', return_value=make_response([good, bad, good])
        )
        with pytest.raises(ValidationError, match=validation_match('entity.name=broken-ip')):
            fresh_list.entities()

    def test_entities_with_tags_validation_error_names_entity(
        self, fresh_list: EntityList, mocker, make_response
    ):
        good = {
            'entity': {'id': 'ip:8.8.8.8', 'type': 'IpAddress', 'name': '8.8.8.8'},
            'status': 'ready',
            'added': '2026-07-21T15:11:18.069Z',
            'tags': [],
        }
        bad = {
            'entity': {'id': 'ip:1.1.1.1', 'type': 'IpAddress', 'name': 'broken-ip'},
            'status': 'ready',
            'tags': [],
        }
        mocker.patch.object(
            fresh_list.rf_client, 'request', return_value=make_response([good, bad, good])
        )
        with pytest.raises(ValidationError, match=validation_match('entity.name=broken-ip')):
            fresh_list.entities_with_tags()

    def test_entities_with_tags_no_tags_key(self, fresh_list: EntityList, mocker, make_response):
        mock = make_response(
            [
                {
                    'entity': {'id': 'ip:8.8.8.8', 'type': 'IpAddress', 'name': '8.8.8.8'},
                    'status': 'ready',
                    'added': '2026-07-21T15:11:18.069Z',
                }
            ]
        )
        mocker.patch.object(fresh_list.rf_client, 'request', return_value=mock)

        entities = fresh_list.entities_with_tags()
        assert len(entities) == 1
        assert entities[0].tags == []

    @pytest.mark.parametrize('status_code', [400, 404])
    def test_entities_with_tags_api_error(self, fresh_list: EntityList, mocker, status_code):
        response = Response()
        response.status_code = status_code
        excp_obj = HTTPError('error')
        excp_obj.response = response
        mocker.patch.object(fresh_list.rf_client, 'request', side_effect=excp_obj)

        with pytest.raises(ListApiError):
            fresh_list.entities_with_tags()

    def test_update_entity_tags_updated(self, fresh_list: EntityList, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'test_update_entity_tags_updated.json')
        request = mocker.patch.object(fresh_list.rf_client, 'request', return_value=mock)

        res = fresh_list.update_entity_tags('B_tZu', ['tier1', 'critical'])

        verb, url = request.call_args.args
        assert verb == 'post'
        assert url == EP_LIST_ENTITY_TAGS.format(fresh_list.id_)
        assert url.endswith(f'/list/{fresh_list.id_}/entity/tags')
        assert request.call_args.kwargs['data'] == {
            'entity': {'id': 'B_tZu'},
            'tags': ['tier1', 'critical'],
        }

        assert isinstance(res, ReplaceEntityTagsOut)
        assert res.entity_id == 'B_tZu'
        assert isinstance(res.operation, TagsUpdatedOperation)
        assert res.operation.tags_before == ['tier1', 'critical', 'financial']
        assert res.operation.tags_after == ['tier1', 'critical']
        assert res.operation.tags_added == []
        assert res.operation.tags_removed == ['financial']
        assert res.operation.updated is not None
        assert res.changed is True
        assert res.current_tags == ['tier1', 'critical']

    def test_update_entity_tags_unchanged(self, fresh_list: EntityList, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'test_update_entity_tags_unchanged.json')
        mocker.patch.object(fresh_list.rf_client, 'request', return_value=mock)

        res = fresh_list.update_entity_tags('B_tZu', ['tier1', 'critical', 'financial'])

        assert isinstance(res.operation, TagsUnchangedOperation)
        assert res.operation.current_tags == ['tier1', 'critical', 'financial']
        assert res.operation.message == 'Tags are already set to the requested values'
        assert res.changed is False
        assert res.current_tags == ['tier1', 'critical', 'financial']

    def test_update_entity_tags_accepts_enum(self, fresh_list: EntityList, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'test_update_entity_tags_updated.json')
        request = mocker.patch.object(fresh_list.rf_client, 'request', return_value=mock)

        fresh_list.update_entity_tags('B_tZu', [ListTagName.TIER1, ListTagName.CRITICAL])

        assert request.call_args.kwargs['data']['tags'] == ['tier1', 'critical']

    def test_update_entity_tags_clears_all(self, fresh_list: EntityList, mocker, make_response):
        mock = make_response(
            {
                'entity_id': 'B_tZu',
                'operation': {
                    'status': 'tags_updated',
                    'tags_before': ['tier1'],
                    'tags_after': [],
                    'tags_added': [],
                    'tags_removed': ['tier1'],
                    'updated': '2026-07-27T23:43:57.834Z',
                },
            }
        )
        request = mocker.patch.object(fresh_list.rf_client, 'request', return_value=mock)

        res = fresh_list.update_entity_tags('B_tZu', [])

        assert request.call_args.kwargs['data']['tags'] == []
        assert res.current_tags == []
        assert res.changed is True

    def test_update_entity_tags_by_name_and_type(
        self, fresh_list: EntityList, mocker, mock_request
    ):
        mock = mock_request(MOCK_DIR / 'test_update_entity_tags_updated.json')
        request = mocker.patch.object(fresh_list.rf_client, 'request', return_value=mock)
        mocker.patch.object(
            fresh_list.match_mgr,
            'resolve_entity_id',
            return_value=mocker.Mock(is_found=True, content=mocker.Mock(id_='B_tZu')),
        )

        res = fresh_list.update_entity_tags(('Sophos', 'Company'), ['tier1', 'critical'])

        assert request.call_args.kwargs['data']['entity'] == {'id': 'B_tZu'}
        assert res.changed is True

    def test_update_entity_tags_unresolvable_entity(self, fresh_list: EntityList, mocker):
        request = mocker.patch.object(fresh_list.rf_client, 'request')
        mocker.patch.object(
            fresh_list.match_mgr,
            'resolve_entity_id',
            return_value=mocker.Mock(is_found=False, content='No entity found'),
        )

        res = fresh_list.update_entity_tags(('Nope Ltd', 'Company'), ['tier1'])

        request.assert_not_called()
        assert isinstance(res.operation, EntityNotResolvedOperation)
        assert res.operation.message == 'No entity found'
        assert res.entity_id is None
        assert res.changed is False
        assert res.current_tags is None

    @pytest.mark.parametrize('status_code', [400, 403, 404])
    def test_update_entity_tags_api_error(self, fresh_list: EntityList, mocker, status_code):
        response = Response()
        response.status_code = status_code
        excp_obj = HTTPError('error')
        excp_obj.response = response
        mocker.patch.object(fresh_list.rf_client, 'request', side_effect=excp_obj)

        with pytest.raises(ListApiError):
            fresh_list.update_entity_tags('B_tZu', ['tier1'])

    def test_update_entity_tags_unknown_status_raises(self, fresh_list: EntityList, mocker):
        mock = mocker.Mock()
        mock.json.return_value = {
            'entity_id': 'B_tZu',
            'operation': {'status': 'tags_exploded', 'message': 'what'},
        }
        mocker.patch.object(fresh_list.rf_client, 'request', return_value=mock)

        with pytest.raises(ValidationError):
            fresh_list.update_entity_tags('B_tZu', ['tier1'])

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

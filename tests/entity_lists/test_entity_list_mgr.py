import pytest
from pydantic_core import ValidationError
from requests import HTTPError, Response

from psengine.entity_lists import EntityListMgr, ListApiError, ListResolutionError
from tests.entity_lists.conftest import MOCK_DIR

TEST_LIST_NAME = 'psengine-test-list-mgr-do-not-delete'


class Test_ListMgr:
    def test_list_create(self, list_mgr: EntityListMgr, mocker, mock_request):
        mock = [mock_request(MOCK_DIR / f'test_list_create_{x}.json') for x in range(2)]
        mocker.patch.object(list_mgr.rf_client, 'request', side_effect=mock)

        list_ = list_mgr.create(TEST_LIST_NAME, list_type='entity')
        assert list_.name == TEST_LIST_NAME
        assert list_.id_ is not None
        assert list_.type_ == 'entity'
        assert list_.created is not None
        assert list_.updated is not None
        assert list_.organisation_id is not None
        assert list_.organisation_name is not None

        with pytest.raises(ListApiError):
            list_mgr.create(TEST_LIST_NAME, list_type='not_a_list_type')

    def test_search_lists_all(self, list_mgr: EntityListMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'test_search_lists_all_0.json')
        mocker.patch.object(list_mgr.rf_client, 'request', return_value=mock)

        name = TEST_LIST_NAME
        response = list_mgr.search(name)
        results = [name in x.name for x in response]
        assert all(results)

    def test_search_list_entity_type(self, list_mgr: EntityListMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'test_search_list_entity_type_0.json')
        mocker.patch.object(list_mgr.rf_client, 'request', return_value=mock)

        response = list_mgr.search(TEST_LIST_NAME, list_type='entity')
        assert len(response) == 1
        assert response[0].name == TEST_LIST_NAME

    def test_search_list_entity_raise_ListAPIError(self, list_mgr: EntityListMgr, mocker):
        response = Response()
        response.status_code = 400
        excp_obj = HTTPError('error')
        excp_obj.response = response

        mocker.patch.object(list_mgr.rf_client, 'request', side_effect=excp_obj)

        with pytest.raises(ListApiError):
            list_mgr.search(TEST_LIST_NAME, list_type='not_a_list_type')

    def test_search_list_without_name(self, list_mgr: EntityListMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'test_search_list_without_name_0.json')
        mocker.patch.object(list_mgr.rf_client, 'request', return_value=mock)

        response = list_mgr.search(list_type='entity', max_results=1)
        assert len(response) == 1

    def test_fetch_list_with_similar_names(self, list_mgr: EntityListMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_fetch_list_with_similar_names_0.json'),
            mock_request(MOCK_DIR / 'test_fetch_list_with_similar_names_1.json'),
        ]
        mocker.patch.object(list_mgr.rf_client, 'request', side_effect=mocks)

        data = list_mgr.fetch(('psengine-test-list', 'entity'))
        assert data.id_ == 'report:vJYLm8'

    def test_fetch_list_by_name_and_type(self, list_mgr: EntityListMgr, mocker, mock_request):
        response = Response()
        response.status_code = 400
        excp_obj = HTTPError('error')
        excp_obj.response = response
        mocks = [
            mock_request(MOCK_DIR / 'test_fetch_list_by_name_and_type_0.json'),
            mock_request(MOCK_DIR / 'test_fetch_list_by_name_and_type_1.json'),
            mock_request(MOCK_DIR / 'test_fetch_list_by_name_and_type_2.json'),
            mock_request(MOCK_DIR / 'test_fetch_list_by_name_and_type_3.json'),
            mock_request(MOCK_DIR / 'test_fetch_list_by_name_and_type_4.json'),
            excp_obj,
        ]
        mocker.patch.object(list_mgr.rf_client, 'request', side_effect=mocks)

        entity_list = list_mgr.fetch(('Dan.me: Tor Nodelist', 'entity'))
        assert entity_list.id_ == 'report:OchJ-r'
        with pytest.raises(ListResolutionError):
            list_mgr.fetch(('bad-id', 'entity'))
        with pytest.raises(ListResolutionError):
            list_mgr.fetch(('duplicate', 'entity'))
        with pytest.raises(ListResolutionError):
            list_mgr.fetch(('DShield', 'entity'))
        with pytest.raises(ListApiError):
            list_mgr.fetch(('DShield', 'not_a_type'))
        with pytest.raises(ValidationError):
            list_mgr.fetch(('DShield', 'entity', 'too_long'))

    def test_fetch_list_by_id(self, list_mgr: EntityListMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'test_fetch_list_by_id_0.json')
        mocker.patch.object(list_mgr.rf_client, 'request', return_value=mock)

        rflist = list_mgr.fetch('report:OchJ-r')
        assert rflist.name == 'Dan.me: Tor Nodelist'
        with pytest.raises(ValidationError):
            list_mgr.fetch(6)

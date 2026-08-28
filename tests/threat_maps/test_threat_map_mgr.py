import json

import pytest
from pydantic import ValidationError

from psengine.threat_maps import (
    EntityCategory,
    ThreatActorProfile,
    ThreatMap,
    ThreatMapInfo,
    ThreatMapMgr,
)
from tests.conftest import validation_match
from tests.threat_maps.conftest import MOCK_DIR


class Test_ThreatMapMgr:
    def test_mgr(self, threat_map_mgr: ThreatMapMgr):
        assert isinstance(threat_map_mgr, ThreatMapMgr)

    def test_fetch_available_maps(self, threat_map_mgr: ThreatMapMgr, mocker):
        json_path = MOCK_DIR / 'test_fetch_available_maps.json'
        with open(json_path) as f:
            file_data = json.load(f)
        mocker.patch.object(
            threat_map_mgr.rf_client, 'request', return_value=mocker.Mock(json=lambda: file_data)
        )

        available_maps = threat_map_mgr.fetch_available_maps()
        sample_map = available_maps[0]
        assert isinstance(available_maps, list)
        assert isinstance(sample_map, ThreatMapInfo)

    @pytest.mark.parametrize(
        'map_type',
        ['actors', 'malware'],
    )
    def test_fetch_entity_categories(self, threat_map_mgr: ThreatMapMgr, map_type, mocker):
        json_path = MOCK_DIR / 'test_fetch_categories.json'
        with open(json_path) as f:
            file_data = json.load(f)
        mocker.patch.object(
            threat_map_mgr.rf_client, 'request', return_value=mocker.Mock(json=lambda: file_data)
        )

        categories = threat_map_mgr.fetch_entity_categories(map_type=map_type)
        category = categories[0]
        assert isinstance(categories, list)
        assert isinstance(category, EntityCategory)

    @pytest.mark.parametrize(
        'name',
        ['actor', None],
    )
    @pytest.mark.parametrize(
        'max_results',
        [1, 10000, None],
    )
    def test_search_threat_actor(self, threat_map_mgr: ThreatMapMgr, name, max_results, mocker):
        json_path = MOCK_DIR / 'test_search_threat_actors.json'
        with open(json_path) as f:
            file_data = json.load(f)
        mock_records = file_data.get('data', [])
        mocker.patch.object(
            threat_map_mgr.rf_client,
            'request_paged',
            side_effect=lambda *args, **kwargs: iter(mock_records),  # noqa: ARG005
        )

        actors = threat_map_mgr.search_threat_actor(name=name, max_results=max_results)
        actor = actors[0]
        assert isinstance(actor, ThreatActorProfile)

    def test_fetch_available_maps_validation_error_names_entity(
        self, threat_map_mgr: ThreatMapMgr, mocker, make_response
    ):
        good = {
            'name': 'goodMap',
            'type': 'actors',
            'organization': {'id': 'org:1', 'name': 'RF'},
            'url': 'https://x',
        }
        bad = {**good, 'name': 'brokenMap'}
        del bad['organization']
        mocker.patch.object(
            threat_map_mgr.rf_client, 'request', return_value=make_response({'data': [good, bad]})
        )
        with pytest.raises(ValidationError, match=validation_match('name=brokenMap')):
            threat_map_mgr.fetch_available_maps()

    def test_fetch_entity_categories_validation_error_names_entity(
        self, threat_map_mgr: ThreatMapMgr, mocker, make_response
    ):
        with open(MOCK_DIR / 'test_fetch_categories.json') as f:
            file_data = json.load(f)
        good = file_data['data'][0]
        bad = {**good, 'id': 'broken-cat-id'}
        del bad['attributes']
        mocker.patch.object(
            threat_map_mgr.rf_client, 'request', return_value=make_response({'data': [good, bad]})
        )
        with pytest.raises(ValidationError, match=validation_match('id=broken-cat-id')):
            threat_map_mgr.fetch_entity_categories(map_type='actors')

    def test_search_threat_actor_validation_error_names_entity(
        self, threat_map_mgr: ThreatMapMgr, mocker
    ):
        with open(MOCK_DIR / 'test_search_threat_actors.json') as f:
            file_data = json.load(f)
        good = file_data['data'][0]
        bad = {**good, 'id': 'broken-actor-id'}
        del bad['attributes']
        mocker.patch.object(
            threat_map_mgr.rf_client,
            'request_paged',
            side_effect=lambda *args, **kwargs: iter([good, bad]),  # noqa: ARG005
        )
        with pytest.raises(ValidationError, match=validation_match('id=broken-actor-id')):
            threat_map_mgr.search_threat_actor(name='actor')

    @pytest.mark.parametrize(
        'map_type',
        ['actors', 'malware'],
    )
    def test_fetch_map(self, threat_map_mgr: ThreatMapMgr, map_type, mocker, mock_request):
        mocks = [mock_request(MOCK_DIR / f'test_validate_threat_map_{map_type}.json')]
        mocker.patch.object(threat_map_mgr.rf_client, 'request', side_effect=mocks)

        threat_map = threat_map_mgr.fetch_map(map_type=map_type)
        assert isinstance(threat_map, ThreatMap)

    @pytest.mark.parametrize(
        'map_type',
        ['actors', 'malware'],
    )
    @pytest.mark.parametrize(
        'org_id',
        ['uhash:36sKPnfRQsl', 'uhash:69sKLfTGsS'],
    )
    def test_fetch_map_org_id(
        self, threat_map_mgr: ThreatMapMgr, map_type, org_id, mocker, mock_request
    ):
        mocks = [mock_request(MOCK_DIR / f'test_validate_threat_map_{map_type}.json')]
        mocker.patch.object(threat_map_mgr.rf_client, 'request', side_effect=mocks)

        threat_map = threat_map_mgr.fetch_map(map_type=map_type, org_id=org_id)
        assert isinstance(threat_map, ThreatMap)

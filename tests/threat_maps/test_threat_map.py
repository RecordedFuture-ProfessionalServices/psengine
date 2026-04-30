from datetime import datetime

import pytest

from psengine.threat_maps import (
    EntityCategory,
    ThreatActorProfile,
    ThreatMap,
    ThreatMapEntity,
    ThreatMapFetchIn,
    ThreatMapInfo,
    ThreatMapMgr,
)
from psengine.threat_maps.models import ThreatMapType
from tests.threat_maps.conftest import MOCK_DIR


class Test_ThreatMap_Models:
    @pytest.mark.parametrize(
        'map_type',
        ['actors', 'malware'],
    )
    def test_validate_threat_maps(
        self, threat_map_mgr: ThreatMapMgr, map_type, mocker, mock_request
    ):
        mocks = [mock_request(MOCK_DIR / f'test_validate_threat_map_{map_type}.json')]
        mocker.patch.object(threat_map_mgr.rf_client, 'request', side_effect=mocks)

        threat_map = threat_map_mgr.fetch_map(map_type=map_type)
        ThreatMap.model_validate(threat_map)

    def test_validate_threat_map_info(self):
        payload = {
            'name': 'name',
            'type': 'actor',
            'organization': {
                'id': 'org_id',
                'name': 'org_name',
            },
            'url': 'https://example.com/threat-maps',
        }
        ThreatMapInfo.model_validate(payload)

    def test_validate_threat_map_equality(self):
        actor = {
            'id': 'ta-entity-id',
            'name': 'ta-name',
            'alias': ['alias'],
            'categories': [{'id': 'id', 'name': 'name'}],
            'opportunity': 0,
            'intent': 0,
            'log_entries': [
                {
                    'entity': {'id': 'id', 'name': 'name'},
                    'severity': 0,
                    'axis': 'axis',
                    'date': datetime.now(),
                }
            ],
        }
        actor = ThreatMapEntity.model_validate(actor)
        actor_twin = ThreatMapEntity.model_validate(actor)
        malware = {
            'id': 'malware-entity-id',
            'name': 'malware-name',
            'alias': ['alias'],
            'categories': [{'id': 'id', 'name': 'name'}],
            'opportunity': 0,
            'prevalence': 0,
            'log_entries': [
                {
                    'entity': {'id': 'id', 'name': 'name'},
                    'severity': 0,
                    'axis': 'axis',
                    'date': datetime.now(),
                }
            ],
        }
        malware = ThreatMapEntity.model_validate(malware)
        malware_twin = ThreatMapEntity.model_validate(malware)

        assert actor == actor_twin
        assert malware == malware_twin
        assert malware != actor
        assert hash(actor) == hash(actor_twin)
        assert hash(malware) == hash(malware_twin)
        entities = [actor, malware, actor_twin, malware_twin]
        assert set(entities) == {actor, malware}

    entity_attributes = [{'name': 'name', 'alias': ['alias']}]

    @pytest.mark.parametrize('id_', ['id'])
    @pytest.mark.parametrize('type_', ['type'])
    @pytest.mark.parametrize('attributes', entity_attributes)
    def test_validate_entity_category(self, id_, type_, attributes):
        payload = {
            'id': id_,
            'type': type_,
            'attributes': attributes,
        }
        EntityCategory.model_validate(payload)

    ta_attributes = [
        {
            'name': 'name',
            'common_names': ['name'],
            'alias': ['alias'],
            'categories': [{'id': 'id', 'name': 'name'}],
        },
    ]

    @pytest.mark.parametrize('id_', ['id'])
    @pytest.mark.parametrize('type_', ['type'])
    @pytest.mark.parametrize('attributes', ta_attributes)
    def test_validate_threat_actor_profile(self, id_, type_, attributes):
        payload = {
            'id': id_,
            'type': type_,
            'attributes': attributes,
        }
        ThreatActorProfile.model_validate(payload)

    @pytest.mark.parametrize('malware', [['id'], None])
    @pytest.mark.parametrize('actors', [['id'], None])
    @pytest.mark.parametrize('categories', [['id'], None])
    @pytest.mark.parametrize('watchlists', [['id'], None])
    def test_validate_threat_map_fetch(self, malware, actors, categories, watchlists):
        payload = {
            'malware': malware,
            'actors': actors,
            'categories': categories,
            'watchlists': watchlists,
        }

        ThreatMapFetchIn.model_validate(payload)

    params = [
        ('actors', 'actor'),
        ('malware', 'malware'),
    ]

    @pytest.mark.parametrize(('key', 'expected'), params)
    def test_threat_map_type_slug(self, key, expected):
        map_type = ThreatMapType(key)
        assert map_type.category_slug == expected

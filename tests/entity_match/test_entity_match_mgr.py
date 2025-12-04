from collections import Counter

import pytest
from pydantic import ValidationError
from requests import HTTPError

from psengine.common_models import IdNameType
from psengine.entity_match import (
    EntityMatchMgr,
    MatchApiError,
    ResolvedEntity,
)
from psengine.entity_match.entity_match import EntityLookup


class Test_EntityMatchMgr:
    def test_match(self, match_mgr: EntityMatchMgr, mocker, make_response):
        mock = make_response([{'id': 'ip:8.8.8.8', 'name': '8.8.8.8', 'type': 'IpAddress'}])
        mocker.patch.object(match_mgr.rf_client, 'request', return_value=mock)
        name = '8.8.8.8'
        type_ = 'IpAddress'
        response = match_mgr.match(name, type_)
        results = [name in x.entity for x in response]
        assert all(results)
        assert all(isinstance(r.content, IdNameType) for r in response)
        assert all(isinstance(r, ResolvedEntity) for r in response)
        assert isinstance(response, list)

    def test_match_no_type(self, match_mgr: EntityMatchMgr, mocker, make_response):
        mock = make_response(
            [
                {'id': 'uky6Pe', 'name': '8.8.8.8', 'type': 'Username'},
                {'id': 'ip:8.8.8.8', 'name': '8.8.8.8', 'type': 'IpAddress'},
                {'id': 'U6CAbz', 'name': 'Google 8.8.8.8', 'type': 'Product'},
                {'id': 'JlfBB1', 'name': 'IP 8.8.8.8', 'type': 'IndustryTerm'},
            ]
        )
        mocker.patch.object(match_mgr.rf_client, 'request', return_value=mock)
        name = '8.8.8.8'
        response = match_mgr.match(name)
        results = [name in x.entity for x in response]
        assert all(results)

    def test_match_raises_MatchApiError(self, match_mgr: EntityMatchMgr, mocker):
        mocker.patch.object(match_mgr.rf_client, 'request', side_effect=HTTPError)
        with pytest.raises(MatchApiError):
            match_mgr.match('8.8.8.8')

    def test_resolve_entity_ids(self, match_mgr: EntityMatchMgr, mocker, make_response):
        entitylist = [
            ('RedGolf', 'Organization'),
            ('RedDelta', 'Organization'),
            ('WannaCry 1.0', 'Malware'),
        ]
        mocks = [
            make_response([{'id': 'I60vfZ', 'name': 'RedGolf', 'type': 'Organization'}]),
            make_response([{'id': 'en_T6N', 'name': 'RedDelta', 'type': 'Organization'}]),
            make_response([{'id': 'TzghRB', 'name': 'WannaCry 1.0', 'type': 'Malware'}]),
        ]

        mocker.patch.object(match_mgr.rf_client, 'request', side_effect=mocks)
        results = match_mgr.resolve_entity_ids(entitylist)
        ids_by_name = {r.content.name: r.content.id_ for r in results}

        assert isinstance(results, list)
        assert all(isinstance(r, ResolvedEntity) for r in results)
        assert len(results) == 3
        assert ids_by_name == {
            'RedGolf': 'I60vfZ',
            'RedDelta': 'en_T6N',
            'WannaCry 1.0': 'TzghRB',
        }

    def test_resolve_entity_ids_str(self, match_mgr: EntityMatchMgr, mocker, make_response):
        mock = make_response(
            [
                {'id': 'en_T6N', 'name': 'RedDelta', 'type': 'Organization'},
                {'id': 'gMN8_P', 'name': 'RedDelta PlugX', 'type': 'Malware'},
                {'id': 'doc:7bsdtw', 'name': 'RedDelta test', 'type': 'Document'},
            ]
        )
        mocker.patch.object(match_mgr.rf_client, 'request', return_value=mock)

        result = match_mgr.resolve_entity_ids(['RedDelta'])
        assert isinstance(result, list)
        assert isinstance(result[0], ResolvedEntity)
        assert result[0].content.id_ == 'en_T6N'

    @pytest.mark.parametrize('values', [1, 'a', [1, 2, 3], (1,), [('a', 'b', 'c'), ('a', 'b')]])
    def test_resolve_entity_ids_raises_ValidationError(self, match_mgr: EntityMatchMgr, values):
        with pytest.raises(ValidationError):
            match_mgr.resolve_entity_ids(values)

    def test_resolve_entity_ids_propagates_MatchApiError(self, match_mgr: EntityMatchMgr, mocker):
        mocker.patch.object(match_mgr, 'resolve_entity_id', side_effect=MatchApiError('something'))
        with pytest.raises(MatchApiError):
            match_mgr.resolve_entity_ids(['RedDelta'])

    # Following entities do not exist in Recorded Future
    data = [
        ('asdgohadgfiuhgfsakugfaiufga', 'Malware', []),
        ('1.1.1.1', 'Malware', []),
        (
            'wannacry',
            None,
            [
                {'id': 'SoA6SP', 'name': 'Wcry', 'type': 'Malware'},
                {'id': 'TPJbPF', 'name': 'wannacry', 'type': 'IndustryTerm'},
                {'id': 'Ub_GAO', 'name': 'wannacry', 'type': 'Username'},
                {'id': 'Ub_GA1', 'name': 'wannacry', 'type': 'Malware'},
            ],
        ),
        ('L37nw-', 'Malware', []),
    ]

    @pytest.mark.parametrize(('entity_name', 'entity_type', 'return_value'), data)
    def test_resolve_entity_id_with_no_exact_match(
        self, match_mgr, entity_name, entity_type, return_value, mocker, make_response
    ):
        mock = make_response(return_value)
        mocker.patch.object(match_mgr.rf_client, 'request', return_value=mock)

        resolved_entity = match_mgr.resolve_entity_id(entity_name, entity_type)
        assert isinstance(resolved_entity.content, str)
        assert resolved_entity.is_found is False

    def test_resolve_entity_id_works(self, match_mgr: EntityMatchMgr, mocker, make_response):
        mock = make_response([{'id': 'L37nw-', 'name': 'BlueDelta', 'type': 'Organization'}])
        mocker.patch.object(match_mgr.rf_client, 'request', return_value=mock)

        d = match_mgr.resolve_entity_id('BlueDelta', 'Organization')
        assert isinstance(d, ResolvedEntity)
        assert d.is_found is True
        assert d.entity == 'BlueDelta'
        assert d.content.id_ == 'L37nw-'

    def test_lookup_works(self, match_mgr: EntityMatchMgr, mocker, make_response):
        data = {
            'data': {
                'id': 'L37nw-',
                'type': 'Organization',
                'attributes': {
                    'name': 'BlueDelta',
                    'common_names': ['Strontium', 'Iron Twilight'],
                    'alias': ['apt28 (pawn storm tsar team)', 'Fancy Bear', 'Fancy Bears'],
                    'is_threat_actor': True,
                },
            }
        }
        mock = make_response(data)
        mocker.patch.object(match_mgr.rf_client, 'request', return_value=mock)

        model = match_mgr.lookup('L37nw-')
        assert isinstance(model, EntityLookup)
        assert model.type_ == 'Organization'
        assert model.attributes.name == 'BlueDelta'

    def test_lookup_raises_MatchApiError(self, match_mgr: EntityMatchMgr, mocker):
        mocker.patch.object(match_mgr.rf_client, 'request', side_effect=HTTPError)
        with pytest.raises(MatchApiError):
            match_mgr.lookup('L37nw-')

    def test_lookup_bulk(self, match_mgr: EntityMatchMgr, mocker, make_response):
        mock_1 = {
            'data': {
                'id': 'JLHNoH',
                'type': 'Malware',
                'attributes': {
                    'name': 'Cobalt Strike',
                    'common_names': [],
                    'alias': [],
                    'is_threat_actor': False,
                },
            }
        }
        mock_2 = {
            'data': {
                'id': 'B_qGH',
                'type': 'Product',
                'attributes': {
                    'name': 'MacOS',
                    'common_names': [],
                    'alias': ['cpe:/o:apple:mac_os_x', 'cpe:2.3:o:apple:macos:-:*:*:*:*:*:*:*'],
                    'is_threat_actor': False,
                },
            }
        }
        mocks = [make_response(mock_1), make_response(mock_2)]
        mocker.patch.object(match_mgr.rf_client, 'request', side_effect=mocks)
        ids = ['JLHNoH', 'B_qGH']
        data = match_mgr.lookup_bulk(ids, max_workers=0)

        assert isinstance(data, list)
        assert all(d.id_ in ids for d in data)

    def test_lookup_bulk_workers(self, match_mgr: EntityMatchMgr, mocker, make_response):
        ids = ['JLHNoH', 'B_qGH']

        dict_1 = {
            'data': {
                'id': 'JLHNoH',
                'type': 'Malware',
                'attributes': {
                    'name': 'Cobalt Strike',
                    'common_names': [],
                    'alias': [],
                    'is_threat_actor': False,
                },
            },
        }
        dict_2 = {
            'data': {
                'id': 'B_qGH',
                'type': 'Product',
                'attributes': {
                    'name': 'MacOS',
                    'common_names': [],
                    'alias': [
                        'cpe:/o:apple:mac_os_x',
                        'cpe:2.3:o:apple:macos:-:*:*:*:*:*:*:*',
                    ],
                    'is_threat_actor': False,
                },
            }
        }

        mocks = [make_response(dict_1), make_response(dict_2)]
        mocker.patch.object(match_mgr.rf_client, 'request', side_effect=mocks)
        data = match_mgr.lookup_bulk(ids, max_workers=2)
        assert isinstance(data, list)
        assert all(d.id_ in ids for d in data)

    def test_duplicates(self, match_mgr: EntityMatchMgr, mocker, make_response):
        mock = make_response(
            [
                {'id': 'I2Mli_', 'name': 'TransUnion', 'type': 'Company'},
                {'id': 'JJkDKS', 'name': 'TransUnion CIBIL', 'type': 'Company'},
                {'id': 'gD1pHd', 'name': 'TransUnion International UK Ltd.', 'type': 'Company'},
                {
                    'id': 'KeIm3E',
                    'name': 'TransUnion Risk and Alternative Data Solutions, Inc.',
                    'type': 'Company',
                },
                {'id': 'UDfMQN', 'name': 'TransUnion Canada', 'type': 'Company'},
                {'id': 'J05FEN', 'name': 'TransUnion South Africa', 'type': 'Company'},
                {'id': 'I2Mli_', 'name': 'TransUnion', 'type': 'Company'},
            ]
        )
        mocker.patch.object(match_mgr.rf_client, 'request', return_value=mock)
        name = 'TransUnion'
        type_ = 'Company'
        response = match_mgr.match(name, type_)
        response = [r.content.id_ for r in response]
        c = Counter(response)
        assert c == Counter(['UDfMQN', 'I2Mli_', 'gD1pHd', 'J05FEN', 'KeIm3E', 'JJkDKS'])

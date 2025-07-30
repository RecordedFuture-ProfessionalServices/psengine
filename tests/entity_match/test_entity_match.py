import pytest

TA = {
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
MALW = {
    'data': {
        'id': 'SoA6SP',
        'type': 'Malware',
        'attributes': {
            'name': 'Wcry',
            'common_names': ['WannaCry', 'WanaCrypt0r'],
            'alias': ['Wanna Decryptor', 'wanacryptor'],
            'is_threat_actor': False,
        },
    }
}


class Test_EntityMatch:
    def test_ordering(self, match_mgr, mocker, make_response):
        mock_2 = [
            {'id': 'SoA6SP', 'name': 'Wcry', 'type': 'Malware'},
            {'id': 'txvlKy', 'name': 'WANA CRY', 'type': 'Malware'},
        ]

        mock_1 = [
            {'id': 'aTsOzg', 'name': 'wanacry', 'type': 'Username'},
            {'id': 'cAO3b-', 'name': 'wanacry', 'type': 'Username'},
        ]
        mocks = [make_response(mock_1), make_response(mock_2)]
        mocker.patch.object(match_mgr.rf_client, 'request', side_effect=mocks)

        data = {'entity_name': 'WanaCry', 'entity_type': 'Username'}

        models = match_mgr.match(**data)
        with pytest.raises(TypeError):
            sorted(models)

    def test_str(self, match_mgr, mocker, make_response):
        mock_1 = make_response(
            [
                {'id': 'Ub_GAO', 'name': 'Wannacry', 'type': 'Username'},
                {'id': 'ub_gao', 'name': 'wannacry', 'type': 'username'},
            ]
        )

        mocker.patch.object(match_mgr.rf_client, 'request', return_value=mock_1)

        models = match_mgr.match(entity_name='WannaCry', entity_type='Username')
        assert '[Entity: Wannacry, Type: Username, ID: Ub_GAO, Entity: wannacry' in str(models)

    def test_ordering_EntityLookup(self, match_mgr, mocker, make_response):
        mocks = [make_response(TA), make_response(TA), make_response(MALW)]
        mocker.patch.object(match_mgr.rf_client, 'request', side_effect=mocks)

        v1 = match_mgr.lookup('L37nw-')
        v2 = match_mgr.lookup('L37nw-')
        v3 = match_mgr.lookup('SoA6SP')
        data = [v1, v2, v3]
        assert v1 == v2
        assert set(data) == {v1, v3}
        assert str(v1) == 'Entity Name: BlueDelta, Type: Organization, ID: L37nw-'

    def test_sorted_not_allowed_EntityLookup(self, match_mgr, mocker, make_response):
        mocks = [make_response(TA), make_response(TA), make_response(MALW)]
        mocker.patch.object(match_mgr.rf_client, 'request', side_effect=mocks)

        v1 = match_mgr.lookup('L37nw-')
        v2 = match_mgr.lookup('L37nw-')
        v3 = match_mgr.lookup('SoA6SP')
        data = [v1, v2, v3]
        with pytest.raises(TypeError):
            sorted(data)

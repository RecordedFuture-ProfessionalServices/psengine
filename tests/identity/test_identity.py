import itertools

import pytest

from psengine.identity.identity import (
    CredentialSearch,
    Detection,
    Detections,
    DetectionsIn,
    LeakedIdentity,
    PasswordLookup,
)
from psengine.identity.identity_mgr import IdentityMgr
from psengine.identity.models.common_models import DumpSearchOut
from tests.identity.conftest import MOCK_DIR


class Test_Identity:
    def test_adt_validation_fetch_detections(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [
            mock_request(MOCK_DIR / f'test_adt_validation_fetch_detections_{x}.json')
            for x in range(10)
        ]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)
        data = identity_mgr.fetch_detections(domains='norsegods.online', max_results=200)
        assert isinstance(data, Detections)
        assert all(isinstance(d, Detection) for d in data.detections)

    def test_detections_adt(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [mock_request(MOCK_DIR / f'test_detections_adt_{x}.json') for x in range(4)]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        data2 = identity_mgr.fetch_detections(domains='norsegods.online', max_results=3)
        d2 = data2.detections[0]
        d3 = data2.detections[1]

        assert (
            str(data2)
            == '[Detection ID: U5SkAsuNDjvgVssLgceYzbHGBlwmXHKV, Created: 2025-11-15 08:18:43, Type: External, Novel: True\nDetection ID: 6eLop47ygrcXQY1bEXDCIdCuS5c07MVw, Created: 2025-09-29 00:00:12, Type: External, Novel: True\nDetection ID: E4DNIy8fP64CATUcZc3B9pWizQRrMGbK, Created: 2025-03-16 08:44:04, Type: External, Novel: True]'
        )
        assert d2 != d3
        assert d2 > d3
        assert {d2, d2, d3} == {d2, d3}

    def test_adt_validation_lookup_hostname(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [
            mock_request(MOCK_DIR / f'test_adt_validation_lookup_hostname_{x}.json')
            for x in range(2)
        ]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        data = identity_mgr.lookup_hostname('LENOVO')
        assert all(isinstance(d, LeakedIdentity) for d in data)

    def test_leaked_identity_adt(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [mock_request(MOCK_DIR / f'test_leaked_identity_adt_{x}.json') for x in range(6)]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        h1 = identity_mgr.lookup_hostname('LENOVO').pop(0).credentials
        h2 = identity_mgr.lookup_hostname('LENOVO2').pop(0).credentials

        h3 = identity_mgr.lookup_hostname('YJ-LAPPY').pop(0).credentials
        h1_zero = h1[0]
        h3_zero = h3[0]
        data = set(itertools.chain(h1, h2, h3))
        assert len(data) == 3
        assert h1_zero != h3_zero
        assert h1_zero > h3_zero
        assert (
            str(h1_zero)
            == "Subject: Where are my pants?, First Downloaded: 2025-01-20 16:44:42, Hashes: [Erlang is known for its designs that are well suited for systems., He looked inquisitively at his keyboard and wrote another sentence., I don't even care., Its main implementation is the Glasgow Haskell Compiler.], Authorization Service: https://percent.cl/"
        )

    def test_adt_validation_lookup_password(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [mock_request(MOCK_DIR / 'test_adt_validation_lookup_password_0.json')]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        passwords = [
            ('1e347780ad4bd419901dd882eb1acd289037a04c083c50761a22a0b016079433', 'sha256'),
            ('b3ece0bfa908b49fee950d32df7eb10c', 'md5'),
            ('5ddc1d99d63a9cd2cdc7b8b725d99a8bff7665f6', 'sha1'),
            ('6d5c9524a4c0a94e0e82c8a03ec84187', 'ntlm'),
        ]
        data = identity_mgr.lookup_password(passwords=passwords)
        assert all(isinstance(d, PasswordLookup) for d in data)

    def test_password_lookup_adt(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [mock_request(MOCK_DIR / f'test_password_lookup_adt_{x}.json') for x in range(3)]

        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        passwords = [
            ('1e347780ad4bd419901dd882eb1acd289037a04c083c50761a22a0b016079433', 'sha256'),
        ]
        h1 = identity_mgr.lookup_password(passwords=passwords).pop(0)
        h3 = identity_mgr.lookup_password(
            passwords=[('6d5c9524a4c0a94e0e82c8a03ec84187', 'ntlm')]
        ).pop(0)

        assert {h1, h1, h3} == {h1, h3}
        assert h1 != h3
        assert h1 > h3
        assert (
            str(h1)
            == 'Hash: They are written as strings of consecutive alphanumeric characters, the first character being lowercase., Algorithm: SHA256, Exposure Status: Its main implementation is the Glasgow Haskell Compiler.'
        )

    def test_adt_validation_lookup_ip(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [
            mock_request(MOCK_DIR / f'test_adt_validation_lookup_ip_{x}.json') for x in range(14)
        ]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        data = identity_mgr.lookup_ip(
            range_gte='152.0.0.0', range_lte='152.255.255.255', max_results=200
        )
        assert all(isinstance(d, LeakedIdentity) for d in data)

    def test_adt_validation_credentials(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [
            mock_request(MOCK_DIR / f'test_adt_validation_credentials_{x}.json') for x in range(4)
        ]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)
        search = identity_mgr.search_credentials(domains='norsegods.online', domain_types='Email')
        data = identity_mgr.lookup_credentials(subjects_login=search)
        assert all(isinstance(d, LeakedIdentity) for d in data)
        assert all(isinstance(d, CredentialSearch) for d in search)

    def test_search_credential_adt(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [
            mock_request(MOCK_DIR / f'test_search_credential_adt_{x}.json') for x in range(2)
        ] * 2
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        search1 = identity_mgr.search_credentials(domains='norsegods.online', domain_types='Email')
        search2 = identity_mgr.search_credentials(domains='norsegods.online', domain_types='Email')

        search = search1 + search2
        search = set(search)
        assert len(search) == len(search1)
        assert all(a == b for a, b in zip(search1, search2))
        assert search1[0] > search1[1]
        assert (
            str(search1[0])
            == 'Login: The syntax {D1,D2,...,Dn} denotes a tuple whose arguments are D1, D2, ... Dn., Domain: Do you come here often?'
        )

    def test_adt_validation_search_dump(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [mock_request(MOCK_DIR / 'test_adt_validation_search_dump_0.json')]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        data = identity_mgr.search_dump(names='Moise Dump 2023')
        assert all(isinstance(d, DumpSearchOut) for d in data)

    @pytest.mark.parametrize(
        'org',
        ['69sKLfTGsS', 'uhash:69sKLfTGsS', ['69sKLfTGsS', 'uhash:69sKLfTGsS']],
        ids=[0, 1, 2],
    )
    def test_fetch_with_org_id(self, org):
        data = DetectionsIn.model_validate(
            {'organization_id': org, 'domains': ['norsegods.online'], 'limit': 1}
        )
        assert set(data.organization_id) == {'uhash:69sKLfTGsS'}

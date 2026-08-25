import re
from pathlib import Path

import pytest
from data_for_tests import (
    CREDS_LOOKUP_FILTER_WITH_RES,
    CREDS_LOOKUP_FILTER_WITHOUT_RES,
    CREDS_SEARCH_FILTER,
    DETECTION_FILTERS,
    HOSTNAME_LOOKUP_FILTER,
    IP_LOOKUP_FILTER,
)
from pydantic import ValidationError
from requests.models import HTTPError

from psengine.identity import IdentityMgr
from psengine.identity.errors import DetectionsFetchError, IdentityLookupError, IdentitySearchError
from psengine.identity.identity import (
    CredentialSearch,
    Detections,
    IncidentReportOut,
    LeakedIdentity,
)
from psengine.identity.models.common_models import DumpSearchOut
from psengine.identity.models.incident_report import (
    IncidentReportCredentials,
    IncidentReportDetails,
)
from tests.identity.conftest import MOCK_DIR


class Test_IdentityMgr:
    def test_mgr(self, identity_mgr: IdentityMgr):
        assert isinstance(identity_mgr, IdentityMgr)

    # fetch_detections
    @pytest.mark.parametrize(
        ('filters', 'expected'), DETECTION_FILTERS, ids=list(range(len(DETECTION_FILTERS)))
    )
    def test_fetch_detections(
        self, identity_mgr: IdentityMgr, filters, expected, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_fetch_detections\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name))

        mock = [mock_request(f) for f in files]

        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        data = identity_mgr.fetch_detections(**filters)
        assert len(data.detections) == expected
        assert isinstance(data, Detections)
        assert len(data.detections) == data.total

    @pytest.mark.parametrize(
        'org',
        ['69sKLfTGsS', 'uhash:69sKLfTGsS', ['69sKLfTGsS', 'uhash:69sKLfTGsS']],
        ids=[0, 1, 2],
    )
    def test_fetch_with_org_id(self, identity_mgr: IdentityMgr, org, mocker, mock_request, request):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_fetch_with_org_id\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name))

        mock = [mock_request(f) for f in files]

        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        mock = mocker.spy(identity_mgr.rf_client, 'request')
        data = identity_mgr.fetch_detections(organization_id=org, domains=['norsegods.online'])

        assert set(mock.call_args[1]['data']['organization_id']) == {'uhash:69sKLfTGsS'}
        assert isinstance(data, Detections)

    def test_fetch_raises_DetectionFetchError(self, identity_mgr: IdentityMgr, mocker):
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=HTTPError)
        with pytest.raises(DetectionsFetchError):
            identity_mgr.fetch_detections(domains=['norsegods.online'])

    def test_fetch_with_detection_per_page(self): ...
    # lookup_hostname
    @pytest.mark.parametrize(
        ('filters', 'expected'),
        HOSTNAME_LOOKUP_FILTER,
        ids=list(range(len(HOSTNAME_LOOKUP_FILTER))),
    )
    def test_lookup_hostname(
        self,
        identity_mgr: IdentityMgr,
        filters,
        expected,
        mocker,
        mock_request,
        request,
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_lookup_hostname\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name))

        mock = [mock_request(f) for f in files]

        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        data = identity_mgr.lookup_hostname(**filters)
        assert len(data) == expected
        assert all(isinstance(x, LeakedIdentity) for x in data)

    def test_lookup_hostname_raises_IdentityLookupError(self, identity_mgr: IdentityMgr, mocker):
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=HTTPError)
        with pytest.raises(IdentityLookupError):
            identity_mgr.lookup_hostname(hostname='Test')

    # lookup_password
    PASSWORD_PARAMS = [
        ({'hash_prefix': 'abc', 'algorithm': 'sha256'}, 'Common'),
        (
            {
                'hash_prefix': '8e9a96e78f380e4a2ec8277395e1a4876d7d476410ba6d9824242121727f5fed',
                'algorithm': 'sha256',
            },
            'Common',
        ),
        (
            {
                'passwords': [
                    ('995bb852c775d6', 'ntlm'),
                    ('8985b89acb97b011913c8b7f57e298d2', 'md5'),
                ]
            },
            'Uncommon',
        ),
    ]

    @pytest.mark.parametrize(('params', 'expected'), PASSWORD_PARAMS)
    def test_lookup_password_hash_prefix(
        self, identity_mgr: IdentityMgr, params, expected, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_lookup_password_hash_prefix\[{re.escape(node_id)}\]_0.json$')
        files = sorted(f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name))

        mock = [mock_request(f) for f in files]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        data = identity_mgr.lookup_password(**params)
        assert all(d.exposure_status == expected for d in data)

    def test_lookup_password_raises_IdentityLookupError(self, identity_mgr: IdentityMgr, mocker):
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=HTTPError)
        with pytest.raises(IdentityLookupError):
            identity_mgr.lookup_password(hash_prefix='abc', algorithm='sha256')

    PASSWORD_VALUE_ERROR = [
        ('a', 'b', [('c', 'd')], 'Specify only hash_prefix with algorithm, or only passwords'),
        ('a', None, None, 'hash_prefix must be specified with algorithm'),
        (None, 'b', None, 'hash_prefix must be specified with algorithm'),
        (None, None, None, 'hash_prefix must be specified with algorithm'),
        ('a', None, [('c', 'd')], 'Specify only hash_prefix with algorithm, or only passwords'),
        (None, 'b', [('c', 'd')], 'Specify only hash_prefix with algorithm, or only passwords'),
    ]

    @pytest.mark.parametrize(
        ('hash_prefix', 'algorithm', 'passwords', 'match'), PASSWORD_VALUE_ERROR
    )
    def test_lookup_password_raises_ValueError(
        self, identity_mgr: IdentityMgr, hash_prefix, algorithm, passwords, match
    ):
        with pytest.raises(ValueError, match=match):
            identity_mgr.lookup_password(
                hash_prefix=hash_prefix, algorithm=algorithm, passwords=passwords
            )

    # lookup_ip
    @pytest.mark.parametrize(
        ('filters', 'expected'), IP_LOOKUP_FILTER, ids=list(range(len(IP_LOOKUP_FILTER)))
    )
    def test_lookup_ip(
        self, identity_mgr: IdentityMgr, filters, expected, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_lookup_ip\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mocks)

        data = identity_mgr.lookup_ip(**filters)
        assert len(data) == expected
        assert all(isinstance(t, LeakedIdentity) for t in data)

    IP_LOOKUP_FILTER_VALUE_ERROR = [
        {},
        {
            'organization_id': 'uhash:abcdef',
            'exfiltration_date_gte': '2012-05-08T13:03:16.570Z',
            'max_results': 200,
            'identities_per_page': 100,
        },
    ]

    @pytest.mark.parametrize(
        ('filters'),
        IP_LOOKUP_FILTER_VALUE_ERROR,
        ids=list(range(len(IP_LOOKUP_FILTER_VALUE_ERROR))),
    )
    def test_lookup_ip_raises_ValueError(self, identity_mgr: IdentityMgr, filters):
        with pytest.raises(ValueError, match='Either an IP or a range has to be specified'):
            identity_mgr.lookup_ip(**filters)

    def test_lookup_ip_raises_IdentityLookupError(self, identity_mgr: IdentityMgr, mocker):
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=HTTPError)
        with pytest.raises(IdentityLookupError):
            identity_mgr.lookup_ip(ip='8.8.8.8')

    # lookup_credentials
    @pytest.mark.parametrize(
        'data', CREDS_LOOKUP_FILTER_WITH_RES, ids=list(range(len(CREDS_LOOKUP_FILTER_WITH_RES)))
    )
    def test_lookup_credentials(
        self, identity_mgr: IdentityMgr, data, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_lookup_credentials\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mocks)

        data = identity_mgr.lookup_credentials(**data)
        assert all(isinstance(_, LeakedIdentity) for _ in data)
        assert len(data) > 0

    @pytest.mark.parametrize(
        'data',
        CREDS_LOOKUP_FILTER_WITHOUT_RES,
        ids=list(range(len(CREDS_LOOKUP_FILTER_WITHOUT_RES))),
    )
    def test_lookup_credentials_query(
        self, identity_mgr: IdentityMgr, data, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_lookup_credentials_query\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mocks)

        data = identity_mgr.lookup_credentials(**data)
        assert all(isinstance(_, LeakedIdentity) for _ in data)

    def test_lookup_credentials_raises_IdentityLookupError(self, identity_mgr: IdentityMgr, mocker):
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=HTTPError)
        with pytest.raises(IdentityLookupError):
            identity_mgr.lookup_credentials(subjects='admin@norsegods.online')

    def test_lookup_credentials_raises_ValueError(self, identity_mgr: IdentityMgr):
        with pytest.raises(ValueError, match=r'At least one subject.*'):
            identity_mgr.lookup_credentials(breach_name='moise')

    # search_credentials
    @pytest.mark.parametrize(
        ('data', 'count'),
        CREDS_SEARCH_FILTER,
        ids=list(range(len(CREDS_SEARCH_FILTER))),
    )
    def test_search_credentials(
        self, identity_mgr: IdentityMgr, data, count, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_search_credentials\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mocks)

        data = identity_mgr.search_credentials(**data)
        assert all(isinstance(d, CredentialSearch) for d in data)
        assert len(data) == count

    def test_search_credentials_raises_IdentitySearchError(self, identity_mgr: IdentityMgr, mocker):
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=HTTPError)
        with pytest.raises(IdentitySearchError):
            identity_mgr.search_credentials(domains='norsegods.online')

    def test_message_wrong_domain_in_identity(
        self, identity_mgr: IdentityMgr, mocker, mock_request
    ):
        mock = [mock_request(MOCK_DIR / 'test_message_wrong_domain_in_identity_0.json')]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        with pytest.raises(IdentitySearchError):
            identity_mgr.search_credentials(domains='moise.com')

    # search_dump
    def test_search_dump(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [mock_request(MOCK_DIR / 'test_search_dump_0.json')]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        data = identity_mgr.search_dump(names='InflateVids Dump 2023')
        assert all(isinstance(d, DumpSearchOut) for d in data)
        assert len(data) > 0

    def test_search_dump_without_results(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [mock_request(MOCK_DIR / 'test_search_dump_without_results_0.json')]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        data = identity_mgr.search_dump(names='Moise Dump 2023')
        assert isinstance(data, list)
        assert len(data) == 0

    def test_search_dump_raises_IdentitySearchError(self, identity_mgr: IdentityMgr, mocker):
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=HTTPError)
        with pytest.raises(IdentitySearchError):
            identity_mgr.search_dump(names='moise')

    def test_lookup_hostname_validation_error_names_entity(
        self, identity_mgr: IdentityMgr, mocker, make_response
    ):
        good = {'identity': {'subjects': ['ok@example.com']}, 'count': 1, 'credentials': []}
        bad = {'identity': {'subjects': ['broken@example.com']}, 'credentials': []}
        mocker.patch.object(
            identity_mgr.rf_client,
            'request',
            return_value=make_response(
                {'identities': [good, bad], 'count': 2, 'next_offset': None}
            ),
        )
        with pytest.raises(ValidationError, match=r'LeakedIdentity validation failed at index 1'):
            identity_mgr.lookup_hostname(hostname='Test')

    def test_lookup_password_validation_error_names_entity(
        self, identity_mgr: IdentityMgr, mocker, make_response
    ):
        good = {
            'password': {'algorithm': 'SHA256', 'hash_prefix': 'okpref'},
            'exposure_status': 'Common',
        }
        bad = {'password': {'algorithm': 'SHA256', 'hash_prefix': 'brokenpref'}}
        mocker.patch.object(
            identity_mgr.rf_client, 'request', return_value=make_response({'results': [good, bad]})
        )
        with pytest.raises(ValidationError, match='password.hash_prefix=brokenpref'):
            identity_mgr.lookup_password(hash_prefix='abc', algorithm='sha256')

    def test_search_credentials_validation_error_names_entity(
        self, identity_mgr: IdentityMgr, mocker, make_response
    ):
        good = {'login': 'ok-login', 'domain': 'example.com'}
        bad = {'login': 'broken-login'}
        mocker.patch.object(
            identity_mgr.rf_client,
            'request',
            return_value=make_response(
                {'identities': [good, bad], 'count': 2, 'next_offset': None}
            ),
        )
        with pytest.raises(ValidationError, match='login=broken-login'):
            identity_mgr.search_credentials(domains='example.com')

    def test_search_dump_validation_error_names_entity(
        self, identity_mgr: IdentityMgr, mocker, make_response
    ):
        good = {
            'name': 'good-dump',
            'source': 'src',
            'description': 'd',
            'downloaded': '2024-01-01T00:00:00Z',
        }
        bad = {'name': 'broken-dump'}
        mocker.patch.object(
            identity_mgr.rf_client, 'request', return_value=make_response({'dumps': [good, bad]})
        )
        with pytest.raises(ValidationError, match='name=broken-dump'):
            identity_mgr.search_dump(names='moise')

    def test_incident_report_with_details(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [
            mock_request(MOCK_DIR / f'test_incident_report_with_details_{x}.json') for x in range(2)
        ]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        source = 'identity-module-source-data/malware_log_hashed_output/ce46cf/ce46cf7845799a604fa8e324639c112f91cb583c328c40696bfac5ab69bbe667.zip'
        data = identity_mgr.fetch_incident_report(source=source, include_details=True)
        assert isinstance(data, IncidentReportOut)
        assert isinstance(data.credentials, list)
        assert all(isinstance(d, IncidentReportCredentials) for d in data.credentials)
        assert isinstance(data.details, IncidentReportDetails)

    def test_incident_report_without_details(self, identity_mgr: IdentityMgr, mocker, mock_request):
        mock = [
            mock_request(MOCK_DIR / f'test_incident_report_without_details_{x}.json')
            for x in range(2)
        ]
        mocker.patch.object(identity_mgr.rf_client, 'request', side_effect=mock)

        source = 'identity-module-source-data/malware_log_hashed_output/ce46cf/ce46cf7845799a604fa8e324639c112f91cb583c328c40696bfac5ab69bbe667.zip'
        data = identity_mgr.fetch_incident_report(source=source, include_details=False)
        assert isinstance(data, IncidentReportOut)
        assert isinstance(data.credentials, list)
        assert all(isinstance(d, IncidentReportCredentials) for d in data.credentials)
        assert data.details is None

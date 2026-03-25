from copy import deepcopy
from pathlib import Path
from typing import Optional

import pytest
from pydantic import ValidationError
from requests.exceptions import HTTPError

from psengine.asi.asi import (
    Asset,
    AssetResponse,
    AssetWithExposureSearch,
    ExposureSearchOut,
    ProjectListOut,
)
from psengine.asi.asi_mgr import AttackSurfaceMgr
from psengine.asi.errors import (
    ASIExposureSearchError,
    ASIFetchAssetError,
    ASIFetchExposureError,
    ASIFetchProjectsError,
    ASISearchAssetsError,
)

DEFAULT_SEARCH_BODY = {'pagination': {'limit': 1000}, 'sort': ['discovered_at']}
MOCK_DIR = Path(__file__).parent / 'mocks'
PROJECT_ID = '7c2d06d7-0c4b-4d0d-bc97-f81dcdc276de'


def _meta_payload(*, limit: int = 1, total: int = 1, next_cursor: Optional[str] = None) -> dict:
    return {'pagination': {'limit': limit, 'total': total, 'next_cursor': next_cursor}}


def _asset_payload(*, asset_id: str = 'asset-1', name: str = 'example.com') -> dict:
    return {
        'project_id': 'project-1',
        'id': asset_id,
        'name': name,
        'type': 'domain',
        'discovered_at': None,
        'added_to_project_at': '2024-01-01T00:00:00Z',
    }


def _signature_payload() -> dict:
    return {
        'id': 'sig-1',
        'name': 'Example Signature',
        'description': None,
        'severity': 'critical',
        'references': [],
    }


@pytest.fixture
def asi_mgr():
    return AttackSurfaceMgr(api_token='a' * 32)


class Test_ASI:
    def test_fetch_projects_returns_project_list_response(
        self, asi_mgr: AttackSurfaceMgr, mocker, make_response
    ):
        mocker.patch.object(
            asi_mgr.asi_client,
            'request',
            return_value=make_response(
                {
                    'data': [
                        {
                            'id': '11111111-1111-1111-1111-111111111111',
                            'title': 'Example Project',
                        }
                    ],
                    'meta': _meta_payload(),
                }
            ),
        )

        result = asi_mgr.fetch_projects()

        assert isinstance(result, ProjectListOut)

    def test_fetch_projects_validates_projects_mock(
        self, asi_mgr: AttackSurfaceMgr, mocker, mock_request
    ):
        mocker.patch.object(
            asi_mgr.asi_client,
            'request',
            return_value=mock_request(MOCK_DIR / 'asi_projects.json'),
        )

        result = asi_mgr.fetch_projects()

        assert isinstance(result, ProjectListOut)
        assert len(result.data) == 3
        assert str(result.data[0].id_) == '3ce6292b-29be-4199-9024-231818e384a4'
        assert result.data[0].title == 'Partner Shared Demo'
        assert result.data[0].max_exposure_score == 99
        assert result.meta.counts.total == 3
        assert result.meta.request_id == '08209248cc2b46139709f15588bcf04b'

    def test_search_assets_returns_asset_response(self, asi_mgr: AttackSurfaceMgr, mocker):
        mocker.patch.object(
            asi_mgr.asi_client,
            'request_paged',
            return_value={'data': [_asset_payload()], 'meta': _meta_payload()},
        )

        result = asi_mgr.search_assets(project_id='project-1')

        assert isinstance(result, AssetResponse)

    def test_search_assets_uses_next_cursor_in_post_body_for_pagination(
        self, asi_mgr: AttackSurfaceMgr, mocker, make_response
    ):
        responses = iter(
            [
                make_response(
                    {
                        'data': [_asset_payload()],
                        'meta': _meta_payload(total=2, next_cursor='cursor-1'),
                    }
                ),
                make_response(
                    {
                        'data': [_asset_payload(asset_id='asset-2', name='example.org')],
                        'meta': _meta_payload(total=2),
                    }
                ),
            ]
        )
        captured = []

        def side_effect(*args, **kwargs):  # noqa: ARG001
            captured.append(
                {
                    'method': kwargs['method'],
                    'params': deepcopy(kwargs.get('params')),
                    'data': deepcopy(kwargs.get('data')),
                }
            )
            return next(responses)

        mocker.patch.object(asi_mgr.asi_client, 'request', side_effect=side_effect)

        result = asi_mgr.search_assets(project_id='project-1', assets_per_page=1, max_results=2)

        assert [asset.id_ for asset in result.data] == ['asset-1', 'asset-2']
        assert [call['method'] for call in captured] == ['POST', 'POST']
        assert [call['params'] for call in captured] == [{}, {}]
        assert captured[0]['data'] == {'pagination': {'limit': 1}, 'sort': ['discovered_at']}
        assert captured[1]['data'] == {
            'pagination': {'limit': 1, 'next_cursor': 'cursor-1'},
            'sort': ['discovered_at'],
        }

    def test_search_assets_validates_search_mock(
        self, asi_mgr: AttackSurfaceMgr, mocker, mock_request
    ):
        mock_request_spy = mocker.patch.object(
            asi_mgr.asi_client,
            'request',
            return_value=mock_request(MOCK_DIR / 'asi_search.json'),
        )

        result = asi_mgr.search_assets(project_id=PROJECT_ID, max_results=100)

        assert isinstance(result, AssetResponse)
        assert len(result.data) == 100
        assert (
            result.data[0].id_ == 'z3nab-a7d897-cca7c8cdafa5a6f9bd85ebf2f62d2c33107f07.zendesk.com'
        )
        assert result.data[0].apex_domain == 'zendesk.com'
        assert result.data[0].type_ == 'domain'
        assert result.data[2].resolved_ips is None
        assert result.meta.counts.returned == 100
        assert result.meta.pagination.total == 1711
        assert mock_request_spy.call_count == 1

    _search_assets_data = [
        (
            {'quick_search': 'example'},
            {**DEFAULT_SEARCH_BODY, 'filter': {'quick_search': {'search': 'example'}}},
        ),
        (
            {'asset_name': 'example.com'},
            {
                **DEFAULT_SEARCH_BODY,
                'filter': {'asset_properties': {'name': {'contains': 'example.com'}}},
            },
        ),
        (
            {'asset_id': 'asset-1', 'is_static_asset': True, 'is_responsive': False},
            {
                **DEFAULT_SEARCH_BODY,
                'filter': {
                    'asset_properties': {
                        'asset_id': {'eq': 'asset-1'},
                        'static_asset': {'eq': True},
                    },
                    'technology_properties': {'is_responsive': {'eq': False}},
                },
            },
        ),
        (
            {
                'asset_discovered_date': ('2024-01-01', '2024-12-31'),
                'exposure_score': (10, 80),
                'exposure_last_scanned': ('2024-06-01', '2024-12-31'),
            },
            {
                **DEFAULT_SEARCH_BODY,
                'filter': {
                    'asset_properties': {
                        'discovered': {'start': '2024-01-01', 'end': '2024-12-31'}
                    },
                    'exposure_properties': {
                        'asset_exposure_score': {'start': 10, 'end': 80},
                        'last_scanned_at': {'start': '2024-06-01', 'end': '2024-12-31'},
                    },
                },
            },
        ),
        (
            {
                'asset_apex_domain': 'apex.com',
                'custom_tags': ['tag1'],
                'certificate_issuer': "Let's Encrypt",
                'exposure_severity': 'critical',
                'exposure_signature_id': 'cve-2024-6387',
                'open_port_number': 443,
                'open_port_protocol': 'tcp',
                'open_port_service': 'http',
                'technology_name': 'nginx',
            },
            {
                **DEFAULT_SEARCH_BODY,
                'filter': {
                    'asset_properties': {
                        'apex': {'eq': 'apex.com'},
                        'custom_tags': {'in': ['tag1']},
                    },
                    'certificate_properties': {'certificate_issuer': {'eq': "Let's Encrypt"}},
                    'exposure_properties': {
                        'severity': {'eq': 'critical'},
                        'signature_id': {'eq': 'cve-2024-6387'},
                    },
                    'technology_properties': {
                        'open_port_number': {'eq': 443},
                        'open_port_protocol': {'eq': 'tcp'},
                        'open_port_service': {'eq': 'http'},
                        'technology_name': {'eq': 'nginx'},
                    },
                },
            },
        ),
        (
            {
                'asset_apex_domain': ['a.com', 'b.com'],
                'custom_tags': ['internal', 'prod'],
                'certificate_issuer': ["Let's Encrypt", 'DigiCert'],
                'exposure_severity': ['critical', 'moderate'],
                'exposure_signature_id': ['cve-2024-6387', 'cve-2024-0001'],
                'open_port_number': [80, 443],
                'open_port_protocol': ['tcp', 'udp'],
                'open_port_service': ['http', 'ftp'],
                'technology_name': ['nginx', 'apache'],
            },
            {
                **DEFAULT_SEARCH_BODY,
                'filter': {
                    'asset_properties': {
                        'apex': {'in': ['a.com', 'b.com']},
                        'custom_tags': {'in': ['internal', 'prod']},
                    },
                    'certificate_properties': {
                        'certificate_issuer': {'in': ["Let's Encrypt", 'DigiCert']}
                    },
                    'exposure_properties': {
                        'severity': {'in': ['critical', 'moderate']},
                        'signature_id': {'in': ['cve-2024-6387', 'cve-2024-0001']},
                    },
                    'technology_properties': {
                        'open_port_number': {'in': [80, 443]},
                        'open_port_protocol': {'in': ['tcp', 'udp']},
                        'open_port_service': {'in': ['http', 'ftp']},
                        'technology_name': {'in': ['nginx', 'apache']},
                    },
                },
            },
        ),
        (
            {'enrichments': ['whois', 'exposures']},
            {**DEFAULT_SEARCH_BODY, 'enrichments': ['whois', 'exposures']},
        ),
        (
            {
                'asset_apex_domain': 'example.com',
                'exposure_severity': 'critical',
                'enrichments': ['exposures', 'certificates'],
            },
            {
                **DEFAULT_SEARCH_BODY,
                'filter': {
                    'asset_properties': {'apex': {'eq': 'example.com'}},
                    'exposure_properties': {'severity': {'eq': 'critical'}},
                },
                'enrichments': ['exposures', 'certificates'],
            },
        ),
    ]

    @pytest.mark.parametrize(
        ('search_kwargs', 'expected_body'),
        _search_assets_data,
        ids=range(len(_search_assets_data)),
    )
    def test_search_assets_builds_correct_filter(
        self, asi_mgr: AttackSurfaceMgr, mocker, search_kwargs, expected_body
    ):
        mock_request_paged = mocker.patch.object(
            asi_mgr.asi_client,
            'request_paged',
            return_value={'data': [_asset_payload()], 'meta': _meta_payload()},
        )

        asi_mgr.search_assets(project_id='project-1', **search_kwargs)

        actual_body = mock_request_paged.call_args.kwargs['data']
        assert actual_body == expected_body

    def test_search_assets_raises_validation_error_for_reversed_exposure_score_range(
        self, asi_mgr: AttackSurfaceMgr, mocker
    ):
        mock_request_paged = mocker.patch.object(asi_mgr.asi_client, 'request_paged')

        with pytest.raises(
            ValidationError,
            match=r'exposure_score start \(80\) must be <= end \(10\)',
        ):
            asi_mgr.search_assets(project_id='project-1', exposure_score=(80, 10))

        mock_request_paged.assert_not_called()

    def test_search_exposures_returns_exposure_search_out(self, asi_mgr: AttackSurfaceMgr, mocker):
        mocker.patch.object(
            asi_mgr.asi_client,
            'request_paged',
            return_value={
                'data': [
                    {
                        'asset_count': 1,
                        'asset_exposures': [],
                        'signature': _signature_payload(),
                    }
                ],
                'meta': _meta_payload(),
            },
        )

        result = asi_mgr.search_exposures(project_id='project-1')

        assert isinstance(result, ExposureSearchOut)

    def test_search_exposures_validates_exposures_mock(
        self, asi_mgr: AttackSurfaceMgr, mocker, mock_request
    ):
        mock_request_spy = mocker.patch.object(
            asi_mgr.asi_client,
            'request',
            return_value=mock_request(MOCK_DIR / 'asi_exposures.json'),
        )

        result = asi_mgr.search_exposures(project_id=PROJECT_ID, max_results=100)

        assert isinstance(result, ExposureSearchOut)
        assert len(result.data) == 100
        assert result.data[0].asset_count == 116
        assert result.data[0].signature.id_ == 'low-security-cipher-list'
        assert result.data[0].signature.severity.value == 'critical'
        assert result.meta.counts.total == 287
        assert result.meta.pagination.limit == 100
        assert mock_request_spy.call_count == 1

    def test_fetch_exposures_by_signature_returns_asset_with_exposure_search(
        self, asi_mgr: AttackSurfaceMgr, mocker
    ):
        mocker.patch.object(
            asi_mgr.asi_client,
            'request_paged',
            return_value={
                'data': [{'asset_exposures': [], 'signature': _signature_payload(), 'meta': {}}],
                'meta': _meta_payload(),
            },
        )

        result = asi_mgr.fetch_exposures_by_signature(project_id='project-1', signature_id='sig-1')

        assert isinstance(result, AssetWithExposureSearch)

    def test_fetch_exposures_by_signature_validates_signature_mock(
        self, asi_mgr: AttackSurfaceMgr, mocker, mock_request
    ):
        mock_request_spy = mocker.patch.object(
            asi_mgr.asi_client,
            'request',
            return_value=mock_request(MOCK_DIR / 'asi_exposure_signature.json'),
        )

        result = asi_mgr.fetch_exposures_by_signature(
            project_id=PROJECT_ID,
            signature_id='CVE-2022-2551',
            max_results=5,
        )

        assert isinstance(result, AssetWithExposureSearch)
        assert result.signature.id_ == 'CVE-2022-2551'
        assert result.signature.severity.value == 'critical'
        assert len(result.asset_exposures) == 5
        assert result.asset_exposures[0].asset_id == 'staff.basij.sharif.edu'
        assert result.signature.vulnerabilities[0].cvss_score == 9.8
        assert mock_request_spy.call_count == 1

    def test_fetch_assets_returns_asset_response(self, asi_mgr: AttackSurfaceMgr, mocker):
        mocker.patch.object(
            asi_mgr.asi_client,
            'request_paged',
            return_value={'data': [_asset_payload()], 'meta': _meta_payload()},
        )

        result = asi_mgr.fetch_assets(project_id='project-1')

        assert isinstance(result, AssetResponse)

    def test_fetch_assets_validates_assets_mock(
        self, asi_mgr: AttackSurfaceMgr, mocker, mock_request
    ):
        mock_request_spy = mocker.patch.object(
            asi_mgr.asi_client,
            'request',
            return_value=mock_request(MOCK_DIR / 'asi_assets.json'),
        )

        result = asi_mgr.fetch_assets(project_id=PROJECT_ID, max_results=50)

        assert isinstance(result, AssetResponse)
        assert len(result.data) == 50
        assert result.data[0].id_ == 'zzzezzzacosmetics.zendesk.com'
        assert result.data[0].resolved_ips == ['216.198.54.6', '216.198.53.6']
        assert result.data[0].apex_domain == 'zendesk.com'
        assert result.meta.counts.returned == 50
        assert result.meta.pagination.total == 1711
        assert mock_request_spy.call_count == 1

    def test_fetch_asset_returns_asset(self, asi_mgr: AttackSurfaceMgr, mocker, make_response):
        mocker.patch.object(
            asi_mgr.asi_client,
            'request',
            return_value=make_response({'data': _asset_payload()}),
        )

        result = asi_mgr.fetch_asset(project_id='project-1', asset_id='asset-1')

        assert isinstance(result, Asset)

    def test_fetch_asset_validates_asset_mock(
        self, asi_mgr: AttackSurfaceMgr, mocker, mock_request
    ):
        mocker.patch.object(
            asi_mgr.asi_client,
            'request',
            return_value=mock_request(MOCK_DIR / 'asi_asset.json'),
        )

        result = asi_mgr.fetch_asset(
            project_id=PROJECT_ID,
            asset_id='zzzezzzacosmetics.zendesk.com',
        )

        assert isinstance(result, Asset)
        assert result.id_ == 'zzzezzzacosmetics.zendesk.com'
        assert result.apex_domain == 'zendesk.com'
        assert len(result.dns_records) == 1
        assert result.dns_records[0].record_type == 'A'
        assert len(result.scanned_ips) == 2
        assert result.scanned_ips[0].metadata.owner_name == 'Cloudflare, Inc.'
        assert result.whois.registrar == 'MarkMonitor, Inc.'

    @pytest.mark.parametrize(
        ('method_name', 'client_method_name', 'kwargs', 'expected_error'),
        [
            ('fetch_projects', 'request', {}, ASIFetchProjectsError),
            ('search_assets', 'request_paged', {'project_id': PROJECT_ID}, ASISearchAssetsError),
            (
                'search_exposures',
                'request_paged',
                {'project_id': PROJECT_ID},
                ASIExposureSearchError,
            ),
            (
                'fetch_exposures_by_signature',
                'request_paged',
                {'project_id': PROJECT_ID, 'signature_id': 'sig-1'},
                ASIFetchExposureError,
            ),
            ('fetch_assets', 'request_paged', {'project_id': PROJECT_ID}, ASIFetchAssetError),
            (
                'fetch_asset',
                'request',
                {'project_id': PROJECT_ID, 'asset_id': 'asset-1'},
                ASIFetchAssetError,
            ),
            (
                'fetch_asset_exposures',
                'request',
                {'project_id': PROJECT_ID, 'asset_id': 'asset-1'},
                ASIFetchAssetError,
            ),
        ],
        ids=[
            'fetch_projects',
            'search_assets',
            'search_exposures',
            'fetch_exposures_by_signature',
            'fetch_assets',
            'fetch_asset',
            'fetch_asset_exposures',
        ],
    )
    def test_methods_reraise_http_error_as_asi_error(
        self,
        asi_mgr: AttackSurfaceMgr,
        mocker,
        method_name: str,
        client_method_name: str,
        kwargs: dict,
        expected_error: type[Exception],
    ):
        mocker.patch.object(
            asi_mgr.asi_client,
            client_method_name,
            side_effect=HTTPError('error'),
        )

        with pytest.raises(expected_error, match='error'):
            getattr(asi_mgr, method_name)(**kwargs)

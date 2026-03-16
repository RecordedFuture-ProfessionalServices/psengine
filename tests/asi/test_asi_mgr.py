import pytest

from psengine.asi.asi import Asset, AssetResponse, AssetWithExposureSearch, ExposureSearchOut
from psengine.asi.asi_mgr import AttackSurfaceMgr
from psengine.asi.models.project import ProjectListResponse

DEFAULT_SEARCH_BODY = {'pagination': {'limit': 1000}, 'sort': ['discovered_at']}


def _meta_payload() -> dict:
    return {'pagination': {'limit': 1, 'total': 1, 'next_cursor': None}}


def _asset_payload() -> dict:
    return {
        'project_id': 'project-1',
        'id': 'asset-1',
        'name': 'example.com',
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


def test_fetch_projects_returns_project_list_response(
    asi_mgr: AttackSurfaceMgr, mocker, make_response
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

    assert isinstance(result, ProjectListResponse)


def test_search_assets_returns_asset_response(asi_mgr: AttackSurfaceMgr, mocker):
    mocker.patch.object(
        asi_mgr.asi_client,
        'request_paged',
        return_value={'data': [_asset_payload()], 'meta': _meta_payload()},
    )

    result = asi_mgr.search_assets(project_id='project-1')

    assert isinstance(result, AssetResponse)


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
    'search_kwargs, expected_body',
    _search_assets_data,
    ids=range(len(_search_assets_data)),
)
def test_search_assets_builds_correct_filter(
    asi_mgr: AttackSurfaceMgr, mocker, search_kwargs, expected_body
):
    mock_request_paged = mocker.patch.object(
        asi_mgr.asi_client,
        'request_paged',
        return_value={'data': [_asset_payload()], 'meta': _meta_payload()},
    )

    asi_mgr.search_assets(project_id='project-1', **search_kwargs)

    actual_body = mock_request_paged.call_args.kwargs['data']
    assert actual_body == expected_body


def test_search_exposures_returns_exposure_search_out(asi_mgr: AttackSurfaceMgr, mocker):
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


def test_fetch_exposures_by_signature_returns_asset_with_exposure_search(
    asi_mgr: AttackSurfaceMgr, mocker
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


def test_fetch_assets_returns_asset_response(asi_mgr: AttackSurfaceMgr, mocker):
    mocker.patch.object(
        asi_mgr.asi_client,
        'request_paged',
        return_value={'data': [_asset_payload()], 'meta': _meta_payload()},
    )

    result = asi_mgr.fetch_assets(project_id='project-1')

    assert isinstance(result, AssetResponse)


def test_fetch_asset_returns_asset(asi_mgr: AttackSurfaceMgr, mocker, make_response):
    mocker.patch.object(
        asi_mgr.asi_client,
        'request',
        return_value=make_response({'data': _asset_payload()}),
    )

    result = asi_mgr.fetch_asset(project_id='project-1', asset_id='asset-1')

    assert isinstance(result, Asset)

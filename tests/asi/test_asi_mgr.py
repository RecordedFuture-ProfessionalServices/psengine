import pytest

from psengine.asi.asi import Asset, AssetResponse, AssetWithExposureSearch, ExposureSearchOut
from psengine.asi.asi_mgr import AttackSurfaceMgr
from psengine.asi.models.project import ProjectListResponse


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


def test_fetch_projects_returns_project_list_response(asi_mgr, mocker, make_response):
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


def test_search_assets_returns_asset_response(asi_mgr, mocker):
    mocker.patch.object(
        asi_mgr.asi_client,
        'request_paged',
        return_value={'data': [_asset_payload()], 'meta': _meta_payload()},
    )

    result = asi_mgr.search_assets(project_id='project-1')

    assert isinstance(result, AssetResponse)


def test_search_exposures_returns_exposure_search_out(asi_mgr, mocker):
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


def test_fetch_exposures_by_signature_returns_asset_with_exposure_search(asi_mgr, mocker):
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


def test_fetch_assets_returns_asset_response(asi_mgr, mocker):
    mocker.patch.object(
        asi_mgr.asi_client,
        'request_paged',
        return_value={'data': [_asset_payload()], 'meta': _meta_payload()},
    )

    result = asi_mgr.fetch_assets(project_id='project-1')

    assert isinstance(result, AssetResponse)


def test_fetch_asset_returns_asset(asi_mgr, mocker, make_response):
    mocker.patch.object(
        asi_mgr.asi_client,
        'request',
        return_value=make_response({'data': _asset_payload()}),
    )

    result = asi_mgr.fetch_asset(project_id='project-1', asset_id='asset-1')

    assert isinstance(result, Asset)

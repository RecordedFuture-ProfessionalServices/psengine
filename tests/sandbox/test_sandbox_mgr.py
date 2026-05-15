from pathlib import Path

import pytest
from pydantic import ValidationError
from requests import ConnectionError, ConnectTimeout, HTTPError, ReadTimeout  # noqa: A004
from requests.models import Response

from psengine.endpoints import EP_SANDBOX_PROFILES, EP_SANDBOX_PROFILES_ID
from psengine.sandbox import (
    Profile,
    ProfileDeleteOut,
    ProfileOptions,
    ProfileUpdateOut,
    SandboxMgr,
)
from psengine.sandbox.errors import (
    ProfileCreateError,
    ProfileDeleteError,
    ProfileFetchError,
    ProfileNotFoundError,
    ProfileUpdateError,
)

MOCK_DIR = Path(__file__).parent / 'mocks'


def _http_error(status_code: int, message: str = 'boom') -> HTTPError:
    response = Response()
    response.status_code = status_code
    err = HTTPError(message)
    err.response = response
    return err


class Test_SandboxMgr:
    """Tests for SandboxMgr."""

    def test_fetch_profiles_happy_path(self, sandbox_mgr: SandboxMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'profile_list.json')
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        profiles = sandbox_mgr.fetch_profiles()

        assert isinstance(profiles, list)
        assert len(profiles) == 3
        assert all(isinstance(p, Profile) for p in profiles)
        assert mocked.call_args.args == (
            'get',
            EP_SANDBOX_PROFILES.format(base_url=sandbox_mgr.base_url),
        )

    def test_fetch_profiles_empty_list(self, sandbox_mgr: SandboxMgr, mocker, make_response):
        mock = make_response({'data': [], 'next': None})
        mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        assert sandbox_mgr.fetch_profiles() == []

    def test_fetch_profiles_raises_on_http_error(self, sandbox_mgr: SandboxMgr, mocker):
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=_http_error(500))

        with pytest.raises(ProfileFetchError):
            sandbox_mgr.fetch_profiles()

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_fetch_profiles_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        err = _http_error(500) if exception is HTTPError else exception('boom')
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=err)

        with pytest.raises(ProfileFetchError):
            sandbox_mgr.fetch_profiles()

    def test_fetch_profiles_raises_on_malformed_response(
        self, sandbox_mgr: SandboxMgr, mocker, make_response
    ):
        # Response missing the 'data' key -> KeyError in manager -> ProfileFetchError.
        mock = make_response({'unexpected': 'shape'})
        mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        with pytest.raises(ProfileFetchError):
            sandbox_mgr.fetch_profiles()

    def test_fetch_profile_by_id_happy_path(self, sandbox_mgr: SandboxMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'profile_single.json')
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        profile = sandbox_mgr.fetch_profile('979a3fb9-6c52-452d-bd14-650b9f2eecda')

        assert isinstance(profile, Profile)
        assert profile.id_ == '979a3fb9-6c52-452d-bd14-650b9f2eecda'
        assert profile.options.browser == 'chrome'
        assert mocked.call_args.args == (
            'get',
            EP_SANDBOX_PROFILES_ID.format(
                base_url=sandbox_mgr.base_url,
                profile_id='979a3fb9-6c52-452d-bd14-650b9f2eecda',
            ),
        )

    def test_fetch_profile_by_name(self, sandbox_mgr: SandboxMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'profile_single.json')
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        sandbox_mgr.fetch_profile('pse-mock-a53247df-full')

        # URL substitution must use the name verbatim (no encoding surprises).
        assert mocked.call_args.args[1].endswith('/profiles/pse-mock-a53247df-full')

    def test_fetch_profile_404_raises_not_found(self, sandbox_mgr: SandboxMgr, mocker):
        mocker.patch.object(
            sandbox_mgr.sb_client, 'request', side_effect=_http_error(404, 'not found')
        )

        with pytest.raises(ProfileNotFoundError):
            sandbox_mgr.fetch_profile('does-not-exist')

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_fetch_profile_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        err = _http_error(500) if exception is HTTPError else exception('boom')
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=err)

        with pytest.raises(ProfileNotFoundError):
            sandbox_mgr.fetch_profile('any-id')

    @pytest.mark.parametrize('profile_id', ['', None, 123])
    def test_fetch_profile_validation_error(self, sandbox_mgr: SandboxMgr, profile_id):
        with pytest.raises(ValidationError):
            sandbox_mgr.fetch_profile(profile_id)

    def test_fetch_profile_normalizes_response_oddities(
        self, sandbox_mgr: SandboxMgr, mocker, mock_request
    ):
        # profile_created_minimal.json has `network: ""` and `geolocation: null`
        # — the Profile validators must normalise these to None and [].
        mock = mock_request(MOCK_DIR / 'profile_created_minimal.json')
        mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        profile = sandbox_mgr.fetch_profile('d7ae61a8-8897-492d-b418-70ed582d0442')

        assert profile.network is None
        assert profile.geolocation == []
        assert profile.options is None

    def test_fetch_profile_options_empty_browser_normalised_to_none(
        self, sandbox_mgr: SandboxMgr, mocker, make_response
    ):
        # Real-world payloads show `"options": {"browser": ""}` for profiles
        # created without a browser choice — ProfileOptions must normalise
        # the empty string to None rather than failing Browser-Literal
        # validation. Mirrors the `drew-test` row in profile_list.json.
        mock = make_response(
            {
                'id': 'x',
                'name': 'x',
                'tags': [],
                'timeout': 30,
                'network': 'internet',
                'options': {'browser': ''},
            }
        )
        mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        profile = sandbox_mgr.fetch_profile('x')

        assert isinstance(profile.options, ProfileOptions)
        assert profile.options.browser is None

    def test_create_profile_minimal_payload(self, sandbox_mgr: SandboxMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'profile_created_minimal.json')
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        profile = sandbox_mgr.create_profile(
            name='pse-mock-a53247df-minimal',
            tags=['os:windows10-2004-x64'],
            timeout=60,
        )

        assert isinstance(profile, Profile)
        assert mocked.call_args.args == (
            'post',
            EP_SANDBOX_PROFILES.format(base_url=sandbox_mgr.base_url),
        )
        assert mocked.call_args.kwargs['data'] == {
            'name': 'pse-mock-a53247df-minimal',
            'tags': ['os:windows10-2004-x64'],
            'timeout': 60,
        }

    def test_create_profile_full_payload_with_browser(
        self, sandbox_mgr: SandboxMgr, mocker, mock_request
    ):
        mock = mock_request(MOCK_DIR / 'profile_created_full.json')
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        profile = sandbox_mgr.create_profile(
            name='pse-mock-a53247df-full',
            tags=['os:windows10-2004-x64', 'locale:en-us'],
            timeout=120,
            network='vpn',
            geolocation='us',  # bare string — coercion must convert to list.
            browser='chrome',
        )

        assert isinstance(profile, Profile)
        assert profile.options.browser == 'chrome'
        sent = mocked.call_args.kwargs['data']
        assert sent['name'] == 'pse-mock-a53247df-full'
        assert sent['tags'] == ['os:windows10-2004-x64', 'locale:en-us']
        assert sent['timeout'] == 120
        assert sent['network'] == 'vpn'
        assert sent['geolocation'] == ['us']
        assert sent['options'] == {'browser': 'chrome'} 
        assert 'browser' not in sent

    def test_create_profile_tags_string_coerced_to_list(
        self, sandbox_mgr: SandboxMgr, mocker, mock_request
    ):
        mock = mock_request(MOCK_DIR / 'profile_created_minimal.json')
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        sandbox_mgr.create_profile(
            name='whatever',
            tags='os:windows10-2004-x64',
            timeout=60,
        )

        assert mocked.call_args.kwargs['data']['tags'] == ['os:windows10-2004-x64']

    @pytest.mark.parametrize(
        'kwargs',
        [
            # empty name
            {'name': '', 'tags': ['t'], 'timeout': 60},
            # empty tags list (Field min_length=1)
            {'name': 'n', 'tags': [], 'timeout': 60},
            # timeout below range
            {'name': 'n', 'tags': ['t'], 'timeout': 0},
            # timeout above range
            {'name': 'n', 'tags': ['t'], 'timeout': 3601},
            # invalid browser
            {'name': 'n', 'tags': ['t'], 'timeout': 60, 'browser': 'safari'},
            # invalid network mode
            {'name': 'n', 'tags': ['t'], 'timeout': 60, 'network': 'wifi'},
        ],
    )
    def test_create_profile_validation_errors(self, sandbox_mgr: SandboxMgr, kwargs):
        with pytest.raises(ValidationError):
            sandbox_mgr.create_profile(**kwargs)

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_create_profile_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        err = _http_error(500) if exception is HTTPError else exception('boom')
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=err)

        with pytest.raises(ProfileCreateError):
            sandbox_mgr.create_profile(name='n', tags=['t'], timeout=60)

    def test_create_profile_raises_on_409_duplicate_name(self, sandbox_mgr: SandboxMgr, mocker):
        mocker.patch.object(
            sandbox_mgr.sb_client, 'request', side_effect=_http_error(409, 'duplicate')
        )

        with pytest.raises(ProfileCreateError):
            sandbox_mgr.create_profile(name='n', tags=['t'], timeout=60)

    def test_update_profile_happy_path(self, sandbox_mgr: SandboxMgr, mocker, make_response):
        # PUT returns empty body {} on success.
        mock = make_response({})
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        result = sandbox_mgr.update_profile(
            profile_id='abc-123',
            name='renamed',
            tags=['os:windows10-2004-x64'],
            timeout=180,
        )

        assert result.updated == True
        assert mocked.call_args.args == (
            'put',
            EP_SANDBOX_PROFILES_ID.format(base_url=sandbox_mgr.base_url, profile_id='abc-123'),
        )
        assert mocked.call_args.kwargs['data'] == {
            'name': 'renamed',
            'tags': ['os:windows10-2004-x64'],
            'timeout': 180,
        }

    def test_update_profile_with_browser_nested_under_options(
        self, sandbox_mgr: SandboxMgr, mocker, make_response
    ):
        mock = make_response({})
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        sandbox_mgr.update_profile(
            profile_id='abc-123',
            name='renamed',
            tags=['os:windows10-2004-x64'],
            timeout=180,
            browser='firefox',
        )

        sent = mocked.call_args.kwargs['data']
        assert sent['options'] == {'browser': 'firefox'}
        assert 'browser' not in sent

    def test_update_profile_404_returns_updated_false(self, sandbox_mgr: SandboxMgr, mocker):
        mocker.patch.object(
            sandbox_mgr.sb_client, 'request', side_effect=_http_error(404, 'not found')
        )

        result = sandbox_mgr.update_profile(
            profile_id='missing-id',
            name='n',
            tags=['t'],
            timeout=60,
        )

        assert result.updated == False

    @pytest.mark.parametrize('status_code', [400, 401, 409, 500])
    def test_update_profile_non_404_raises(self, sandbox_mgr: SandboxMgr, mocker, status_code):
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=_http_error(status_code))

        with pytest.raises(ProfileUpdateError):
            sandbox_mgr.update_profile(profile_id='abc-123', name='n', tags=['t'], timeout=60)

    @pytest.mark.parametrize('exception', [ConnectTimeout, ConnectionError, ReadTimeout])
    def test_update_profile_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=exception('boom'))

        with pytest.raises(ProfileUpdateError):
            sandbox_mgr.update_profile(profile_id='abc-123', name='n', tags=['t'], timeout=60)

    @pytest.mark.parametrize(
        'kwargs',
        [
            # empty profile_id
            {'profile_id': '', 'name': 'n', 'tags': ['t'], 'timeout': 60},
            # empty name
            {'profile_id': 'p', 'name': '', 'tags': ['t'], 'timeout': 60},
            # empty tags list
            {'profile_id': 'p', 'name': 'n', 'tags': [], 'timeout': 60},
            # bad timeout (too high)
            {'profile_id': 'p', 'name': 'n', 'tags': ['t'], 'timeout': 3601},
            # invalid browser
            {'profile_id': 'p', 'name': 'n', 'tags': ['t'], 'timeout': 60, 'browser': 'safari'},
        ],
    )
    def test_update_profile_validation_errors(self, sandbox_mgr: SandboxMgr, kwargs):
        with pytest.raises(ValidationError):
            sandbox_mgr.update_profile(**kwargs)

    def test_delete_profile_happy_path(self, sandbox_mgr: SandboxMgr, mocker, make_response):
        mock = make_response({})
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        result = sandbox_mgr.delete_profile(profile_id='abc-123')

        assert result.deleted == True
        assert mocked.call_args.args == (
            'delete',
            EP_SANDBOX_PROFILES_ID.format(base_url=sandbox_mgr.base_url, profile_id='abc-123'),
        )
        # DELETE carries no body.
        assert 'data' not in mocked.call_args.kwargs

    def test_delete_profile_404_returns_deleted_false(self, sandbox_mgr: SandboxMgr, mocker):
        mocker.patch.object(
            sandbox_mgr.sb_client, 'request', side_effect=_http_error(404, 'not found')
        )

        result = sandbox_mgr.delete_profile(profile_id='missing-id')

        assert result.deleted == False

    @pytest.mark.parametrize('status_code', [400, 401, 403, 500])
    def test_delete_profile_non_404_raises(self, sandbox_mgr: SandboxMgr, mocker, status_code):
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=_http_error(status_code))

        with pytest.raises(ProfileDeleteError):
            sandbox_mgr.delete_profile(profile_id='abc-123')

    @pytest.mark.parametrize('exception', [ConnectTimeout, ConnectionError, ReadTimeout])
    def test_delete_profile_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=exception('boom'))

        with pytest.raises(ProfileDeleteError):
            sandbox_mgr.delete_profile(profile_id='abc-123')

    @pytest.mark.parametrize('profile_id', ['', None, 123])
    def test_delete_profile_validation_error(self, sandbox_mgr: SandboxMgr, profile_id):
        with pytest.raises(ValidationError):
            sandbox_mgr.delete_profile(profile_id=profile_id)

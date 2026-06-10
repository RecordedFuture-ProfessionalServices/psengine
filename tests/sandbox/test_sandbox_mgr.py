import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from requests import ConnectionError, ConnectTimeout, HTTPError, ReadTimeout  # noqa: A004
from requests.models import Response

from psengine.endpoints import (
    EP_SANDBOX_PROFILES,
    EP_SANDBOX_PROFILES_ID,
    EP_SANDBOX_SAMPLES,
    EP_SANDBOX_SAMPLES_DOWNLOAD,
    EP_SANDBOX_SAMPLES_ID,
    EP_SANDBOX_SAMPLES_PROFILE,
    EP_SANDBOX_SAMPLES_STATIC_REPORT,
    EP_SANDBOX_SAMPLES_SUMMARY,
    EP_SANDBOX_SEARCH,
    SANDBOX_BASE_URLS,
)
from psengine.sandbox import (
    Profile,
    ProfileOptions,
    SampleProfileOut,
    SandboxMgr,
    StaticAnalysisReport,
)
from psengine.sandbox.errors import (
    ProfileCreateError,
    ProfileDeleteError,
    ProfileFetchError,
    ProfileNotFoundError,
    ProfileUpdateError,
    SampleDeleteError,
    SampleFetchError,
    SampleFileFetchError,
    SampleProfileError,
    SampleSearchError,
    SamplesFetchError,
    SampleStaticReportError,
    SampleSubmitError,
    SampleSummaryError,
)
from psengine.sandbox.sandbox import (
    SampleTasks,
    SampleSummary,
    Sample,
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

    @pytest.mark.parametrize('choice', ['eu', 'usa', 'apj', 'public', 'private'])
    def test_sandbox_choice_valid(self, choice):
        mgr = SandboxMgr(sandbox_choice=choice)
        assert mgr.base_url == SANDBOX_BASE_URLS[choice]

    @pytest.mark.parametrize('choice', ['invalid-sandbox', '', 'EU'])
    def test_sandbox_choice_invalid_raises_value_error(self, choice):
        with pytest.raises(ValueError):
            SandboxMgr(sandbox_choice=choice)

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

        assert result.updated is True
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

        assert result.updated is False

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

        assert result.deleted is True
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

        assert result.deleted is False

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

    # --- sample methods ----------------------------------------------------

    def test_fetch_sample_summary_happy_path(self, sandbox_mgr: SandboxMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'sample_summary.json')
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        result = sandbox_mgr.fetch_sample_summary('260515-nta8kscxnf')

        assert isinstance(result, SampleSummary)
        assert result.sample == '260515-nta8kscxnf'
        assert mocked.call_args.args == (
            'get',
            EP_SANDBOX_SAMPLES_SUMMARY.format(
                base_url=sandbox_mgr.base_url, sample_id='260515-nta8kscxnf'
            ),
        )

    def test_fetch_sample_summary_normalises_task_keys(
        self, sandbox_mgr: SandboxMgr, mocker, mock_request
    ):
        # Wire keys carry the `<sample_id>-` prefix; SampleSummary.normalize_task_keys
        # strips that. The captured fixture has `260515-nta8kscxnf-static1` / `-behavioral1`.
        mock = mock_request(MOCK_DIR / 'sample_summary.json')
        mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        result = sandbox_mgr.fetch_sample_summary('260515-nta8kscxnf')

        assert set(result.tasks) == {'static1', 'behavioral1'}

    @pytest.mark.parametrize('sample_id', [None, 123])
    def test_fetch_sample_summary_validation_error(self, sandbox_mgr: SandboxMgr, sample_id):
        # NOTE: `fetch_sample_summary`'s `sample_id` parameter lacks `Field(min_length=1)`
        # (unlike fetch_sample/delete_sample), so `''` passes type validation here
        # and would hit the network. Only non-str types raise ValidationError.
        with pytest.raises(ValidationError):
            sandbox_mgr.fetch_sample_summary(sample_id)

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_fetch_sample_summary_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        err = _http_error(500) if exception is HTTPError else exception('boom')
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=err)

        with pytest.raises(SampleSummaryError):
            sandbox_mgr.fetch_sample_summary('any-id')

    def test_search_samples_happy_path(self, sandbox_mgr: SandboxMgr, mocker):
        page = json.loads((MOCK_DIR / 'sample_list_page.json').read_text())
        mocked = mocker.patch.object(
            sandbox_mgr.sb_client, 'request_paged', return_value=page['data']
        )

        results = sandbox_mgr.search_samples(tag='malware')

        assert isinstance(results, list)
        assert len(results) == len(page['data'])
        assert all(isinstance(r, Sample) for r in results)
        assert mocked.call_args.args[:2] == (
            'get',
            EP_SANDBOX_SEARCH.format(base_url=sandbox_mgr.base_url),
        )
        # SearchIn.to_query_out() builds the query string with the field prefix.
        assert mocked.call_args.kwargs['params'] == {'query': 'tag:malware'}

    def test_search_samples_query_string_composition(self, sandbox_mgr: SandboxMgr, mocker):
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request_paged', return_value=[])

        sandbox_mgr.search_samples(tag='malware', family='zeus')

        # Order in the AND-joined string is the SearchIn field-declaration order.
        assert mocked.call_args.kwargs['params'] == {'query': 'family:zeus AND tag:malware'}

    def test_search_samples_bare_query_appended(self, sandbox_mgr: SandboxMgr, mocker):
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request_paged', return_value=[])

        sandbox_mgr.search_samples(tag='malware', query='extra-text')

        assert mocked.call_args.kwargs['params']['query'].endswith('extra-text')
        assert 'tag:malware' in mocked.call_args.kwargs['params']['query']

    def test_search_samples_empty_result(self, sandbox_mgr: SandboxMgr, mocker):
        mocker.patch.object(sandbox_mgr.sb_client, 'request_paged', return_value=[])

        assert sandbox_mgr.search_samples(tag='nothing-here') == []

    def test_search_samples_forwards_pagination_kwargs(self, sandbox_mgr: SandboxMgr, mocker):
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request_paged', return_value=[])

        sandbox_mgr.search_samples(tag='malware', max_results=42, results_per_page=17)

        assert mocked.call_args.kwargs['max_results'] == 42
        assert mocked.call_args.kwargs['results_per_page'] == 17

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_search_samples_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        err = _http_error(500) if exception is HTTPError else exception('boom')
        mocker.patch.object(sandbox_mgr.sb_client, 'request_paged', side_effect=err)

        with pytest.raises(SampleSearchError):
            sandbox_mgr.search_samples(tag='anything')

    def test_fetch_samples_happy_path(self, sandbox_mgr: SandboxMgr, mocker):
        page = json.loads((MOCK_DIR / 'sample_list_page.json').read_text())
        mocked = mocker.patch.object(
            sandbox_mgr.sb_client, 'request_paged', return_value=page['data']
        )

        results = sandbox_mgr.fetch_samples()

        assert isinstance(results, list)
        assert len(results) == len(page['data'])
        assert all(isinstance(r, Sample) for r in results)
        assert mocked.call_args.args[:2] == (
            'get',
            EP_SANDBOX_SAMPLES.format(base_url=sandbox_mgr.base_url),
        )
        assert mocked.call_args.kwargs['params'] == {'subset': 'owned'}

    def test_fetch_samples_non_default_subset(self, sandbox_mgr: SandboxMgr, mocker):
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request_paged', return_value=[])

        sandbox_mgr.fetch_samples(subset='public')

        assert mocked.call_args.kwargs['params'] == {'subset': 'public'}

    @pytest.mark.parametrize(
        'kwargs',
        [
            {'subset': 'invalid'},
            {'max_results': 0},
            {'samples_per_page': 0},
            {'samples_per_page': 201},
        ],
    )
    def test_fetch_samples_validation_errors(self, sandbox_mgr: SandboxMgr, kwargs):
        with pytest.raises(ValidationError):
            sandbox_mgr.fetch_samples(**kwargs)

    def test_fetch_samples_empty_result(self, sandbox_mgr: SandboxMgr, mocker):
        mocker.patch.object(sandbox_mgr.sb_client, 'request_paged', return_value=[])

        assert sandbox_mgr.fetch_samples() == []

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_fetch_samples_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        err = _http_error(500) if exception is HTTPError else exception('boom')
        mocker.patch.object(sandbox_mgr.sb_client, 'request_paged', side_effect=err)

        with pytest.raises(SamplesFetchError):
            sandbox_mgr.fetch_samples()

    def test_fetch_sample_happy_path(self, sandbox_mgr: SandboxMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'sample_single.json')
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        sample = sandbox_mgr.fetch_sample('260515-nta8kscxnf')

        assert isinstance(sample, SampleTasks)
        assert sample.id_ == '260515-nta8kscxnf'
        assert mocked.call_args.args == (
            'get',
            EP_SANDBOX_SAMPLES_ID.format(
                base_url=sandbox_mgr.base_url, sample_id='260515-nta8kscxnf'
            ),
        )

    def test_fetch_sample_404_raises_fetch_error(self, sandbox_mgr: SandboxMgr, mocker):
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=_http_error(404))

        with pytest.raises(SampleFetchError):
            sandbox_mgr.fetch_sample('missing')

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_fetch_sample_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        err = _http_error(500) if exception is HTTPError else exception('boom')
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=err)

        with pytest.raises(SampleFetchError):
            sandbox_mgr.fetch_sample('any-id')

    @pytest.mark.parametrize('sample_id', ['', None, 123])
    def test_fetch_sample_validation_error(self, sandbox_mgr: SandboxMgr, sample_id):
        with pytest.raises(ValidationError):
            sandbox_mgr.fetch_sample(sample_id)

    def test_fetch_sample_file_happy_path(
        self, sandbox_mgr: SandboxMgr, mocker, make_binary_response
    ):
        # The endpoint returns raw octet-stream bytes with no filename header,
        # so the manager returns response.content verbatim.
        mock = make_binary_response(b'\x50\x4b\x03\x04rawbytes', {})
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        content = sandbox_mgr.fetch_sample_file('260515-nta8kscxnf')

        assert content == b'\x50\x4b\x03\x04rawbytes'
        assert mocked.call_args.args == (
            'get',
            EP_SANDBOX_SAMPLES_DOWNLOAD.format(
                base_url=sandbox_mgr.base_url, sample_id='260515-nta8kscxnf'
            ),
        )

    def test_fetch_sample_file_404_raises_fetch_error(self, sandbox_mgr: SandboxMgr, mocker):
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=_http_error(404))

        with pytest.raises(SampleFileFetchError):
            sandbox_mgr.fetch_sample_file('missing')

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_fetch_sample_file_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        err = _http_error(500) if exception is HTTPError else exception('boom')
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=err)

        with pytest.raises(SampleFileFetchError):
            sandbox_mgr.fetch_sample_file('any-id')

    @pytest.mark.parametrize('sample_id', ['', None, 123])
    def test_fetch_sample_file_validation_error(self, sandbox_mgr: SandboxMgr, sample_id):
        with pytest.raises(ValidationError):
            sandbox_mgr.fetch_sample_file(sample_id)

    def test_fetch_sample_static_report_simple(self, sandbox_mgr: SandboxMgr, mocker, mock_request):
        # static_report_simple.json is a real capture of a single-file (CSV) sample:
        # no signatures, one file at depth 0, nothing unpacked.
        mock = mock_request(MOCK_DIR / 'static_report_simple.json')
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        report = sandbox_mgr.fetch_sample_static_report('260529-q2zl9abwxw')

        assert isinstance(report, StaticAnalysisReport)
        assert report.sample.sample == '260529-q2zl9abwxw'
        assert report.sample.target == 'ca.csv'
        assert report.analysis.score == 1
        assert report.signatures == []
        assert len(report.files) == 1
        assert report.files[0].sha256.startswith('51bcb923')
        assert report.unpack_count == 0
        assert mocked.call_args.args == (
            'get',
            EP_SANDBOX_SAMPLES_STATIC_REPORT.format(
                base_url=sandbox_mgr.base_url, sample_id='260529-q2zl9abwxw'
            ),
        )

    def test_fetch_sample_static_report_archive(
        self, sandbox_mgr: SandboxMgr, mocker, mock_request
    ):
        # static_report_archive.json is a real capture of a zip submission: it carries
        # signatures, analysis tags, and an unpacked files table with per-file errors.
        mock = mock_request(MOCK_DIR / 'static_report_archive.json')
        mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        report = sandbox_mgr.fetch_sample_static_report('260529-raphmsb1e5')

        assert report.analysis.score == 5
        assert report.analysis.tags == ['pdf']
        assert [s.name for s in report.signatures] == ['Malformed data in PDF']
        archive = next(f for f in report.files if f.kind == 'archive')
        assert archive.exts == ['.zip']
        # A child file with relpath, ssdeep and an analysis error round-trips.
        errored = next(f for f in report.files if f.error)
        assert errored.relpath is not None
        assert errored.error.startswith('PDF crash')

    def test_fetch_sample_static_report_404_raises(self, sandbox_mgr: SandboxMgr, mocker):
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=_http_error(404))

        with pytest.raises(SampleStaticReportError):
            sandbox_mgr.fetch_sample_static_report('missing')

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_fetch_sample_static_report_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        err = _http_error(500) if exception is HTTPError else exception('boom')
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=err)

        with pytest.raises(SampleStaticReportError):
            sandbox_mgr.fetch_sample_static_report('any-id')

    @pytest.mark.parametrize('sample_id', ['', None, 123])
    def test_fetch_sample_static_report_validation_error(self, sandbox_mgr: SandboxMgr, sample_id):
        with pytest.raises(ValidationError):
            sandbox_mgr.fetch_sample_static_report(sample_id)

    # --- set_sample_profile ------------------------------------------------

    def test_set_sample_profile_auto_default_pick(self, sandbox_mgr: SandboxMgr, mocker):
        # auto=True with no pick -> empty list (advance all targets).
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mocker.Mock())

        result = sandbox_mgr.set_sample_profile('260529-szm7jsc1b3', auto=True)

        assert isinstance(result, SampleProfileOut)
        assert result.success is True
        assert mocked.call_args.args == (
            'post',
            EP_SANDBOX_SAMPLES_PROFILE.format(
                base_url=sandbox_mgr.base_url, sample_id='260529-szm7jsc1b3'
            ),
        )
        assert mocked.call_args.kwargs['data'] == {'auto': True, 'pick': []}

    def test_set_sample_profile_auto_with_pick(self, sandbox_mgr: SandboxMgr, mocker):
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mocker.Mock())

        sandbox_mgr.set_sample_profile('sid', auto=True, pick=['unpack001/a.txt'])

        assert mocked.call_args.kwargs['data'] == {'auto': True, 'pick': ['unpack001/a.txt']}

    def test_set_sample_profile_manual_string_profile_wrapped(
        self, sandbox_mgr: SandboxMgr, mocker
    ):
        # A string profile (id or name) is wrapped into the {"id": ...} object.
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mocker.Mock())

        sandbox_mgr.set_sample_profile(
            'sid', profiles=[{'pick': 'unpack001/a.txt', 'profile': 'drew-test'}]
        )

        assert mocked.call_args.kwargs['data'] == {
            'auto': False,
            'profiles': [{'pick': 'unpack001/a.txt', 'profile': {'id': 'drew-test'}}],
        }

    def test_set_sample_profile_manual_dict_profile_passthrough(
        self, sandbox_mgr: SandboxMgr, mocker
    ):
        # A dict profile is sent verbatim (no wrapping).
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mocker.Mock())

        sandbox_mgr.set_sample_profile(
            'sid', profiles=[{'pick': 'unpack001/a.txt', 'profile': {'name': 'drew-test'}}]
        )

        assert mocked.call_args.kwargs['data'] == {
            'auto': False,
            'profiles': [{'pick': 'unpack001/a.txt', 'profile': {'name': 'drew-test'}}],
        }

    @pytest.mark.parametrize(
        'kwargs',
        [
            {},  # auto=False (default) but no profiles
            {'auto': False},  # explicit, still no profiles
            {'auto': False, 'pick': ['a']},  # pick only valid with auto=True
            {'auto': True, 'profiles': [{'pick': 'a', 'profile': 'p'}]},  # profiles with auto
        ],
    )
    def test_set_sample_profile_invalid_combinations(self, sandbox_mgr: SandboxMgr, mocker, kwargs):
        mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mocker.Mock())
        with pytest.raises(ValidationError):
            sandbox_mgr.set_sample_profile('sid', **kwargs)

    def test_set_sample_profile_400_raises(self, sandbox_mgr: SandboxMgr, mocker):
        # e.g. the sample is not paused in static_analysis.
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=_http_error(400))

        with pytest.raises(SampleProfileError):
            sandbox_mgr.set_sample_profile('sid', auto=True)

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_set_sample_profile_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        err = _http_error(500) if exception is HTTPError else exception('boom')
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=err)

        with pytest.raises(SampleProfileError):
            sandbox_mgr.set_sample_profile('sid', auto=True)

    @pytest.mark.parametrize('sample_id', ['', None, 123])
    def test_set_sample_profile_sample_id_validation(self, sandbox_mgr: SandboxMgr, sample_id):
        with pytest.raises(ValidationError):
            sandbox_mgr.set_sample_profile(sample_id, auto=True)

    def test_submit_sample_url_kind(self, sandbox_mgr: SandboxMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'sample_submit_url.json')
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        result = sandbox_mgr.submit_sample(kind='url', url='https://example.com')

        assert isinstance(result, Sample)
        assert mocked.call_args.args == (
            'post',
            EP_SANDBOX_SAMPLES.format(base_url=sandbox_mgr.base_url),
        )
        assert 'data' not in mocked.call_args.kwargs
        files = mocked.call_args.kwargs['files']
        body = json.loads(files['_json'][1])
        assert body == {'kind': 'url', 'url': 'https://example.com'}
        assert 'file' not in files

    def test_submit_sample_fetch_kind(self, sandbox_mgr: SandboxMgr, mocker, make_response):
        mocked = mocker.patch.object(
            sandbox_mgr.sb_client,
            'request',
            return_value=make_response(
                {
                    'id': 'x',
                    'kind': 'file',
                    'status': 'pending',
                    'submitted': '2026-05-15T11:40:51Z',
                    'user_id': 'u',
                }
            ),
        )

        sandbox_mgr.submit_sample(kind='fetch', url='https://example.com/foo.bin')

        body = json.loads(mocked.call_args.kwargs['files']['_json'][1])
        assert body == {'kind': 'fetch', 'url': 'https://example.com/foo.bin'}
        assert 'file' not in mocked.call_args.kwargs['files']

    def test_submit_sample_import_kind_maps_source_id_to_url(
        self, sandbox_mgr: SandboxMgr, mocker, make_response
    ):
        mocked = mocker.patch.object(
            sandbox_mgr.sb_client,
            'request',
            return_value=make_response(
                {
                    'id': 'x',
                    'kind': 'file',
                    'status': 'pending',
                    'submitted': '2026-05-15T11:40:51Z',
                    'user_id': 'u',
                }
            ),
        )

        sandbox_mgr.submit_sample(kind='import', source_id='260501-h4p7laawme')

        body = json.loads(mocked.call_args.kwargs['files']['_json'][1])
        # source_id is carried in the API's `url` field, not as `source_id`.
        assert body == {'kind': 'import', 'url': '260501-h4p7laawme'}

    def test_submit_sample_file_kind_carries_file_part(
        self, sandbox_mgr: SandboxMgr, mocker, make_response, tmp_path
    ):
        sample_file = tmp_path / 'payload.bin'
        sample_file.write_bytes(b'malware-bytes')

        mocked = mocker.patch.object(
            sandbox_mgr.sb_client,
            'request',
            return_value=make_response(
                {
                    'id': 'x',
                    'kind': 'file',
                    'filename': 'payload.bin',
                    'status': 'pending',
                    'submitted': '2026-05-15T11:40:51Z',
                    'user_id': 'u',
                }
            ),
        )

        sandbox_mgr.submit_sample(kind='file', file_path=sample_file)

        files = mocked.call_args.kwargs['files']
        body = json.loads(files['_json'][1])
        assert body == {'kind': 'file'}
        assert files['file'] == ('payload.bin', b'malware-bytes', 'application/octet-stream')

    def test_submit_sample_defaults_nesting(self, sandbox_mgr: SandboxMgr, mocker, make_response):
        mocked = mocker.patch.object(
            sandbox_mgr.sb_client,
            'request',
            return_value=make_response(
                {
                    'id': 'x',
                    'kind': 'url',
                    'status': 'pending',
                    'submitted': '2026-05-15T11:40:51Z',
                    'user_id': 'u',
                }
            ),
        )

        sandbox_mgr.submit_sample(
            kind='url',
            url='https://example.com',
            timeout=60,
            network='vpn',
            geolocation='us',
        )

        body = json.loads(mocked.call_args.kwargs['files']['_json'][1])
        # timeout/network/geolocation go under `defaults`, not top-level.
        assert body['defaults'] == {'timeout': 60, 'network': 'vpn', 'geolocation': 'us'}
        assert 'timeout' not in body
        assert 'network' not in body
        assert 'geolocation' not in body

    def test_submit_sample_user_tags_str_coerced_to_list(
        self, sandbox_mgr: SandboxMgr, mocker, make_response
    ):
        mocked = mocker.patch.object(
            sandbox_mgr.sb_client,
            'request',
            return_value=make_response(
                {
                    'id': 'x',
                    'kind': 'url',
                    'status': 'pending',
                    'submitted': '2026-05-15T11:40:51Z',
                    'user_id': 'u',
                }
            ),
        )

        sandbox_mgr.submit_sample(kind='url', url='https://example.com', user_tags='foo')

        body = json.loads(mocked.call_args.kwargs['files']['_json'][1])
        assert body['user_tags'] == ['foo']

    @pytest.mark.parametrize(
        ('kwargs', 'reason'),
        [
            # missing-per-kind
            ({'kind': 'file'}, 'kind=file requires file_path'),
            ({'kind': 'url'}, 'kind=url requires url'),
            ({'kind': 'fetch'}, 'kind=fetch requires url'),
            ({'kind': 'import'}, 'kind=import requires source_id'),
            # cross-kind exclusivity
            (
                {'kind': 'url', 'url': 'https://x', 'source_id': 'y'},
                'source_id only valid for import',
            ),
            (
                {'kind': 'import', 'source_id': 'y', 'url': 'https://x'},
                'url only valid for url/fetch',
            ),
            # geolocation requires vpn network
            (
                {'kind': 'url', 'url': 'https://x', 'geolocation': 'us', 'network': 'internet'},
                'geolocation requires network=vpn',
            ),
        ],
    )
    def test_submit_sample_validation_errors(self, sandbox_mgr: SandboxMgr, kwargs, reason):
        # All these are caught by SubmitSampleIn model_validators -> ValidationError
        # before any HTTP request is made. `reason` is included for readability
        # in the parametrized test ID.
        del reason
        with pytest.raises(ValidationError):
            sandbox_mgr.submit_sample(**kwargs)

    def test_submit_sample_file_path_must_exist(self, sandbox_mgr: SandboxMgr, tmp_path):
        missing = tmp_path / 'does-not-exist.bin'

        with pytest.raises(ValidationError):
            sandbox_mgr.submit_sample(kind='file', file_path=missing)

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_submit_sample_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        err = _http_error(500) if exception is HTTPError else exception('boom')
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=err)

        with pytest.raises(SampleSubmitError):
            sandbox_mgr.submit_sample(kind='url', url='https://example.com')

    @pytest.mark.parametrize('status_code', [400, 401, 409, 500])
    def test_submit_sample_raises_on_4xx_5xx(self, sandbox_mgr: SandboxMgr, mocker, status_code):
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=_http_error(status_code))

        with pytest.raises(SampleSubmitError):
            sandbox_mgr.submit_sample(kind='url', url='https://example.com')

    def test_delete_sample_happy_path(self, sandbox_mgr: SandboxMgr, mocker, make_response):
        mock = make_response({})
        mocked = mocker.patch.object(sandbox_mgr.sb_client, 'request', return_value=mock)

        result = sandbox_mgr.delete_sample(sample_id='260515-nta8kscxnf')

        assert result.deleted is True
        assert mocked.call_args.args == (
            'delete',
            EP_SANDBOX_SAMPLES_ID.format(
                base_url=sandbox_mgr.base_url, sample_id='260515-nta8kscxnf'
            ),
        )
        assert 'data' not in mocked.call_args.kwargs

    @pytest.mark.parametrize('sample_id', ['', None, 123])
    def test_delete_sample_validation_error(self, sandbox_mgr: SandboxMgr, sample_id):
        with pytest.raises(ValidationError):
            sandbox_mgr.delete_sample(sample_id=sample_id)

    @pytest.mark.parametrize(
        'status_code',
        # 401 is included on purpose: the Triage API returns it for every
        # non-success outcome (already deleted, never existed, no permission,
        # expired token). delete_sample has no idempotency, so all of these raise.
        [400, 401, 404, 500],
    )
    def test_delete_sample_non_2xx_raises(self, sandbox_mgr: SandboxMgr, mocker, status_code):
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=_http_error(status_code))

        with pytest.raises(SampleDeleteError):
            sandbox_mgr.delete_sample(sample_id='260515-nta8kscxnf')

    @pytest.mark.parametrize('exception', [ConnectTimeout, ConnectionError, ReadTimeout])
    def test_delete_sample_raises_on_connection_errors(
        self, sandbox_mgr: SandboxMgr, exception, mocker
    ):
        mocker.patch.object(sandbox_mgr.sb_client, 'request', side_effect=exception('boom'))

        with pytest.raises(SampleDeleteError):
            sandbox_mgr.delete_sample(sample_id='260515-nta8kscxnf')

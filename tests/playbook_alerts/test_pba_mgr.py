import re
from enum import Enum
from pathlib import Path
from unittest import mock

import pytest
from pydantic import ValidationError
from requests import Response
from requests.exceptions import HTTPError

from psengine.constants import DEFAULT_LIMIT
from psengine.errors import WriteFileError
from psengine.playbook_alerts import (
    PACategory,
    PBA_DomainAbuse,
    PBA_Generic,
    PlaybookAlertFetchError,
    PlaybookAlertMgr,
    PlaybookAlertRetrieveImageError,
    PlaybookAlertUpdateError,
    SearchIn,
)
from psengine.playbook_alerts.errors import PlaybookAlertBulkFetchError
from psengine.playbook_alerts.helpers import _save_image, save_pba_images
from tests.playbook_alerts.conftest import MGR_MOCK


class Test_PlaybookAlertMgr:
    ### <Fetch alert>
    def test_fetch_raises_PlaybookAlertFetchError(self, playbook_mgr, mocker):
        response = Response()
        response.status_code = 400
        excp_obj = HTTPError('error')
        excp_obj.response = response
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=excp_obj)

        with pytest.raises(PlaybookAlertFetchError):
            playbook_mgr.fetch(
                alert_id='task:98cfabbb-ad68-4daf-a8d8-wrong-id',
                category=PACategory.DOMAIN_ABUSE.value,
            )

    test_params = [
        {'category': 'domain_abusers', 'alert_id': 'task:27547e1e-a235-41f2-bb50-d33c1befad21'},
        {'category': None, 'alert_id': None},
        {'category': PACategory.DOMAIN_ABUSE.value, 'alert_id': None},
    ]

    @pytest.mark.parametrize('kwargs', test_params)
    def test_fetch_raises_ValidationError(self, kwargs, playbook_mgr):
        with pytest.raises(ValidationError):
            playbook_mgr.fetch(**kwargs)

    def test_fetch_without_category_supported_alert(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(MGR_MOCK / 'test_fetch_without_category_supported_alert_0.json'),
            mock_request(MGR_MOCK / 'test_fetch_without_category_supported_alert_1.json'),
            make_binary_response(
                MGR_MOCK / 'test_fetch_without_category_supported_alert_2.file', {}
            ),
            make_binary_response(
                MGR_MOCK / 'test_fetch_without_category_supported_alert_3.file', {}
            ),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)
        mocker_fetch = mocker.spy(playbook_mgr, '_fetch_alert_category')
        p_alert = playbook_mgr.fetch(
            alert_id='task:27547e1e-a235-41f2-bb50-d33c1befad21',
        )
        assert isinstance(p_alert, PBA_DomainAbuse)
        assert mocker_fetch.spy_return.value == 'domain_abuse'

    def test_fetch_without_category_unsupported_alert(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        class PACategoryFake(Enum):
            CYBER_VULNERABILITY = 'cyber_vulnerability'

        mock = mock_request(MGR_MOCK / 'test_fetch_without_category_unsupported_alert_0.json')
        mocker.patch.object(playbook_mgr.rf_client, 'request', return_value=mock)
        mocker.patch('psengine.playbook_alerts.playbook_alert_mgr.PACategory', PACategoryFake)
        with pytest.raises(ValueError, match=r'Unsupported playbook alert category.*'):
            playbook_mgr.fetch(alert_id='task:27547e1e-a235-41f2-bb50-d33c1befad21')

    def test_fetch_returns_alert_obj(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(MGR_MOCK / 'test_fetch_returns_alert_obj_0.json'),
            make_binary_response(MGR_MOCK / 'test_fetch_returns_alert_obj_1.file', {}),
            make_binary_response(MGR_MOCK / 'test_fetch_returns_alert_obj_2.file', {}),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        p_alert = playbook_mgr.fetch(
            category=PACategory.DOMAIN_ABUSE.value,
            alert_id='task:27547e1e-a235-41f2-bb50-d33c1befad21',
        )
        assert isinstance(p_alert, PBA_Generic)
        assert isinstance(p_alert, PBA_DomainAbuse)
        assert p_alert.playbook_alert_id == 'task:27547e1e-a235-41f2-bb50-d33c1befad21'
        assert p_alert.category == PACategory.DOMAIN_ABUSE.value

    def test_fetch_for_specific_panel(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(MGR_MOCK / 'test_fetch_for_specific_panel_0.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        mocker_fetch = mocker.spy(playbook_mgr, 'fetch')
        mocker_client = mocker.spy(playbook_mgr.rf_client, 'request')
        p_alert = playbook_mgr.fetch(
            category=PACategory.DOMAIN_ABUSE.value,
            alert_id='task:27547e1e-a235-41f2-bb50-d33c1befad21',
            panels=['evidence'],
        )
        assert sorted(mocker_client.call_args[1]['data']['panels']) == sorted(
            ['status', 'evidence']
        )
        assert mocker_fetch.call_args[1]['panels'] == ['evidence']
        assert isinstance(p_alert, PBA_DomainAbuse)

    @pytest.mark.parametrize('panel', ['status', 'action', 'summary', 'dns', 'whois', 'log'])
    def test_fetch_for_each_panel(
        self, playbook_mgr: PlaybookAlertMgr, panel, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_fetch_for_each_panel\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(MGR_MOCK).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        mocker_fetch = mocker.spy(playbook_mgr, 'fetch')
        mocker_post = mocker.spy(playbook_mgr.rf_client, 'request')
        p_alert = playbook_mgr.fetch(
            category=PACategory.DOMAIN_ABUSE.value,
            alert_id='task:27547e1e-a235-41f2-bb50-d33c1befad21',
            panels=[panel],
            fetch_images=False,
        )
        assert isinstance(p_alert, PBA_DomainAbuse)
        assert mocker_fetch.call_args[1]['panels'] == [panel]
        assert sorted(mocker_post.call_args[1]['data']['panels']) == sorted({'status', panel})

    ### </Fetch alert>

    ### <Fetch bulk alert>
    test_params = [
        ('limit', [56]),
        ('limit', -23),
        ('limit', 'hundred'),
        ('fetch_image', 'meow'),
        ('statuses', 1),
        ('category', 1),
        ('priority', 1),
        ('category', 'unknown_category'),
    ]

    @pytest.mark.parametrize(('setting', 'value'), test_params)
    def test_fetch_bulk_validation_errors(self, playbook_mgr: PlaybookAlertMgr, setting, value):
        with pytest.raises(ValidationError):
            playbook_mgr.fetch_bulk(**{setting: value})

    def test_fetch_bulk_validation_error_on_category_with_alert(
        self, playbook_mgr: PlaybookAlertMgr
    ):
        with pytest.raises(ValidationError):
            playbook_mgr.fetch_bulk(
                alerts=[('task:27547e1e-a235-41f2-bb50-d33c1befad21', 'unknown_category')]
            )

    def test_fetch_bulk_for_specific_panel(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [
            mock_request(MGR_MOCK / 'test_fetch_bulk_for_specific_panel_0.json'),
            mock_request(MGR_MOCK / 'test_fetch_bulk_for_specific_panel_1.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)
        mocker_fetch = mocker.spy(playbook_mgr, 'fetch_bulk')
        mocker_post = mocker.spy(playbook_mgr.rf_client, 'request')
        p_alerts = playbook_mgr.fetch_bulk(
            category=PACategory.DOMAIN_ABUSE.value, panels=['evidence'], max_results=2
        )
        assert sorted(mocker_post.call_args[1]['data']['panels']) == sorted(['status', 'evidence'])
        assert mocker_fetch.call_args[1]['panels'] == ['evidence']
        assert all(isinstance(p_alert, PBA_DomainAbuse) for p_alert in p_alerts)

    def test_fetch_bulk_success(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(MGR_MOCK / 'test_fetch_bulk_success_0.json'),
            mock_request(MGR_MOCK / 'test_fetch_bulk_success_1.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)
        alerts = playbook_mgr.fetch_bulk()
        assert isinstance(alerts, list)
        assert len(alerts) > 0
        assert all(isinstance(alert, PBA_Generic) for alert in alerts)

    @pytest.mark.parametrize(
        'error', [PlaybookAlertBulkFetchError, PlaybookAlertRetrieveImageError]
    )
    def test_fetch_bulk_error_count(
        self, playbook_mgr: PlaybookAlertMgr, mocker, error, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_fetch_bulk_error_count\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(MGR_MOCK).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        mocker.patch.object(PlaybookAlertMgr, '_do_bulk').side_effect = error('Error')
        mocker.patch.object(playbook_mgr, 'log')

        with pytest.raises(PlaybookAlertFetchError):
            playbook_mgr.fetch_bulk()

        playbook_mgr.log.error.assert_called_with(
            'Failed to fetch alerts due to 2 error(s). See errors above',
        )

    def test_fetch_bulk_with_search_results(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [
            mock_request(MGR_MOCK / 'test_fetch_bulk_with_search_results_0.json'),
            mock_request(MGR_MOCK / 'test_fetch_bulk_with_search_results_1.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        search_results = playbook_mgr.search()
        ids_and_cats = [(alert.playbook_alert_id, alert.category) for alert in search_results.data]
        alerts = playbook_mgr.fetch_bulk(alerts=ids_and_cats)
        assert len(alerts) == search_results.counts.returned

    ### </Fetch bulk alert>

    ### <Search alert>
    def test_search_empty_success(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(MGR_MOCK / 'test_search_empty_success_0.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        search_results = playbook_mgr.search()
        assert search_results
        assert len(search_results.data) > 0

    def test_search_raise_ValidationError_wrong_category(self, playbook_mgr: PlaybookAlertMgr):
        with pytest.raises(ValidationError):
            playbook_mgr.search(category=['unknown_category'])

    def test_search_add_all_categories(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(MGR_MOCK / 'test_search_add_all_categories_0.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        mocker_req = mocker.spy(playbook_mgr.rf_client, 'request')
        playbook_mgr.search()
        assert sorted(mocker_req.call_args[1]['data']['category']) == sorted(
            c.value for c in PACategory
        )

    def test_search_alerts_per_page_with_max_results(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [
            mock_request(MGR_MOCK / 'test_search_alerts_per_page_with_max_results_0.json'),
            mock_request(MGR_MOCK / 'test_search_alerts_per_page_with_max_results_1.json'),
            mock_request(MGR_MOCK / 'test_search_alerts_per_page_with_max_results_2.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        search_results = playbook_mgr.search(max_results=5, alerts_per_page=2)
        assert search_results.counts.returned == 5
        assert len(search_results.data) == 5

    ### </Search alert>

    ### <Update alert>
    def test_update_raises_PlaybookAlertUpdateError(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        response = Response()
        response.status_code = 400
        excp_obj = HTTPError('error')
        excp_obj.response = response

        mocks = [
            mock_request(MGR_MOCK / 'test_update_raises_PlaybookAlertUpdateError_0.json'),
            mock_request(MGR_MOCK / 'test_update_raises_PlaybookAlertUpdateError_1.json'),
            excp_obj,
            excp_obj,
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        alert = playbook_mgr.fetch('task:27547e1e-a235-41f2-bb50-d33c1befad21', fetch_images=False)

        with pytest.raises(PlaybookAlertUpdateError):
            playbook_mgr.update(alert, priority='invalid')

        with pytest.raises(PlaybookAlertUpdateError):
            playbook_mgr.update(alert, status='no-progress')

    def test_update(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(MGR_MOCK / 'test_update_0.json'),
            mock_request(MGR_MOCK / 'test_update_1.json'),
            mock_request(MGR_MOCK / 'test_update_4.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        alert = playbook_mgr.fetch('task:27547e1e-a235-41f2-bb50-d33c1befad21', fetch_images=False)

        playbook_mgr.update(
            alert,
            priority='High',
            status='InProgress',
            assignee='uhash:3aXZxdkMck',
            log_entry='hola from the unit tests ;)',
        )

    def test_update_takes_alert_id(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(MGR_MOCK / 'test_update_takes_alert_id_0.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        playbook_mgr.update(
            'task:27547e1e-a235-41f2-bb50-d33c1befad21',
            priority='High',
            status='InProgress',
            log_entry='wowawewa, update with an alert id',
        )

    def test_update_reopen_strategy(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(MGR_MOCK / 'test_update_reopen_strategy_0.json'),
            mock_request(MGR_MOCK / 'test_update_reopen_strategy_1.json'),
            mock_request(MGR_MOCK / 'test_update_reopen_strategy_3.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        alert = playbook_mgr.fetch('task:7fcd943b-7c7e-436f-a391-01f797334bc5', fetch_images=False)
        playbook_mgr.update(alert, status='Dismissed', reopen_strategy='Never')

    def test_update_alert_obj(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(MGR_MOCK / 'test_update_alert_obj_0.json'),
            mock_request(MGR_MOCK / 'test_update_alert_obj_3.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        p_alert = playbook_mgr.fetch(
            category=PACategory.DOMAIN_ABUSE.value,
            alert_id='task:27547e1e-a235-41f2-bb50-d33c1befad21',
            fetch_images=False,
        )
        playbook_mgr.update(alert=p_alert, priority='High', status='InProgress')

    def test_update_raises_ValueError(self, playbook_mgr: PlaybookAlertMgr):
        with pytest.raises(ValueError, match='No update parameters were supplied'):
            playbook_mgr.update('alert', *(None,) * 4)

    ### </Update alert>

    ### <Alert Factory>
    def test_playbook_alert_factory_unknown_category(self):
        playbook_mgr = PlaybookAlertMgr()
        with pytest.raises(KeyError):
            # In theory the alert factory should not be called directly,
            # only public fuctions call it downstream and they already have
            # the category checked, so factory is always called with a valid category.
            playbook_mgr._playbook_alert_factory(
                'unknown',
                {
                    'playbook_alert_id': 'task:1234',
                    'panel_status': {
                        'case_rule_label': 'Domain Abuse',
                        'status': 'New',
                        'priority': 'Moderate',
                        'created': '2024-08-01T22:53:59.940Z',
                        'updated': '2024-08-01T22:57:14.685Z',
                        'actions_taken': [],
                    },
                },
            )

    def test_playbook_alert_factory_validation_fails(self, playbook_mgr: PlaybookAlertMgr):
        broken_alert = {
            'playbook_alert_id': 'task:bd2c8e27-e3c4-45fe-a7c9-f067f744eed3',
            'panel_log_v2': [],
            'status': {
                'status': 'New',
                'priority': 'Informational',
                'created': '2025-06-16T15:18:03.188000Z',
                'updated': '2025-06-16T15:18:06.468000Z',
                'case_rule_id': 'report:oT8Yal',
                'case_rule_label': 'Domain Abuse',
                'owner_organisation_details': {
                    'organisations': [
                        {
                            'organisation_id': 'uhash:oDJ5LVWfXL',
                            'organisation_name': 'Enterprise - Moise',
                        }
                    ],
                    'enterprise_id': 'uhash:5zQaSyRpA1',
                    'enterprise_name': 'Professional Services Development',
                },
                'entity_id': 'idn:cn44.cw101.cloud',
                'entity_name': 'cn44.cw101.cloud',
                'actions_taken': [],
                'targets': ['idn:cw101.com'],
                'entity_criticality': 'Medium',
                'risk_score': 26,
                'context_list': [{'context': 'Default or Common Mail Server'}],
            },
            'panel_evidence_summary': {
                'explanation': 'Alert was created as a result of a triggered typosquat detection'
            },
            'panel_evidence_dns': {
                'ip_list': [
                    {
                        'entity': 'ip:104.247.81.50',
                        'risk_score': 35,
                        'criticality': 'Medium',
                        'record_type': 'A',
                        'context_list': [],
                    }
                ]
            },
            'panel_evidence_whois': {'body': []},
        }
        with pytest.raises(ValidationError):
            playbook_mgr._playbook_alert_factory('domain_abuse', broken_alert)

    ### </Alert Factory>

    ### <Prepare Query>
    def test_prepare_query(selc, playbook_mgr: PlaybookAlertMgr):
        query = playbook_mgr._prepare_query(
            max_results=2,
            statuses=['New'],
            priority=['High', 'Informational'],
            organisation=['moise', 'ernest'],
            direction='asc',
            category=['code_repo_leakage'],
            created_from='2023-01-01',
            created_until='2023-01-02',
            updated_from='2023-01-01',
            updated_until='2023-01-02',
        )

        assert isinstance(query, SearchIn)
        assert query.limit == 2
        assert query.statuses == ['New']
        assert query.priority == ['High', 'Informational']
        assert query.direction == 'asc'
        assert query.organisation == ['uhash:moise', 'uhash:ernest']
        assert query.category == ['code_repo_leakage']
        assert query.created_range.from_.strftime('%Y-%m-%d') == '2023-01-01'
        assert query.created_range.until.strftime('%Y-%m-%d') == '2023-01-02'
        assert query.updated_range.from_.strftime('%Y-%m-%d') == '2023-01-01'
        assert query.updated_range.until.strftime('%Y-%m-%d') == '2023-01-02'

        query = playbook_mgr._prepare_query(
            statuses='New', priority='High', category='domain_abuse', organisation='moise'
        )

        assert isinstance(query, SearchIn)
        assert query.limit == DEFAULT_LIMIT
        assert query.statuses == ['New']
        assert query.priority == ['High']
        assert query.category == ['domain_abuse']
        assert query.organisation == ['uhash:moise']
        assert query.from_ is None
        assert query.created_range is None
        assert query.updated_range is None

    test_data = [
        {'statuses': 1},
        {'category': 123},
        {'priority': {'High': 'Priority'}},
        {'direction': ['asc']},
        {'limit': 'hundred'},
    ]

    @pytest.mark.parametrize('param', test_data)
    def test_prepare_query_raises_ValidationError(self, playbook_mgr: PlaybookAlertMgr, param):
        with pytest.raises(ValidationError):
            playbook_mgr._prepare_query(**param)

    ### </Prepare Query>
    ### <Fetch Images>
    def test_fetch_images_non_image_alert(
        self, playbook_mgr: PlaybookAlertMgr, alerts_factory, mocker: mock
    ):
        code_repo_alerts = alerts_factory(PACategory.CODE_REPO_LEAKAGE.value)
        mock_retrieve_image = mocker.patch.object(playbook_mgr, 'fetch_one_image')

        for alert in code_repo_alerts:
            with pytest.raises(ValidationError):
                playbook_mgr.fetch_images(alert)

        assert mock_retrieve_image.call_count == 0

    ### </Fetch Images>

    ### <Fetch One Image>
    def test_fetch_one_image_raises_PlaybookAlertRetrieveImageError(
        self,
        playbook_mgr: PlaybookAlertMgr,
        alerts_factory,
        mocker: mock,
    ):
        mock_get_request = mocker.patch('psengine.rf_client.RFClient.request')
        mock_get_request.side_effect = HTTPError('woah!')

        domain_abuse_alerts = alerts_factory(PACategory.DOMAIN_ABUSE.value)
        for alert in domain_abuse_alerts:  # noqa: B007
            with pytest.raises(PlaybookAlertRetrieveImageError):
                playbook_mgr.fetch_one_image('alert_id', 'image_id', PACategory.DOMAIN_ABUSE.value)

    def test_fetch_one_image_unsupported_category(self, playbook_mgr: PlaybookAlertMgr):
        with pytest.raises(ValidationError):
            playbook_mgr.fetch_one_image(
                alert_id='task:b164bb6e-9ce1-4747-92f6-f0e4cc2305c3',
                image_id='image_1234',
                alert_category='malware_report',
            )

    def test_fetch_one_image_ok_domain_abuse(
        self, playbook_mgr: PlaybookAlertMgr, mocker, make_binary_response
    ):
        mocks = [make_binary_response(b'asdf', {})]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        img = playbook_mgr.fetch_one_image(
            alert_id='task:4decf327-e6aa-43f0-b3a1-4008e934bf1b',
            image_id='img:2ff2a5b4-d65a-4485-b7d0-f607165bd2bd',
            alert_category=PACategory.DOMAIN_ABUSE.value,
        )
        assert img
        assert isinstance(img, bytes)

    def test_fetch_one_image_ok_geopol(
        self, playbook_mgr: PlaybookAlertMgr, mocker, make_binary_response
    ):
        mocks = [make_binary_response(b'asdf', {})]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        img = playbook_mgr.fetch_one_image(
            image_id='img:7c0a6589-5f54-4fa6-b67a-9b431d639415',
            alert_category=PACategory.GEOPOLITICS_FACILITY.value,
        )
        assert img
        assert isinstance(img, bytes)

    ### </Fetch One Image>

    ### <Save Images>
    def test_save_images(
        self, playbook_mgr: PlaybookAlertMgr, tmp_path, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(MGR_MOCK / 'test_save_images_0.json'),
            make_binary_response(b'asg', {}),
            mock_request(MGR_MOCK / 'test_save_images_2.json'),
            make_binary_response(b'asg', {}),
            mock_request(MGR_MOCK / 'test_save_images_4.json'),
            make_binary_response(b'asg', {}),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        playbook_mgr.output_dir = tmp_path.as_posix()

        alert_ids_with_images = [
            'task:74d4d3f3-5dcd-4813-bfaa-37ed0e7d0e5a',
            'task:43dc5161-6ac8-413f-b951-f1e381b80338',
            'task:9447761b-1213-4877-bd36-10c67375745a',
        ]
        alerts = []
        for alert_id in alert_ids_with_images:
            alert = playbook_mgr.fetch(category='domain_abuse', alert_id=alert_id)
            alerts.append(alert)

        for alert in alerts:
            save_pba_images(alert, tmp_path)

        assert list(tmp_path.glob('*.png'))

    def test_save_images_wrong_pa_raises_TypeError(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [
            mock_request(MGR_MOCK / 'test_save_images_wrong_pa_raises_TypeError_0.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        identity_alert = playbook_mgr.fetch(
            category='identity_novel_exposures',
            alert_id='task:a2bdd7af-1847-4ebf-9601-4522e39432a1',
        )
        with pytest.raises(TypeError):
            save_pba_images(identity_alert)
        with pytest.raises(TypeError):
            save_pba_images([identity_alert])

    def test_save_image_raises_WriteFileError(self):
        with pytest.raises(WriteFileError):
            _save_image('image.png', 'b\x00\x00\x00\x00\x00', output_directory='/non/existing/path')

    ### </Save Images>

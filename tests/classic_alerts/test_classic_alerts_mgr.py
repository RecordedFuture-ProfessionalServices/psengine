import pytest
from pydantic import ValidationError

from psengine.classic_alerts import ALL_CA_FIELDS, REQUIRED_CA_FIELDS, ClassicAlertMgr
from psengine.classic_alerts.classic_alert import AlertRuleOut, ClassicAlert, ClassicAlertHit
from psengine.constants import DEFAULT_LIMIT
from tests.classic_alerts.conftest import MOCK_DIR

ALERT_IDS = ['w1KF1z', 'whz4Ya', 'w7HgBa']

FIELDS = [
    ['id', 'log', 'title', 'rule'],
    [
        'id',
        'log',
        'title',
        'rule',
        'type',
        'url',
    ],
    ALL_CA_FIELDS,
]

IMAGE_IDS = [
    'img:d4620c6a-c789-48aa-b652-b47e0d06d91a',
    'img:b0884512-ed26-495d-a6ef-9b648f238c3a',
    'img:5a2250d5-63c7-44b8-979d-82b09cc53b59',
]


class Test_ClassicAlertsMgr:
    def test_init(self, ca_mgr: ClassicAlertMgr):
        assert isinstance(ca_mgr, ClassicAlertMgr)

    @pytest.mark.parametrize('id_', ALERT_IDS)
    def test_fetch_works(self, ca_mgr: ClassicAlertMgr, id_: str, request, mocker, mock_request):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alert = ca_mgr.fetch(id_=id_)
        assert isinstance(alert, ClassicAlert)
        assert alert.id_ == id_

    @pytest.mark.parametrize('id_', ALERT_IDS)
    def test_fetch_works_with_tagged_text(
        self, ca_mgr: ClassicAlertMgr, id_: str, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alert = ca_mgr.fetch(id_=id_, tagged_text=True)
        assert isinstance(alert, ClassicAlert)
        assert alert.id_ == id_

    def test_fetch_bulk_works(self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alerts = ca_mgr.fetch_bulk(ids=ALERT_IDS)
        assert len(alerts) == 3
        for alert in alerts:
            assert isinstance(alert, ClassicAlert)

    @pytest.mark.parametrize('fields', FIELDS)
    def test_fetch_with_different_fields_works(
        self, ca_mgr: ClassicAlertMgr, fields: list[str], request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)
        spy = mocker.spy(ca_mgr.rf_client, 'request')

        alert = ca_mgr.fetch(id_='w1KF1z', fields=fields)
        assert isinstance(alert, ClassicAlert)
        assert 'w1KF1z' in spy.call_args[1]['url']

        for field in fields:
            assert field in alert.json()

    @pytest.mark.parametrize('fields', FIELDS)
    def test_fetch_bulk_with_different_fields_works(
        self, ca_mgr: ClassicAlertMgr, fields: list[str], request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alerts = ca_mgr.fetch_bulk(ids=ALERT_IDS)
        assert len(alerts) == 3
        for alert in alerts:
            assert isinstance(alert, ClassicAlert)

            for field in fields:
                assert field in alert.json()

    @pytest.mark.parametrize('ids', [ALERT_IDS, 'w1KF1z', 'w7HgBa'])
    def test_fetch_hits_works(
        self, ca_mgr: ClassicAlertMgr, ids: str, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alerts = ca_mgr.fetch_hits(ids=ids)
        for alert in alerts:
            assert isinstance(alert, ClassicAlertHit)

    @pytest.mark.parametrize('ids', [ALERT_IDS, 'w1KF1z', 'w7HgBa'])
    def test_fetch_hits_with_tagged_text(
        self, ca_mgr: ClassicAlertMgr, ids: str, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alerts = ca_mgr.fetch_hits(ids=ids, tagged_text=True)
        for alert in alerts:
            assert isinstance(alert, ClassicAlertHit)

    @pytest.mark.parametrize('id_', IMAGE_IDS, ids=(i[0] for i in IMAGE_IDS))
    def test_fetch_image_works(
        self, ca_mgr: ClassicAlertMgr, id_: str, mocker, make_binary_response
    ):
        mock = make_binary_response(b'abcd', {'Content-Disposition': 'filename=abc.png'})
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        image = ca_mgr.fetch_image(id_=id_)
        assert isinstance(image, bytes)

    @pytest.mark.parametrize(
        ('freetext', 'expected', 'mock_file'),
        [
            (None, 10, 'test_fetch_rules_works[None-10].json'),
            ('Leaked Credential Monitoring', 5, 'test_fetch_rules_works[freetext3-10].json'),
            ('Vulnerability', 10, 'test_fetch_rules_works[Vulnerability-10].json'),
            (['leaked', 'domains'], 10, 'test_fetch_rules_works[freetext3-10]_1.json'),
        ],
    )
    def test_fetch_rules_works(
        self, ca_mgr: ClassicAlertMgr, freetext: str, expected: int, mock_file, mocker, mock_request
    ):
        mock = mock_request(MOCK_DIR / mock_file)
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        rules = ca_mgr.fetch_rules(freetext=freetext)
        assert len(rules) == expected
        for rule in rules:
            assert isinstance(rule, AlertRuleOut)

    def test_fetch_rules_list_with_limit(self, ca_mgr: ClassicAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_fetch_rules_list_with_limit.json'),
            mock_request(MOCK_DIR / 'test_fetch_rules_list_with_limit_1.json'),
        ]
        mocker.patch.object(ca_mgr.rf_client, 'request', side_effect=mocks)

        rules = ca_mgr.fetch_rules(freetext=['leaked', 'domains'], max_results=14)
        assert len(rules) == 14

    @pytest.mark.parametrize(('limit', 'expected'), [(1, 1), (10, 10), (2, 2)])
    def test_fetch_rules_limit_0(
        self, ca_mgr: ClassicAlertMgr, limit, expected, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        rules = ca_mgr.fetch_rules(max_results=limit)
        assert len(rules) == expected

    @pytest.mark.parametrize(
        ('ids', 'status'),
        [
            (ALERT_IDS, 'Dismissed'),
            (ALERT_IDS, 'Pending'),
            (ALERT_IDS, 'Resolved'),
            (ALERT_IDS, 'New'),
        ],
    )
    def test_update_status_works(
        self, ca_mgr: ClassicAlertMgr, ids: str, status: int, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        update_resp = ca_mgr.update_status(ids=ids, status=status)
        assert len(update_resp.get('error')) == 0
        assert len(update_resp.get('success')) == len(ids)

    def test_update_works(self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        updates = [
            {'id': 'w1KF1z', 'note': 'Changes from sample app', 'statusInPortal': 'Pending'},
            {
                'id': 'whz4Ya',
                'note': 'Comment from sample app!',
            },
        ]
        update_resp = ca_mgr.update(updates)
        assert len(update_resp.get('error')) == 0
        assert len(update_resp.get('success')) == len(updates)

    def test_fetch_all_images_finds_images(
        self, ca_mgr: ClassicAlertMgr, mocker, make_binary_response, mock_request
    ):
        mocks = [
            mock_request(MOCK_DIR / 'test_fetch_all_images_finds_images.json'),
            make_binary_response(b'abcd', {'Content-Disposition': 'filename=abc.png'}),
            make_binary_response(b'abcd', {'Content-Disposition': 'filename=aabc.png'}),
        ]
        mocker.patch.object(ca_mgr.rf_client, 'request', side_effect=mocks)

        # Alert with a few images
        alert = ca_mgr.fetch('xOTsae')
        ca_mgr.fetch_all_images(alert)

        assert isinstance(alert.images, dict)
        for id_, bytes_ in alert.images.items():
            assert isinstance(id_, str)
            assert id_.startswith('img:')
            assert isinstance(bytes_, bytes)

    def test_fetch_all_images_finds_no_images(self, ca_mgr: ClassicAlertMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'test_fetch_all_images_finds_no_images.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        # An alert without images
        alert = ca_mgr.fetch('xPtXPZ')
        ca_mgr.fetch_all_images(alert)

        assert isinstance(alert.images, dict)
        assert len(alert.images) == 0

    def test_fetch_bulk_workers(self, ca_mgr: ClassicAlertMgr, mocker):
        ALERT_IDS = ['w1KF1z', 'whz4Ya']

        dict_1 = {
            'data': {
                'review': {
                    'note': 'Comment from sample app!',
                    'status_in_portal': 'Dismissed',
                    'status': 'dismiss',
                },
                'rule': {
                    'name': 'Leaked Credential Monitoring',
                    'id': 'oT8Yaq',
                    'url': {
                        'portal': 'https://app.recordedfuture.com/live/sc/ViewIdkobra_view_report_item_alert_editor?view_opts=%7B%22reportId%22%3A%22oT8Yaq%22%2C%22bTitle%22%3Atrue%2C%22title%22%3A%22Leaked+Credential+Monitoring%22%7D'
                    },
                },
                'id': 'whz4Ya',
                'log': {
                    'note_author': 'e6dc23093a5e43908c18f1c0280fa8ce@integration.recordedfuture.com',
                    'note_date': '2024-10-25T11:00:06.547000Z',
                    'status_date': '2024-10-25T11:00:06.289000Z',
                    'triggered': '2024-06-18T06:06:49.851000Z',
                    'status_change_by': 'e6dc23093a5e43908c18f1c0280fa8ce@integration.recordedfuture.com',
                },
                'title': 'Leaked Credential Monitoring - 5 references',
            }
        }
        dict_2 = {
            'data': {
                'review': {
                    'note': 'Changes from sample app',
                    'status_in_portal': 'Pending',
                    'status': 'pending',
                },
                'rule': {
                    'name': 'Brand name in suspicious websites content (OCR)',
                    'id': 'qCaKN2',
                    'url': {
                        'portal': 'https://app.recordedfuture.com/live/sc/ViewIdkobra_view_report_item_alert_editor?view_opts=%7B%22reportId%22%3A%22qCaKN2%22%2C%22bTitle%22%3Atrue%2C%22title%22%3A%22Brand+name+in+suspicious+websites+content+%28OCR%29%22%7D'
                    },
                },
                'id': 'w1KF1z',
                'log': {
                    'note_author': 'e6dc23093a5e43908c18f1c0280fa8ce@integration.recordedfuture.com',
                    'note_date': '2024-10-25T11:00:06.452000Z',
                    'status_date': '2024-10-25T11:00:06.452000Z',
                    'triggered': '2024-07-05T10:07:17.876000Z',
                    'status_change_by': 'e6dc23093a5e43908c18f1c0280fa8ce@integration.recordedfuture.com',
                },
                'title': 'Brand name in suspicious websites content (OCR) - 1000+ references',
            }
        }

        def mock_request(method, url, *args, **kwargs):  # noqa: ARG001
            mock_response = mocker.MagicMock()

            from urllib.parse import urlparse

            path = urlparse(url).path
            id_ = path.split('/')[-1]

            data = dict_1 if id_ == 'w1KF1z' else dict_2

            mock_response.status_code = 200
            mock_response.json.return_value = data  # noqa: W291
            return mock_response

        mocker.patch.object(ca_mgr.rf_client, 'request', side_effect=mock_request)
        data = ca_mgr.fetch_bulk(ids=ALERT_IDS, fields=['id', 'log'], max_workers=2)
        assert isinstance(data, list)
        assert all(d.id_ in ALERT_IDS for d in data)
        assert len(data) == 2
        for alert in data:
            assert isinstance(alert, ClassicAlert)

    ####### <SEARCH TESTS> ###########

    # <TEST RULE_ID>
    # rule_id can be: None, a single rule as string, a list of strings (1 or more) or an empty list.
    def test_search_rule_id_empty(self, ca_mgr: ClassicAlertMgr, mocker):
        """Test search with rule_id not provided."""
        patched_search = mocker.patch.object(ca_mgr.rf_client, 'request_paged')
        ca_mgr.search()
        assert patched_search.call_args[1]['params'].get('alertRule') is None

    def test_search_rule_id_None(self, ca_mgr: ClassicAlertMgr, mocker):
        """Test search with rule_id not provided."""
        patched_search = mocker.patch.object(ca_mgr.rf_client, 'request_paged')
        ca_mgr.search(rule_id=None)
        assert patched_search.call_args[1]['params'].get('alertRule') is None

    def test_search_rule_id_empty_list(self, ca_mgr: ClassicAlertMgr, mocker):
        """Test search with rule_id as empty list. rule_id should be ignored and."""
        patched_search = mocker.patch.object(ca_mgr.rf_client, 'request_paged')
        ca_mgr.search(rule_id=[])
        assert patched_search.call_args[1]['params'].get('alertRule') is None

    def test_search_rule_id_as_string(self, ca_mgr: ClassicAlertMgr, mocker):
        """Test search with rule_id as str"""
        patched_search = mocker.patch.object(ca_mgr.rf_client, 'request_paged')
        rule = 'oT8Yaq'
        ca_mgr.search(rule_id=rule)

        assert patched_search.call_args[1]['params']['alertRule'] == rule

    def test_search_rule_id_as_list_one_element(self, ca_mgr: ClassicAlertMgr, mocker):
        """Test search with rule_id as list of len 1"""
        patched_search = mocker.patch.object(ca_mgr.rf_client, 'request_paged')
        rule = ['oT8Yaq']
        ca_mgr.search(rule_id=rule)

        assert patched_search.call_args[1]['params']['alertRule'] == rule[0]

    def test_search_rule_id_as_list_multiple_elements(self, ca_mgr: ClassicAlertMgr, mocker):
        """Test search with rule_id as list of len N>1"""
        patched_search = mocker.patch.object(ca_mgr.rf_client, 'request_paged')
        rule = ['oT8Yaq', 'oT8Yaw']
        ca_mgr.search(rule_id=rule)

        assert patched_search.call_args_list[0][1]['params']['alertRule'] == rule[0]
        assert patched_search.call_args_list[1][1]['params']['alertRule'] == rule[1]

    # </TEST RULE_ID>

    # <TEST MAX_RESULTS AND PAGINATION_NUMBER>
    # max_results is the maximum number of results returned. Limit in the API
    # items_per_paged_request is the number of items each pagination query should make. from in the API

    @pytest.mark.parametrize('max_results', [1, 2, 3, 10, 20])
    def test_search_max_results_is_given_as_number(
        self, ca_mgr: ClassicAlertMgr, max_results, mocker, request, mock_request
    ):
        """Test search is called with the correct number of max_results"""
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        patched_search = mocker.spy(ca_mgr.rf_client, 'request_paged')

        search_results = ca_mgr.search(max_results=max_results, triggered='-10d')
        assert len(search_results) == max_results
        assert patched_search.call_args[1]['params']['limit'] == max_results

    def test_search_max_results_is_None_returns_default_limit(
        self, ca_mgr: ClassicAlertMgr, mocker, request, mock_request
    ):
        """Test search is called with the default of 10 max_results since max results was called with None"""

        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        patched_search = mocker.spy(ca_mgr.rf_client, 'request_paged')

        search_results = ca_mgr.search(max_results=None, triggered='-10d')
        assert len(search_results) == DEFAULT_LIMIT
        assert patched_search.call_args[1]['params']['limit'] == DEFAULT_LIMIT

    def test_search_max_results_is_zero_raise_ValidationError(self, ca_mgr: ClassicAlertMgr):
        """Test search is called with the 0 max_results raises ValidationError"""
        with pytest.raises(ValidationError):
            ca_mgr.search(max_results=0, triggered='-10d')

    def test_search_paginate_one_request_with_max_results_lt_alerts_per_page(
        self, ca_mgr: ClassicAlertMgr, mocker, request, mock_request
    ):
        """Test search to call the API once, since max_results < alerts_per_page"""
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)
        max_results = 1
        alerts_per_page = max_results + 1
        patched_search = mocker.spy(ca_mgr.rf_client, 'request_paged')

        search_results = ca_mgr.search(
            max_results=max_results, triggered='-10d', alerts_per_page=alerts_per_page
        )
        assert len(search_results) == max_results
        assert patched_search.call_args[1]['params']['limit'] == max_results
        assert patched_search.call_args[1]['max_results'] == max_results

    def test_search_paginate_one_request_with_max_results_eq_alerts_per_page(
        self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request
    ):
        """Test search to call the API once, since max_results = alerts_per_page"""
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        patched_search = mocker.spy(ca_mgr.rf_client, 'request_paged')
        max_results = 10
        alerts_per_page = max_results

        search_results = ca_mgr.search(
            max_results=max_results, triggered='-10d', alerts_per_page=alerts_per_page
        )
        assert len(search_results) == max_results
        assert patched_search.call_args[1]['params']['limit'] == max_results
        assert patched_search.call_args[1]['max_results'] == max_results

    def test_search_paginate_two_request_with_max_results_eq_alerts_per_page_plus_one(
        self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request
    ):
        """Test search to call the API twice, since max_results = (alerts_per_page + 1)"""
        nodeid = request.node.nodeid
        mocks = [
            mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json'),
            mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}_1.json'),
        ]
        mocker.patch.object(ca_mgr.rf_client, 'call', side_effect=mocks)

        call_spy = mocker.spy(ca_mgr.rf_client, 'call')
        paged_spy = mocker.spy(ca_mgr.rf_client, 'request_paged')

        max_results = 10
        alerts_per_page = max_results - 1

        search_results = ca_mgr.search(
            max_results=max_results, triggered='-10d', alerts_per_page=alerts_per_page
        )
        req_list = call_spy.call_args_list
        assert len(search_results) == max_results
        assert paged_spy.call_args[1]['max_results'] == max_results
        assert req_list[0][1]['params']['limit'] == alerts_per_page
        assert req_list[1][1]['params']['limit'] == max_results - alerts_per_page
        assert req_list[1][1]['params']['from'] == alerts_per_page

    def test_search_paginate_five_request_with_max_results_lt_alerts_per_page_times_five(
        self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request
    ):
        """Test search to call the API five times, since max_results = (alerts_per_page * 5)"""
        nodeid = request.node.nodeid
        mocks = [
            mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}_0.json'),
            mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}_1.json'),
            mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}_2.json'),
            mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}_3.json'),
            mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}_4.json'),
        ]
        mocker.patch.object(ca_mgr.rf_client, 'call', side_effect=mocks)

        call_spy = mocker.spy(ca_mgr.rf_client, 'call')
        paged_spy = mocker.spy(ca_mgr.rf_client, 'request_paged')

        alerts_per_page = 10
        max_results = alerts_per_page * 5

        search_results = ca_mgr.search(
            max_results=max_results, triggered='-10d', alerts_per_page=alerts_per_page
        )

        froms = [call_spy.call_args_list[i][1]['params']['from'] for i in range(1, 5)]
        assert froms == [10, 20, 30, 40]
        assert len(search_results) == max_results
        assert len(set(search_results)) == max_results
        assert paged_spy.call_args[1]['params']['limit'] == alerts_per_page
        assert paged_spy.call_args[1]['max_results'] == max_results

    # </TEST MAX_RESULTS AND PAGINATION_NUMBER>
    def test_search_contains_required_fields(
        self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        search_results = ca_mgr.search(triggered='-1d')
        for result in search_results:
            assert len(REQUIRED_CA_FIELDS) == len(result.json())

            for field in REQUIRED_CA_FIELDS:
                assert field in result.json()

    def test_search_with_tagged_text(self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        search_results = ca_mgr.search(triggered='-1d', tagged_text=True)
        for result in search_results:
            assert len(REQUIRED_CA_FIELDS) == len(result.json())

            for field in REQUIRED_CA_FIELDS:
                assert field in result.json()

    def test_search_contains_requested_fields(
        self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        # This will end up fetching the full alert payload
        search_results = ca_mgr.search(triggered='-80d', fields=ALL_CA_FIELDS, rule_id='mf0rAa')
        assert len(search_results) == 9
        for result in search_results:
            assert len(ALL_CA_FIELDS) == len(result.json())

            for field in ALL_CA_FIELDS:
                assert field in result.json()

    def test_search_contains_requested_fields_with_max_results(
        self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        # This will end up fetching the full alert payload
        search_results = ca_mgr.search(
            triggered='-80d', fields=ALL_CA_FIELDS, rule_id='mf0rAa', max_results=2
        )
        assert len(search_results) == 2
        for result in search_results:
            assert len(ALL_CA_FIELDS) == len(result.json())

            for field in ALL_CA_FIELDS:
                assert field in result.json()

    def test_search_bulk_workers(self, ca_mgr: ClassicAlertMgr, mocker):
        ALERT_RULES = ['oT8Yaq', 'whz4Ya']

        dict_1 = {
            'data': [
                {
                    'log': {
                        'note_author': None,
                        'note_date': None,
                        'status_date': None,
                        'triggered': '2024-11-13T06:07:42.120Z',
                        'status_change_by': None,
                    },
                    'rule': {
                        'use_case_deprecation': None,
                        'name': 'Leaked Credential Monitoring',
                        'id': 'oT8Yaq',
                        'url': {
                            'portal': 'https://app.recordedfuture.com/live/sc/ViewIdkobra_view_report_item_alert_editor?view_opts=%7B%22reportId%22%3A%22oT8Yaq%22%2C%22bTitle%22%3Atrue%2C%22title%22%3A%22Leaked+Credential+Monitoring%22%7D'
                        },
                    },
                    'id': '0fYR1m',
                    'title': 'moise',
                }
            ],
            'counts': {'returned': 1, 'total': 604},
        }
        dict_2 = {
            'data': [
                {
                    'log': {
                        'note_author': None,
                        'note_date': None,
                        'status_date': None,
                        'triggered': '2024-11-13T06:07:42.120Z',
                        'status_change_by': None,
                    },
                    'rule': {
                        'use_case_deprecation': None,
                        'name': 'Leaked Credential Monitoring',
                        'id': 'whz4Ya',
                        'url': {
                            'portal': 'https://app.recordedfuture.com/live/sc/ViewIdkobra_view_report_item_alert_editor?view_opts=%7B%22reportId%22%3A%22oT8Yaq%22%2C%22bTitle%22%3Atrue%2C%22title%22%3A%22Leaked+Credential+Monitoring%22%7D'
                        },
                    },
                    'id': '0fYR1n',
                    'title': 'moise',
                }
            ],
            'counts': {'returned': 1, 'total': 604},
        }

        def mock_request(method, url, *args, **kwargs):  # noqa: ARG001
            mock_response = mocker.MagicMock()

            from urllib.parse import urlparse

            path = urlparse(url).path
            id_ = path.split('/')[-1]

            data = dict_1 if id_ == 'oT8Yaq' else dict_2

            mock_response.status_code = 200
            mock_response.json.return_value = data  # noqa: W291
            return mock_response

        mocker.patch.object(ca_mgr.rf_client, 'request', side_effect=mock_request)
        data = ca_mgr.search(rule_id=ALERT_RULES, max_workers=2)
        assert isinstance(data, list)

    @pytest.mark.parametrize(
        'args',
        [
            {'triggered': '-1d'},
            {'triggered': '-1d', 'max_results': 1},
            {'triggered': '-1d', 'status': 'New'},
            {'triggered': '-80d', 'rule_id': 'mf0rAa'},
        ],
    )
    def test_search_args(self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request, args):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        search_results = ca_mgr.search(**args)
        assert len(search_results) > 0

    ####### </SEARCH TESTS> ###########

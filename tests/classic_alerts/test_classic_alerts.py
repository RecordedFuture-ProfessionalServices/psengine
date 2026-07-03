import pytest

from psengine.classic_alerts import ClassicAlert, ClassicAlertMgr
from psengine.classic_alerts.constants import ALL_CA_FIELDS
from psengine.classic_alerts.errors import AlertMarkdownError
from psengine.classic_alerts.markdown.markdown import _hits_markdown
from tests.classic_alerts.conftest import MOCK_DIR

ALERT_IDS = [
    '0nwGJG',
    '0nzN2_',
    '0nzN5u',
    '0n2q5G',
    '0n_aQr',
    '0n_aZe',
    '0osZdm',
    '0oxjSZ',
    '0o2oaR',
    '0pJJFj',
    '0pJJFn',
    '0pTAwu',
    '0pUX8M',
    '0pUX8N',
    '0pTAxn',
    '0pUX8o',
    '0pUX9U',
    '0pUX9h',
    '0pUX-R',
    '0pUX_M',
    '0pUX_F',
    '0pUX_N',
    '0pUX_S',
    '0pUX-8',
    '0pUX_0',
    '0pUX_3',
    '0pUYAG',
    '0quoSV',
    '0pUYAn',
    '0pUYAm',
    '0pUX_4',
    '0pUYFw',
    '0pUYgC',
    '0pUYhc',
    '0pUYky',
    '0pUYkn',
    '0pUYkz',
    '0pUYk0',
    '0pUZ85',
    '0pUZ86',
    '0pUZ-T',
    '0pUZ82',
    '0pdQzG',
    '0przGY',
    '0pzxG4',
    '0pzxGq',
    '0p09dX',
    '0p09ik',
    '0qcGMX',
]

ALERTS_WITH_ENRICHED_ENTITIES = ['0pUYgC', '0pUZ86', '0qcGMX']

ALERTS_WITH_ENRICHED_ENTITY_FRAGMENTS = [
    '0pTAwu',
    '0pUX_M',
    '0pUX_S',
    '0pUX_0',
    '0pUX_3',
    '0pUYAG',
    '0pUYAm',
    '0pUX_4',
]

PARAMS_TEST_DATA = [
    ('0nwGJG', {'ai_insights': True, 'owner_org': True, 'fragment_entities': True}),
    ('0nzN2_', {'ai_insights': True, 'owner_org': True, 'fragment_entities': False}),
    ('0nzN5u', {'ai_insights': True, 'owner_org': False, 'fragment_entities': True}),
    ('0n2q5G', {'ai_insights': True, 'owner_org': False, 'fragment_entities': False}),
    ('0n_aQr', {'ai_insights': False, 'owner_org': True, 'fragment_entities': True}),
    ('0n_aZe', {'ai_insights': False, 'owner_org': True, 'fragment_entities': False}),
    ('0osZdm', {'ai_insights': False, 'owner_org': False, 'fragment_entities': True}),
    ('0oxjSZ', {'ai_insights': False, 'owner_org': False, 'fragment_entities': False}),
]

IMAGE_BYTES_BY_ID = {
    'img:ZzD761qE1lG7NQ78y1YvZZYh3aIUMnm3WNJGFaQn': b'abcd',
    'img:KR15PL4OH8khYa9cP5jeYV64clkBAXmkep2bxLa7': b'abcde',
}


class Test_ClassicAlert:
    def test_fetch_downloads_images_when_requested(
        self, ca_mgr: ClassicAlertMgr, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(MOCK_DIR / 'test_fetch_all_images_finds_images.json'),
            *[
                make_binary_response(bytes_, {'Content-Disposition': 'filename=abc.png'})
                for bytes_ in IMAGE_BYTES_BY_ID.values()
            ],
        ]
        request_mock = mocker.patch.object(ca_mgr.rf_client, 'request', side_effect=mocks)

        alert = ca_mgr.fetch('xOTsae', fetch_images=True)

        assert alert.images == IMAGE_BYTES_BY_ID
        assert request_mock.call_count == len(mocks)
        assert [call_[1]['params']['id'] for call_ in request_mock.call_args_list[1:]] == list(
            IMAGE_BYTES_BY_ID
        )

    def test_fetch_bulk_downloads_images_when_requested(
        self, ca_mgr: ClassicAlertMgr, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(MOCK_DIR / 'test_fetch_all_images_finds_images.json'),
            *[
                make_binary_response(bytes_, {'Content-Disposition': 'filename=abc.png'})
                for bytes_ in IMAGE_BYTES_BY_ID.values()
            ],
            mock_request(MOCK_DIR / 'test_fetch_all_images_finds_no_images.json'),
        ]
        request_mock = mocker.patch.object(ca_mgr.rf_client, 'request', side_effect=mocks)

        alerts = ca_mgr.fetch_bulk(['xOTsae', 'xPtXPZ'], fetch_images=True)

        assert alerts[0].images == IMAGE_BYTES_BY_ID
        assert alerts[1].images == {}
        assert request_mock.call_count == len(mocks)
        assert [
            call_[1]['params']['id']
            for call_ in request_mock.call_args_list
            if call_[1].get('params', {}).get('id')
        ] == list(IMAGE_BYTES_BY_ID)

    @pytest.mark.parametrize('alert_id', ALERT_IDS)
    def test_markdown(self, ca_mgr: ClassicAlertMgr, alert_id: str, request, mocker, mock_request):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alert = ca_mgr.fetch(alert_id)
        markdown = alert.markdown()
        assert markdown

    @pytest.mark.parametrize('alert_id', ALERTS_WITH_ENRICHED_ENTITIES)
    def test_markdown_with_enriched_entities(
        self, ca_mgr: ClassicAlertMgr, alert_id: str, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alert = ca_mgr.fetch(alert_id)
        markdown = alert.markdown()
        assert 'Risk Score' in markdown
        assert 'Criticality' in markdown
        assert 'Triggered' in markdown
        assert 'Last Triggered' in markdown
        assert 'Rule Criticality' in markdown
        assert 'Rule' in markdown
        assert 'Evidence' in markdown
        assert 'Timestamp' in markdown

    @pytest.mark.parametrize('alert_id', ALERTS_WITH_ENRICHED_ENTITY_FRAGMENTS)
    def test_markdown_with_enriched_entity_fragments(
        self, ca_mgr: ClassicAlertMgr, alert_id: str, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alert = ca_mgr.fetch(alert_id)
        markdown = alert.markdown()
        assert 'Summary' in markdown
        assert 'AI Insights' in markdown
        assert 'Target Entities' in markdown
        assert '1.' in markdown

    @pytest.mark.parametrize(('alert_id', 'kwargs'), PARAMS_TEST_DATA)
    def test_markdown_params(
        self, ca_mgr: ClassicAlertMgr, alert_id: str, kwargs, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alert = ca_mgr.fetch(alert_id)
        markdown = alert.markdown(**kwargs)

        assert markdown

    def test_markdown_on_search_raises_AlertMarkdownError(
        self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)
        alert = ca_mgr.search(max_results=1)[0]

        with pytest.raises(AlertMarkdownError):
            alert.markdown()

    def test_markdown_on_search_succed_with_all_fields(
        self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alert = ca_mgr.search(max_results=1, fields=ALL_CA_FIELDS)[0]

        assert alert.markdown() is not None

    def test_markdown_multiple_alerts(self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alerts = ca_mgr.search(fields=ALL_CA_FIELDS)

        markdowns = [alert.markdown() for alert in alerts]

        assert len(markdowns) == len(alerts)
        for i, alert in enumerate(alerts):
            assert alert.title.split('-')[0] in markdowns[i]

    def test_markdown_multiple_alerts_different_markdown_limits(
        self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alerts = ca_mgr.search(fields=ALL_CA_FIELDS, max_results=3)

        markdowns = [
            alerts[0].markdown(character_limit=5000),
            alerts[1].markdown(),
            alerts[2].markdown(character_limit=2000),
        ]

        assert len(markdowns) == len(alerts)
        assert len(markdowns[0]) == 5000
        assert len(markdowns[1]) == 9907
        assert len(markdowns[2]) == 2000

    def test_markdown_char_limit_with_defang(
        self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alert = ca_mgr.fetch(id_='3gepzd', fields=ALL_CA_FIELDS)
        assert len(alert.markdown(character_limit=10000, defang_iocs=True)) == 10000

    def test_markdown_multiple_alerts_different_markdown_params(
        self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alerts = ca_mgr.search(fields=ALL_CA_FIELDS, max_results=3)

        markdowns = [
            alerts[0].markdown(html_tags=False),
            alerts[0].markdown(html_tags=True),
            alerts[1].markdown(ai_insights=False),
            alerts[2].markdown(),
            alerts[2].markdown(reviewer_note=True),
        ]

        assert '\n</details>' not in markdowns[0]
        assert 'AI Insights' in markdowns[1]
        assert 'AI Insights' not in markdowns[2]
        assert 'AI Insights' in markdowns[3]
        assert 'Reviewer Note' not in markdowns[3]
        assert 'Reviewer Note' in markdowns[4]

    def test_markdown_defang_iocs(self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        alert = ca_mgr.fetch(id_='3gepzd', fields=ALL_CA_FIELDS)
        markdown = alert.markdown(defang_iocs=True)

        assert '62[.]6[.]190[.]28' in markdown
        assert '32[.]62[.]1[.]230' in markdown
        assert 'realty[.]trade' in markdown

    def test_markdown_defang_escaped_url_in_table(
        self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        d = ca_mgr.fetch(id_='3gepzf', fields=ALL_CA_FIELDS)
        data = d.markdown(defang_iocs=True)

        assert 'https://consciousness[.]tirol/agdkd/adf' in data

    def test_markdown_table_not_broken(
        self, ca_mgr: ClassicAlertMgr, request, mocker, mock_request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        d = ca_mgr.fetch('3gepzf')
        markdown = d.markdown()
        assert (
            'CyberVulnerability | An authentication bypass in the Palo Alto Networks PAN-OS software enables an unauthenticated attacker with network access to the management web interface to bypass the authentication otherwise required by the PAN-OS management web interface and invoke certain PHP scripts. While invoking these PHP scripts does not enable remote code execution, it can negatively impact integrity and confidentiality of PAN-OS.  You can greatly reduce the risk of this issue by restricting access to the management web interface to only trusted internal IP addresses according to our recommended  best practices deployment guidelines https://live.paloaltonetworks.com/t5/community-blogs/tips-amp-tricks-how-to-secure-the-management-access-of-your-palo/ba-p/464431 .  This issue does not affect Cloud NGFW or Prisma Access software.'
            in markdown
        )

    def test_hits_markdown_missing_fragment(self):
        raw_alert = {
            'review': {
                'note': None,
                'status_in_portal': 'New',
                'assignee': None,
                'status': 'no-action',
            },
            'owner_organisation_details': {
                'owner_id': 'uhash:123456678',
                'enterprise_id': 'uhash:12345668',
                'owner_name': 'ernest',
                'organisations': [
                    {'organisation_id': 'uhash:12345678', 'organisation_name': 'cool beans'}
                ],
                'enterprise_name': 'cool beans',
            },
            'url': {'api': 'https:...', 'portal': 'https:...'},
            'rule': {
                'use_case_deprecation': None,
                'name': 'name',
                'id': 'id',
                'url': {'portal': 'https:...'},
            },
            'id': '5tgAM1',
            'hits': [
                {
                    'entities': [],
                    'document': {
                        'source': {
                            'id': 'source:uGGyI5',
                            'name': 'iOSGods Forum',
                            'type': 'Source',
                        },
                        'title': 'DomiNations v12.1470.1470 +40++ Cheats [ Exclusive ]',
                        'url': 'https://iosgods.com/topic/50401-dominations-v1214701470-40-cheats-exclusive/',
                        'authors': [{'id': '5q3mLz', 'name': 'uae988', 'type': 'Username'}],
                    },
                    'fragment': None,
                    'id': 'HFBfAAA4uQs',
                    'language': 'eng',
                    'primary_entity': None,
                    'analyst_note': None,
                },
            ],
            'enriched_entities': [],
            'ai_insights': {'comment': None, 'text': 'n/a'},
            'log': {
                'note_author': None,
                'note_date': None,
                'status_date': None,
                'triggered': '2025-05-02T17:56:42.187Z',
                'status_change_by': None,
            },
            'triggered_by': [],
            'title': 'test alert title',
            'type': 'REFERENCE',
        }
        alert_model = ClassicAlert(**raw_alert)
        hits_md = _hits_markdown(alert_model, alert_model.hits, True, True, False)
        assert hits_md is not None
        assert isinstance(hits_md, list)
        assert hits_md == [
            {
                'content': [
                    '**Author(s):** uae988\n',
                    '**Title:** DomiNations v12.1470.1470 +40++ Cheats [ Exclusive ]\n',
                    '**URL:** https://iosgods.com/topic/50401-dominations-v1214701470-40-cheats-exclusive/\n',
                    '_Reference text is missing, check the Recorded Future [Portal](https://.../) for more information._\n',
                ],
                'title': '1. From iOSGods Forum',
            }
        ]

    def test_search_without_all_fields(self):
        alert = {
            'id': '9_J5JD',
            'log': {
                'note_author': None,
                'note_date': None,
                'status_date': None,
                'triggered': '2025-09-08T14:20:14.909000Z',
                'status_change_by': None,
            },
            'title': 'Vulnerability Risk, New Critical - High: CVE-2025-9751',
            'url': {
                'api': 'https://api.recordedfuture.com/v3/alerts/9_J5JD',
                'portal': 'https://app.recordedfuture.com/live/sc/notification/?id=9_J5JD',
            },
            'rule': {
                'use_case_deprecation': None,
                'name': 'Vulnerability Risk, New Critical or Pre NVD Watch List Vulnerabilities',
                'id': 'nZW3KP',
                'url': {'portal': 'https://app.recordedfuture.com/asld'},
            },
            'enriched_entities': [
                {
                    'evidence': [
                        {
                            'timestamp': '2025-08-31T10:20:38.316000Z',
                            'mitigation_string': '',
                            'criticality_label': 'Medium',
                            'rule': 'Recent Unverified Proof of Concept Available',
                            'evidence_string': '3 sightings on 1 ',
                            'criticality': 2,
                        },
                        {
                            'timestamp': '2025-09-08T14:11:07.626000Z',
                            'mitigation_string': '',
                            'criticality_label': 'High',
                            'rule': 'NIST Severity: High',
                            'evidence_string': '1 sighting on 1 s',
                            'criticality': 3,
                        },
                    ],
                    'references': [
                        {
                            'entities': [
                                {
                                    'id': 'url:https://img.shields.io/static/v1?label',
                                    'name': 'https://img.shields.io/static/v1?label=Ve',
                                    'type': 'URL',
                                },
                            ],
                            'document': {
                                'source': {
                                    'id': 'source:MIKjae',
                                    'name': 'GitHub',
                                    'type': 'Source',
                                },
                                'title': 'Code change in file 2025/CVE-2025-9751.md on repo cve:',
                                'url': 'https://github.com/test/cve/commit/4b741f8',
                                'authors': [
                                    {
                                        'id': 'rROI-j',
                                        'name': 'trickest-workflows',
                                        'type': 'Username',
                                    }
                                ],
                            },
                            'fragment': '<i id=HFB_gACE2_L>Code change in file 2025/<e id',
                            'id': 'HFB_gACE2_L',
                            'language': 'eng',
                            'primary_entity': {
                                'id': '9njxv1',
                                'name': 'CVE-2025-9751',
                                'type': 'CyberVulnerability',
                                'description': 'A weakness has been identified in Campcod',
                            },
                        }
                    ],
                    'criticality': {
                        'name': 'High',
                        'score': 66,
                        'last_triggered': '2025-09-08T00:00:00Z',
                        'triggered': '2025-09-08T14:18:04.520000Z',
                        'level': 3,
                    },
                    'entity': {
                        'id': '9njxv1',
                        'name': 'CVE-2025-9751',
                        'type': 'CyberVulnerability',
                    },
                },
                {
                    'evidence': [
                        {
                            'timestamp': '2025-08-31T10:20:37.315000Z',
                            'mitigation_string': '',
                            'criticality_label': 'Medium',
                            'rule': 'Recent Unverified Proof of Concept Available',
                            'evidence_string': '3 sightings on 1 source: Recorded Future ',
                            'criticality': 2,
                        },
                        {
                            'timestamp': '2025-09-08T14:11:07.570000Z',
                            'mitigation_string': '',
                            'criticality_label': 'High',
                            'rule': 'NIST Severity: High',
                            'evidence_string': '1 sighting on 1 source: Recorded ',
                            'criticality': 3,
                        },
                    ],
                    'references': [],
                    'criticality': {
                        'name': 'High',
                        'score': 66,
                        'last_triggered': '2025-09-08T00:00:00Z',
                        'triggered': '2025-09-08T14:18:04.520000Z',
                        'level': 3,
                    },
                    'entity': {
                        'id': '9nk6Qd',
                        'name': 'CVE-2025-9750',
                        'type': 'CyberVulnerability',
                    },
                },
            ],
        }

        alert = ClassicAlert(**alert)
        markdown = alert.markdown(ai_insights=False, triggered_by=False, defang_iocs=True)

        assert all(
            x in markdown
            for x in (
                'CVE-2025-9750',
                'Vulnerability Risk, New Critical - High: CVE-2025-9751',
                'Rule',
                'Triggered',
            )
        )

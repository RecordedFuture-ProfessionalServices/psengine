import json
from itertools import chain
from pathlib import Path

import pytest

from psengine.classic_alerts import ClassicAlertMgr
from psengine.classic_alerts.classic_alert import AlertRuleOut, ClassicAlert, ClassicAlertHit
from tests.classic_alerts.conftest import MOCK_DIR

ALERT_IDS = [
    ['vJaAG9'],
    ['vJaAG1', 'vJaAGg'],
    ['vJaAPo', 'vJaAu6', 'vJb20b'],
    ['vJb21V', 'vJb27P', 'vJceB1', 'vJceDX'],
    ['vJceER', 'vJcemT', 'vJcemh', 'vJcemR', 'vJcemi'],
    ['vJtQmi', 'vJtQm4', 'vKZV75', 'vKkbi-', 'vKkbjG', 'vKsG4W'],
]

DATA = [
    ('vJaAG9', ['log', 'type'], True),
    ('vJaAG1', ['ai_insights', 'id', 'rule', 'title'], False),
    (
        'vJaAGg',
        [
            'ai_insights',
            'hits',
            'log',
            'owner_organisation_details',
            'review',
            'type',
            'url',
        ],
        True,
    ),
    ('vJaAPo', None, True),
    ('vJaAu6', None, False),
    ('vJb20b', ['rule', 'title'], None),
    ('vJaAPo', ['id', 'url'], False),
    ('vJaAu6', ['id', 'log', 'owner_organisation_details', 'rule'], True),
    ('vJb20b', ['rule', 'title'], False),
    ('vJb21V', ['id', 'log', 'owner_organisation_details', 'rule', 'type'], True),
    ('vJb27P', ['ai_insights', 'log', 'rule', 'title', 'type', 'url'], False),
    (
        'vJceB1',
        ['id', 'log', 'owner_organisation_details', 'review', 'title', 'type'],
        True,
    ),
    (
        'vJceDX',
        ['hits', 'id', 'log', 'owner_organisation_details', 'rule', 'type', 'url'],
        False,
    ),
    ('vJceER', ['ai_insights', 'hits', 'id', 'type', 'url'], True),
    (
        'vJcemT',
        ['ai_insights', 'hits', 'id', 'owner_organisation_details', 'title', 'type'],
        False,
    ),
    ('vJcemh', ['ai_insights', 'hits', 'title', 'type', 'url'], True),
    ('vJcemR', ['hits', 'id', 'log', 'rule', 'title', 'url'], False),
    ('vJcemi', ['id', 'owner_organisation_details', 'review', 'rule', 'type'], True),
    ('vJtQmi', ['hits', 'log', 'title', 'type'], False),
    ('vJtQm4', ['owner_organisation_details', 'review', 'title'], True),
    ('vKZV75', None, False),
    ('vKkbi-', None, True),
    ('vKkbjG', ['ai_insights', 'title', 'url'], None),
    ('vKsG4W', None, None),
    ('0pUZ86', ['enriched_entities'], None),
    ('0pUZ86', None, None),
]


class Test_ClassicAlertModels:
    @pytest.mark.parametrize(('alert_id', 'fields', 'tagged_text'), DATA)
    def test_validate_ClassicAlert(
        self, ca_mgr: ClassicAlertMgr, alert_id, fields, tagged_text, mocker, mock_request, request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')

        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        res = ca_mgr.fetch(alert_id, fields, tagged_text)
        assert isinstance(res, ClassicAlert)

    @pytest.mark.parametrize(('ids'), ALERT_IDS)
    def test_validate_ClassicAlertHit(
        self, ca_mgr: ClassicAlertMgr, ids, mocker, mock_request, request
    ):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        res = ca_mgr.fetch_hits(ids)
        assert all(isinstance(hit, ClassicAlertHit) for hit in res)

    def test_validate_AlertRuleOut(self, ca_mgr: ClassicAlertMgr, mocker, mock_request, request):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        res = ca_mgr.fetch_rules()
        assert all(isinstance(rule, AlertRuleOut) for rule in res)

    def test_ordering_fetch(self, ca_mgr: ClassicAlertMgr, mock_request, mocker):
        mocks = [
            mock_request(MOCK_DIR / 'test_ordering_fetch_0.json'),
            mock_request(MOCK_DIR / 'test_ordering_fetch_1.json'),
            mock_request(MOCK_DIR / 'test_ordering_fetch_2.json'),
            mock_request(MOCK_DIR / 'test_ordering_fetch_3.json'),
            mock_request(MOCK_DIR / 'test_ordering_fetch_4.json'),
            mock_request(MOCK_DIR / 'test_ordering_fetch_5.json'),
        ]
        mocker.patch.object(ca_mgr.rf_client, 'request', side_effect=mocks)

        models = [ca_mgr.fetch(id_) for id_ in ALERT_IDS[-1]]
        assert [model.id_ for model in sorted(models)] == [
            'hZ1kfQ',
            'niWlvO',
            'AeBxGp',
            'kuo44h',
            'qGyNko',
            '8Q2YiW',
        ]

    def test_ordering_search(self, ca_mgr: ClassicAlertMgr, mock_request, mocker, request):
        nodeid = request.node.nodeid
        mock = mock_request(MOCK_DIR / f'{nodeid.split(":")[-1]}.json')
        mocker.patch.object(ca_mgr.rf_client, 'request', return_value=mock)

        models = ca_mgr.search()
        assert [model.id_ for model in sorted(models)] == [
            'wOBwA6',
            'vXkabM',
            'QDiqE0',
            'PBFTK0',
            'Ug0oX0',
            'XjaI9T',
            'r74aDn',
            'pamrrO',
            'bi3htI',
            'auJ6eX',
        ]

    def test_hash_fetch(self, ca_mgr: ClassicAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_hash_fetch_0.json'),
            mock_request(MOCK_DIR / 'test_hash_fetch_1.json'),
            mock_request(MOCK_DIR / 'test_hash_fetch_0.json'),
            mock_request(MOCK_DIR / 'test_hash_fetch_1.json'),
        ]
        mocker.patch.object(ca_mgr.rf_client, 'request', side_effect=mocks)

        alert1 = ca_mgr.fetch(id_='vJaAG9')
        alert2 = ca_mgr.fetch(id_='vJaAG1')

        alert1_twin = ca_mgr.fetch(id_='vJaAG9')
        alert2_twin = ca_mgr.fetch(id_='vJaAG1')

        alerts = [alert1, alert2, alert1_twin, alert2_twin]

        assert alert1 == alert1_twin
        assert alert2 == alert2_twin

        assert alert1 != alert2

        assert hash(alert1) == hash(alert1_twin)
        assert set(alerts) == {alert1, alert2}

    def test_hash_search(self, ca_mgr: ClassicAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_hash_search.json'),
            mock_request(MOCK_DIR / 'test_hash_search.json'),
        ]
        mocker.patch.object(ca_mgr.rf_client, 'request', side_effect=mocks)

        model1 = ca_mgr.search()
        model2 = ca_mgr.search()

        assert min(model1) == min(model2)
        assert set(chain(model1, model2)) == set(model1)

    # <TEST TRIGGER_BY REMAPPING>
    def test_triggered_by_triggered_by_strings_brand_cyber_focus(self):
        sample_file = (
            Path(__file__).parent / 'triggered_by_files' / 'brand_cyber_focused_09pmAU.json'
        )
        data = json.loads(sample_file.read_text())
        expected_object = [
            {
                'reference_id': 'HFA4AAD1OEX',
                'triggered_by_strings': [
                    'https://www.recordedfuture.com/research/operation-undercut-shows-multifaceted-nature-sdas-influence-operations (URL) -> www.recordedfuture.com (InternetDomainName) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                    'https://www.recordedfuture.com/research/operation-undercut-shows-multifaceted-nature-sdas-influence-operations (URL) -> www.recordedfuture.com (InternetDomainName) -> recordedfuture.com (InternetDomainName) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                ],
            },
            {
                'reference_id': 'HFA3wAEh0Vg',
                'triggered_by_strings': [
                    'Recorded Future (Company) -> Brand Names Watch List (EntityList)'
                ],
            },
            {
                'reference_id': 'HFA4AAA46yh',
                'triggered_by_strings': [
                    'Recorded Future News (Company) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)'
                ],
            },
            {
                'reference_id': 'HFA4AAA5AQW',
                'triggered_by_strings': [
                    'Recorded Future News (Company) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)'
                ],
            },
            {
                'reference_id': 'HFA4AAD1QPa',
                'triggered_by_strings': [
                    'https://www.recordedfuture.com/research/scam-websites-take-advantage-of-seasonal-openings (URL) -> www.recordedfuture.com (InternetDomainName) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                    'https://www.recordedfuture.com/research/scam-websites-take-advantage-of-seasonal-openings (URL) -> www.recordedfuture.com (InternetDomainName) -> recordedfuture.com (InternetDomainName) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                ],
            },
            {
                'reference_id': 'HFA4AAEJk4T',
                'triggered_by_strings': [
                    'A.P. Moller-Maersk (Company) -> Brand Names Watch List (EntityList)'
                ],
            },
            {
                'reference_id': 'HFA4AACmjyH',
                'triggered_by_strings': [
                    'Recorded Future News (Company) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)'
                ],
            },
            {
                'reference_id': 'HFA4AABZAgA',
                'triggered_by_strings': [
                    'Recorded Future News (Company) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)'
                ],
            },
            {
                'reference_id': 'HFA4AAD11KI',
                'triggered_by_strings': [
                    'Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                    'Insikt Group (Organization) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                ],
            },
            {
                'reference_id': 'HFA4AAArMe7',
                'triggered_by_strings': [
                    'https://therecord.media/lockbit-ransomware-hopital-de-cannes-data-published (URL) -> therecord.media (InternetDomainName) -> Recorded Future News (Company) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                ],
            },
            {
                'reference_id': 'HFA4AABZAgC',
                'triggered_by_strings': [
                    'Recorded Future News (Company) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                ],
            },
            {
                'reference_id': 'HFA4AACmZHz',
                'triggered_by_strings': [
                    'Recorded Future News (Company) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                ],
            },
            {
                'reference_id': 'HFA4AAE1wZp',
                'triggered_by_strings': [
                    'A.P. Moller-Maersk (Company) -> Brand Names Watch List (EntityList)'
                ],
            },
            {
                'reference_id': 'HFA4AAD_i1T',
                'triggered_by_strings': [
                    'Recorded Future News (Company) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                ],
            },
            {
                'reference_id': 'HFA4AAAfRRa',
                'triggered_by_strings': [
                    'Recorded Future News (Company) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                ],
            },
            {
                'reference_id': 'HFA4AAD1p62',
                'triggered_by_strings': [
                    'Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                ],
            },
            {
                'reference_id': 'HFA4AAAda1Z',
                'triggered_by_strings': [
                    'https://therecord.media/lockbit-ransomware-hopital-de-cannes-data-published (URL) -> therecord.media (InternetDomainName) -> Recorded Future News (Company) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                ],
            },
            {
                'reference_id': 'HFA4AAAeSCF',
                'triggered_by_strings': [
                    'Recorded Future News (Company) -> Recorded Future (Company) -> Brand Names Watch List (EntityList)',
                ],
            },
        ]

        triggered_by = ClassicAlert.parse_trigger_by(data)
        for i, elem in enumerate(triggered_by):
            assert elem == expected_object[i]

    def test_triggered_by_triggered_by_strings_vidar_infrastructure(self):
        sample_file = Path(__file__).parent / 'triggered_by_files' / 'vidar_infra_0-XW9x.json'
        data = json.loads(sample_file.read_text())
        expected_object = [
            {
                'reference_id': 'HFA4QAA3V-E',
                'triggered_by_strings': [
                    'Vidar (Malware)',
                    'https://steamcommunity.com/profiles/76561199802540894 (URL) -> Any URL',
                ],
            },
            {
                'reference_id': 'HFA4QAAJ8qZ',
                'triggered_by_strings': [
                    'Vidar (Malware)',
                    'https://t.me/asg7rd (URL) -> Any URL',
                ],
            },
            {
                'reference_id': 'HFA4QAApY0k',
                'triggered_by_strings': [
                    'Vidar (Malware)',
                    'https://t.me/fu4chmo (URL) -> Any URL',
                ],
            },
            {
                'reference_id': 'HFA4QAATNMc',
                'triggered_by_strings': [
                    'Vidar (Malware)',
                    'https://t.me/fu4chmo (URL) -> Any URL',
                ],
            },
            {
                'reference_id': 'HFA4AADwJq4',
                'triggered_by_strings': [
                    'Vidar (Malware)',
                    'https://steamcommunity.com/profiles/76561199794498376 (URL) -> Any URL',
                ],
            },
            {
                'reference_id': 'HFA4QAAXIbt',
                'triggered_by_strings': [
                    'Vidar (Malware)',
                    'https://steamcommunity.com/profiles/76561199681720597 (URL) -> Any URL',
                ],
            },
            {
                'reference_id': 'HFA4QAA2s66',
                'triggered_by_strings': [
                    'Vidar (Malware)',
                    'https://lenak513.tumblr.com/ (URL) -> Any URL',
                ],
            },
            {
                'reference_id': 'HFA4QABAQRy',
                'triggered_by_strings': [
                    'Vidar (Malware)',
                    'https://mastodon.social/@mniami (URL) -> Any URL',
                ],
            },
        ]

        triggered_by = ClassicAlert.parse_trigger_by(data)
        for i, elem in enumerate(triggered_by):
            assert elem == expected_object[i]

    # </TEST TRIGGER_BY REMAPPING>

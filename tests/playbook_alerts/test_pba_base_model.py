import copy
import json

import pytest
from pydantic_core import ValidationError

from psengine.playbook_alerts import PACategory, PBA_Generic
from psengine.playbook_alerts.mappings import CATEGORY_TO_OBJECT_MAP
from psengine.playbook_alerts.playbook_alert_mgr import PlaybookAlertMgr
from tests.playbook_alerts.conftest import (
    BANK_CHECK_MOCK,
    BASE_MOCK_DIR,
    CODE_REPO_MOCK,
    MALW_MOCK,
)

MINIMAL_STATUS = {
    'status': 'New',
    'priority': 'Informational',
    'created': '2025-12-01T19:48:15.554Z',
    'updated': '2025-10-15T01:19:21.238Z',
    'alert_rule': {'id': 'x', 'label': 'test', 'name': 'Test Alert Rule'},
    'entity_name': 'example.test',
    'risk_score': 5,
    'context_list': [],
    'targets': [],
    'actions_taken': [],
}

COMMENT_LOG = [
    {
        'id': 'uuid:1',
        'author_name': 'Ada Lovelace',
        'created': '2026-01-02T10:00:00.000Z',
        'changes': [{'comment': 'First comment for testing', 'type': 'comment_change'}],
    },
    {
        'id': 'uuid:2',
        'author_name': 'Alan Turing',
        'created': '2026-01-01T09:00:00.000Z',
        'changes': [{'comment': 'Second comment for testing', 'type': 'comment_change'}],
    },
    {
        'id': 'uuid:3',
        'author_name': 'Grace Hopper',
        'created': '2026-01-01T08:00:00.000Z',
        'changes': [
            {
                'old': 'alpha-state',
                'new': 'beta-state',
                'actions_taken': [],
                'type': 'status_change',
            }
        ],
    },
]

DUPLICATE_TEXT_LOG = [
    {
        'id': 'uuid:dup-1',
        'author_id': 'uhash:5o9xIgLFI9',
        'author_name': 'malicious_sites_hudson',
        'created': '2026-07-22T00:04:55.743Z',
        'changes': [{'comment': 'comment2', 'type': 'comment_change'}],
    },
    {
        'id': 'uuid:dup-2',
        'author_id': 'uhash:5o9xIgLFI9',
        'author_name': 'malicious_sites_hudson',
        'created': '2026-07-22T00:04:22.269Z',
        'changes': [{'comment': 'comment2', 'type': 'comment_change'}],
    },
]

EDITED_COMMENT_LOG = [
    {
        'id': 'uuid:a1e0e180',
        'author_id': 'uhash:7JYarWENMi',
        'author_name': 'Hudson Woomer',
        'created': '2026-07-22T00:17:48.581Z',
        'changes': [{'comment': 'second ui comment', 'type': 'comment_change'}],
    },
    {
        'id': 'uuid:ec7c3fb7',
        'author_id': 'uhash:5o9xIgLFI9',
        'author_name': 'malicious_sites_hudson',
        'created': '2026-07-22T00:15:12.563Z',
        'changes': [
            {
                'new': {'id': 'uhash:5o9xIgLFI9', 'name': 'malicious_sites_hudson'},
                'type': 'assignee_change',
            },
            {'comment': 'combined entry comment', 'type': 'comment_change'},
        ],
    },
]


def _make_alert(category, panel_log_v2):
    return CATEGORY_TO_OBJECT_MAP[category](
        playbook_alert_id='task:comments-test',
        panel_status=copy.deepcopy(MINIMAL_STATUS),
        panel_log_v2=copy.deepcopy(panel_log_v2),
    )


def _make_alert_from_mock(category, mock_path, panel_log_v2):
    raw = json.loads(mock_path.read_text())
    data = copy.deepcopy(raw.get('data', raw))
    data['panel_log_v2'] = copy.deepcopy(panel_log_v2) + list(data.get('panel_log_v2') or [])
    return CATEGORY_TO_OBJECT_MAP[category](**data)


class Test_BasePlaybookAlert:
    def test_base_playbook_alert(self, alerts_factory):
        domain_abuse_alerts = alerts_factory(PACategory.DOMAIN_ABUSE.value)
        # Any PA alert is based on the base class
        for alert in domain_abuse_alerts:
            assert isinstance(alert, PBA_Generic)

    def test_create_empty_pa(self):
        alert_data = {}
        with pytest.raises(ValidationError):
            PBA_Generic(**alert_data)

    def test_json(self, alerts_factory):
        domain_abuse_alerts = alerts_factory(PACategory.DOMAIN_ABUSE.value)
        for alert in domain_abuse_alerts:
            assert alert.json() is not None
            assert isinstance(alert.json(), dict)

    def test_str_repr(self, alerts_factory):
        domain_abuse_alerts = alerts_factory(PACategory.DOMAIN_ABUSE.value)
        for alert in domain_abuse_alerts:
            assert str(alert) is not None
            assert isinstance(str(alert), str)
            assert repr(alert) is not None
            assert isinstance(repr(alert), str)

    data = [
        ('playbook_alert_id', str),
        ('panel_log_v2', list),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_base_attributes(self, alerts_factory, attribute, type_to_check):
        cyber_vulnerability_alerts = alerts_factory(PACategory.CYBER_VULNERABILITY.value)
        for alert in cyber_vulnerability_alerts:
            attr = getattr(alert, attribute)
            assert attr is not None
            assert isinstance(attr, type_to_check)

    def test_get_changes(self, alerts_factory):
        domain_abuse_alerts = alerts_factory(PACategory.DOMAIN_ABUSE.value)
        for alert in domain_abuse_alerts:
            assert isinstance(alert._get_changes('priority_change'), list)

    def test_ordering(self, alerts_factory):
        domain_abuse_alerts = alerts_factory(PACategory.DOMAIN_ABUSE.value)
        assert domain_abuse_alerts[0] > domain_abuse_alerts[1]

    def test_generic_pba_markdown(self, mocker, mock_request):
        pba_mgr = PlaybookAlertMgr()
        mocks = [
            mock_request(BASE_MOCK_DIR / 'test_generic_pba_markdown_0.json'),
            mock_request(BASE_MOCK_DIR / 'test_generic_pba_markdown_1.json'),
        ]
        mocker.patch.object(pba_mgr.rf_client, 'request', side_effect=mocks)
        generic = pba_mgr.fetch('task:af4426fe-7818-4fab-9644-6273182e73eb')
        generic = PBA_Generic.model_validate(generic.json())
        generic.category = 'moise'
        with pytest.raises(NotImplementedError):
            generic.markdown()


class Test_PlaybookAlertComments:
    def test_markdown_comments_renders_section(self):
        md = _make_alert(PACategory.DOMAIN_ABUSE.value, COMMENT_LOG).markdown(comments=True)
        assert '### Comments' in md
        assert 'First comment for testing' in md
        assert 'Second comment for testing' in md
        assert 'Ada Lovelace' in md

    def test_markdown_comments_filters_non_comment_changes(self):
        md = _make_alert(PACategory.DOMAIN_ABUSE.value, COMMENT_LOG).markdown(comments=True)
        comments_block = md.split('### Comments', 1)[1].split('\n### ', 1)[0]
        assert 'beta-state' not in comments_block

    def test_markdown_comments_off_by_default(self):
        md = _make_alert(PACategory.DOMAIN_ABUSE.value, COMMENT_LOG).markdown()
        assert '### Comments' not in md
        assert 'First comment for testing' not in md

    def test_markdown_comments_empty_log(self):
        md = _make_alert(PACategory.DOMAIN_ABUSE.value, []).markdown(comments=True)
        assert '### Comments' not in md

    @pytest.mark.parametrize(
        'category',
        [
            PACategory.DOMAIN_ABUSE.value,
            PACategory.CYBER_VULNERABILITY.value,
            PACategory.THIRD_PARTY_RISK.value,
            PACategory.IDENTITY_NOVEL_EXPOSURES.value,
            PACategory.GEOPOLITICS_FACILITY.value,
            PACategory.MALICIOUS_SITES.value,
        ],
    )
    def test_markdown_comments_across_categories(self, category):
        log = [
            {
                'id': 'uuid:x',
                'author_name': 'Cross Cat Author',
                'created': '2026-01-01T00:00:00.000Z',
                'changes': [{'comment': 'CROSS_CAT_SENTINEL', 'type': 'comment_change'}],
            }
        ]
        md = _make_alert(category, log).markdown(comments=True)
        assert '### Comments' in md
        assert 'CROSS_CAT_SENTINEL' in md
        assert 'Cross Cat Author' in md

    def test_markdown_comments_preserves_separate_identical_posts(self):
        md = _make_alert(PACategory.DOMAIN_ABUSE.value, DUPLICATE_TEXT_LOG).markdown(comments=True)
        assert md.count('comment2') == 2

    def test_markdown_comments_no_duplicate_after_edit(self):
        md = _make_alert(PACategory.DOMAIN_ABUSE.value, EDITED_COMMENT_LOG).markdown(comments=True)
        assert md.count('second ui comment') == 1
        assert md.count('combined entry comment') == 1

    @pytest.mark.parametrize(
        ('category', 'mock_path'),
        [
            (PACategory.CODE_REPO_LEAKAGE.value, CODE_REPO_MOCK / 'test_markdown_fetch_0.json'),
            (
                PACategory.MALWARE_REPORT.value,
                MALW_MOCK / 'test_markdown_html_tags_True_or_False_0.json',
            ),
            (
                PACategory.COMPROMISED_BANK_CHECKS.value,
                BANK_CHECK_MOCK / 'test_markdown_single_alert.json',
            ),
        ],
    )
    def test_markdown_comments_across_categories_from_mocks(self, category, mock_path):
        log = [
            {
                'id': 'uuid:x',
                'author_name': 'Cross Cat Author',
                'created': '2026-01-01T00:00:00.000Z',
                'changes': [{'comment': 'CROSS_CAT_SENTINEL', 'type': 'comment_change'}],
            }
        ]
        md = _make_alert_from_mock(category, mock_path, log).markdown(comments=True)
        assert '### Comments' in md
        assert 'CROSS_CAT_SENTINEL' in md
        assert 'Cross Cat Author' in md

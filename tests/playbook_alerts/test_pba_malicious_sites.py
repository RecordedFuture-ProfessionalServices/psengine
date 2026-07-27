import json
from pathlib import Path

import pytest

from psengine.playbook_alerts import PACategory
from psengine.playbook_alerts.models.panel_log import (
    TYPE_MAPPING,
    AttackerAddedChange,
    ForSaleChange,
    LogoHashChange,
    MaliciousSitesDnsChange,
    MaliciousSitesLogoChange,
    MaliciousSitesMaliciousDnsChange,
    MaliciousSitesMaliciousUrlChange,
    MaliciousSitesReregistrationChange,
    MaliciousSitesScreenshotMentionChange,
    MaliciousSitesWhoisChange,
    ParkedChange,
    PhishingVerdictChange,
    SuggestedTakedownChange,
)
from psengine.playbook_alerts.models.pba_malicious_sites import (
    Asset,
    Attacker,
    MaliciousSitesPanelEvidenceDns,
    MaliciousSitesPanelEvidenceSummary,
    MaliciousSitesPanelEvidenceWhois,
    MaliciousSitesPanelStatus,
)
from psengine.playbook_alerts.playbook_alert_mgr import PlaybookAlertMgr
from tests.playbook_alerts.conftest import MALICIOUS_SITES_MOCK

CATEGORY = PACategory.MALICIOUS_SITES.value


class Test_MaliciousSites:
    data = [
        ('panel_action', list),
        ('panel_status', MaliciousSitesPanelStatus),
        ('panel_evidence_summary', MaliciousSitesPanelEvidenceSummary),
        ('panel_evidence_dns', MaliciousSitesPanelEvidenceDns),
        ('panel_evidence_whois', MaliciousSitesPanelEvidenceWhois),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_panels(self, alerts_factory, attribute, type_to_check):
        for alert in alerts_factory(CATEGORY):
            attr = getattr(alert, attribute)
            assert attr is not None
            assert isinstance(attr, type_to_check)

    def test_category(self, alerts_factory):
        for alert in alerts_factory(CATEGORY):
            assert alert.category == CATEGORY

    data = [
        ('ip_list', 'panel_evidence_dns'),
        ('mx_list', 'panel_evidence_dns'),
        ('ns_list', 'panel_evidence_dns'),
        ('body', 'panel_evidence_whois'),
    ]

    @pytest.mark.parametrize(('key', 'panel'), data)
    def test_keys_in_panel_evidence(self, alerts_factory, key, panel):
        for alert in alerts_factory(CATEGORY):
            pnl = getattr(alert, panel)
            assert key in dir(pnl)
            assert isinstance(getattr(pnl, key), list)

    data = [
        ('image_ids', list),
        ('images', dict),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_non_log_getters(self, alerts_factory, attribute, type_to_check):
        for alert in alerts_factory(CATEGORY):
            assert isinstance(getattr(alert, attribute), type_to_check)

    def test_image_ids_are_strings(self, alerts_factory):
        for alert in alerts_factory(CATEGORY):
            assert all(isinstance(x, str) for x in alert.image_ids)

    def test_status_panel_fields(self, alerts_factory):
        for alert in alerts_factory(CATEGORY):
            ps = alert.panel_status
            assert isinstance(ps.risk_score, int)
            assert ps.entity_criticality is not None
            assert all(a.name for a in ps.assessments)
            assert all(isinstance(a, str) for a in ps.attackers)

    def test_attacker_and_assets(self, alerts_factory):
        for alert in alerts_factory(CATEGORY):
            assert alert.panel_evidence_summary.attackers
            for attacker in alert.panel_evidence_summary.attackers:
                assert isinstance(attacker, Attacker)
                assert all(isinstance(a, Asset) for a in attacker.assets)

            # Each polymorphic asset type resolves to its own field.
            assets = {a.type_: a for a in alert.panel_evidence_summary.attackers[0].assets}
            assert assets['client_domain'].domain_id
            assert assets['similar_domain_term'].term is not None
            assert assets['logotype'].logotype_id

    log_getters = [
        ('log_dns_changes', MaliciousSitesDnsChange),
        ('log_whois_changes', MaliciousSitesWhoisChange),
        ('log_malicious_dns_changes', MaliciousSitesMaliciousDnsChange),
        ('log_reregistration_changes', MaliciousSitesReregistrationChange),
        ('log_malicious_url_changes', MaliciousSitesMaliciousUrlChange),
        ('log_logo_changes', MaliciousSitesLogoChange),
        ('log_screenshot_mention_changes', MaliciousSitesScreenshotMentionChange),
        ('log_attacker_added_changes', AttackerAddedChange),
        ('log_phishing_verdict_changes', PhishingVerdictChange),
        ('log_suggested_takedown_changes', SuggestedTakedownChange),
        ('log_for_sale_changes', ForSaleChange),
        ('log_parked_changes', ParkedChange),
        ('log_logo_hash_changes', LogoHashChange),
    ]

    @pytest.mark.parametrize(('attribute', 'change_type'), log_getters)
    def test_log_getters(self, alerts_factory, attribute, change_type):
        for alert in alerts_factory(CATEGORY):
            changes = getattr(alert, attribute)
            assert isinstance(changes, list)
            assert all(isinstance(c, change_type) for c in changes)

    def test_log_getters_populated_from_fixture(self, alerts_factory):
        for alert in alerts_factory(CATEGORY):
            for attribute, _ in self.log_getters:
                assert getattr(alert, attribute), f'{attribute} unexpectedly empty'

    def test_panel_log_no_changes_dropped(self, alerts_factory, tests_dir):
        raw = json.loads(
            (Path(tests_dir) / 'static' / 'playbook_alerts' / 'malicious_sites.json').read_text()
        )
        for entry, alert in zip(raw, alerts_factory(CATEGORY), strict=True):
            input_changes = [
                change.get('type')
                for log in entry['data'].get('panel_log_v2', [])
                for change in log.get('changes', [])
            ]
            mapped = [t for t in input_changes if t in TYPE_MAPPING]
            parsed = sum(len(log.changes) for log in alert.panel_log_v2)
            # Every supported change validated; nothing silently dropped or errored.
            assert parsed == len(mapped)
            # The fixture only carries change types the model knows how to parse.
            assert all(t in TYPE_MAPPING for t in input_changes)

    def test_markdown_sections(self, alerts_factory):
        for alert in alerts_factory(CATEGORY):
            md = alert.markdown(comments=True)
            assert isinstance(md, str)
            for section in ('Targets', 'Attackers', 'DNS Records', 'WHOIS Details'):
                assert section in md


class Test_MaliciousSitesMarkdown:
    def test_markdown(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(MALICIOUS_SITES_MOCK / 'test_markdown_0.json'),
            mock_request(MALICIOUS_SITES_MOCK / 'test_markdown_1.json'),
            make_binary_response(
                (MALICIOUS_SITES_MOCK / 'test_markdown_2.file').read_bytes(),
                {'Content-Disposition': 'filename=abc.png'},
            ),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch_bulk(category='malicious_sites', fetch_images=True)
        data = [d.markdown() for d in data]

        assert all(isinstance(d, str) for d in data)
        assert any('Screenshots' in d for d in data)

    def test_markdown_fetch_images_false(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [
            mock_request(MALICIOUS_SITES_MOCK / 'test_markdown_0.json'),
            mock_request(MALICIOUS_SITES_MOCK / 'test_markdown_1.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch_bulk(category='malicious_sites', fetch_images=False)
        data = [d.markdown() for d in data]

        assert all(isinstance(d, str) for d in data)
        assert all('Screenshots' not in d for d in data)

    def test_markdown_single_alert_no_images(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [mock_request(MALICIOUS_SITES_MOCK / 'test_markdown_single_alert.json')]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        alert = playbook_mgr.fetch('string', PACategory.MALICIOUS_SITES.value, fetch_images=False)
        markdown = alert.markdown()

        assert isinstance(markdown, str)
        assert 'Screenshots' not in markdown

    def test_markdown_character_limit(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(MALICIOUS_SITES_MOCK / 'test_markdown_single_alert.json'),
            make_binary_response(
                (MALICIOUS_SITES_MOCK / 'test_markdown_2.file').read_bytes(),
                {'Content-Disposition': 'filename=abc.png'},
            ),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        alert = playbook_mgr.fetch('string', PACategory.MALICIOUS_SITES.value)
        markdown = alert.markdown(character_limit=5000)

        assert 'Screenshots' not in markdown
        assert len(markdown) <= 5000

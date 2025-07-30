import re
from pathlib import Path

import pytest

from psengine.analyst_notes import AnalystNoteMgr
from psengine.enrich import LookupMgr
from psengine.playbook_alerts import PACategory, PBA_CyberVulnerability, PlaybookAlertMgr
from psengine.playbook_alerts.models.pba_cyber_vulnerability import (
    CyberVulnerabilityPanelEvidence,
    CyberVulnerabilityPanelStatus,
)
from tests.playbook_alerts.conftest import VULN_MOCK


class Test_CyberVulnerability:
    def test_cyber_vulnerability(self, alerts_factory):
        cyber_vulnerability_alerts = alerts_factory(PACategory.CYBER_VULNERABILITY.value)
        for alert in cyber_vulnerability_alerts:
            assert isinstance(alert, PBA_CyberVulnerability)

    data = [
        ('panel_status', CyberVulnerabilityPanelStatus),
        ('panel_evidence_summary', CyberVulnerabilityPanelEvidence),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_panels(self, alerts_factory, attribute, type_to_check):
        cyber_vulnerability_alerts = alerts_factory(PACategory.CYBER_VULNERABILITY.value)
        for alert in cyber_vulnerability_alerts:
            attr = getattr(alert, attribute)
            assert attr is not None
            assert isinstance(attr, type_to_check)

    def test_category(self, alerts_factory):
        cyber_vulnerability_alerts = alerts_factory(PACategory.CYBER_VULNERABILITY.value)
        for alert in cyber_vulnerability_alerts:
            assert alert.category == PACategory.CYBER_VULNERABILITY.value

    @pytest.mark.parametrize('panel', ['status', 'summary', 'log'])
    def test_for_each_panel(
        self, playbook_mgr: PlaybookAlertMgr, panel, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_for_each_panel\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(VULN_MOCK).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        mocker_fetch = mocker.spy(playbook_mgr, 'fetch')
        mocker_post = mocker.spy(playbook_mgr.rf_client, 'request')
        p_alert = playbook_mgr.fetch(
            category=PACategory.CYBER_VULNERABILITY.value,
            alert_id='task:dcdb0cd6-0817-4e97-a350-5a64e7c99817',
            panels=[panel],
        )
        assert isinstance(p_alert, PBA_CyberVulnerability)
        assert mocker_fetch.call_args[1]['panels'] == [panel]
        assert sorted(mocker_post.call_args[1]['data']['panels']) == sorted({'status', panel})

    data = [
        ('lifecycle_stage', str),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_non_log_getters(self, alerts_factory, attribute, type_to_check):
        cyber_vulnerability_alerts = alerts_factory(PACategory.CYBER_VULNERABILITY.value)
        for alert in cyber_vulnerability_alerts:
            assert isinstance(getattr(alert, attribute), type_to_check)

    def test_log_getters(self, alerts_factory):
        cyber_vulnerability_alerts = alerts_factory(PACategory.CYBER_VULNERABILITY.value)
        for alert in cyber_vulnerability_alerts:
            assert isinstance(alert.log_vulnerability_lifecycle_changes, list)
            assert all(isinstance(log, dict) for log in alert.log_vulnerability_lifecycle_changes)

    def test_markdown(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(VULN_MOCK / 'test_markdown_0.json'),
            mock_request(VULN_MOCK / 'test_markdown_1.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        pbas = playbook_mgr.fetch_bulk(
            category=PACategory.CYBER_VULNERABILITY.value, created_from='-30d'
        )
        pbdas_md = [d.markdown() for d in pbas]

        assert all(isinstance(d, str) for d in pbdas_md)
        assert any('Affected Products' in d for d in pbdas_md)

    def test_markdown_extra_content_empty(
        self, playbook_mgr: PlaybookAlertMgr, tests_dir, mocker, mock_request
    ):
        mocks = [
            mock_request(VULN_MOCK / 'test_markdown_extra_content_empty_0.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        pba = playbook_mgr.fetch(
            alert_id='task:95e30a1a-5f1e-47b6-860b-7aa96c06eb30',
            category=PACategory.CYBER_VULNERABILITY.value,
        )
        markdown = pba.markdown()

        expected_md = (
            Path(tests_dir) / 'playbook_alerts' / 'markdown' / 'cyber_vuln_extra_content_empty.md'
        )
        assert markdown == expected_md.read_text()

    @pytest.mark.parametrize('html', [True, False])
    def test_markdown_extra_context_html_tags(
        self, playbook_mgr: PlaybookAlertMgr, tests_dir, html, mocker, mock_request
    ):
        mocks = [mock_request(VULN_MOCK / f'test_markdown_extra_context_html_tags[{html}]_0.json')]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        pba = playbook_mgr.fetch(
            alert_id='task:b0a23d05-f981-47f6-a82f-5596c8f44dfb',
            category=PACategory.CYBER_VULNERABILITY.value,
        )

        mocks = [mock_request(VULN_MOCK / f'test_markdown_extra_context_html_tags[{html}]_1.json')]
        lookup_mgr = LookupMgr()
        mocker.patch.object(lookup_mgr.rf_client, 'request', side_effect=mocks)

        enriched_cve = lookup_mgr.lookup(
            pba.panel_status.entity_name,
            'vulnerability',
            fields=['aiInsights', 'entity', 'risk', 'cvss', 'cvssv3'],
        )
        extra_context = [enriched_cve]
        mocks = [mock_request(VULN_MOCK / f'test_markdown_extra_context_html_tags[{html}]_2.json')]
        analyst_note_mgr = AnalystNoteMgr()
        mocker.patch.object(analyst_note_mgr.rf_client, 'request', side_effect=mocks)

        insikt_notes = [analyst_note_mgr.lookup(id_) for id_ in pba.insikt_note_ids]
        extra_context.extend(insikt_notes)

        markdown = pba.markdown(html_tags=html, extra_context=extra_context)

        expected_md = (
            Path(tests_dir)
            / 'playbook_alerts'
            / 'markdown'
            / f'cyber_vuln_extra_context_html_tags_{html}.md'
        )
        assert markdown == expected_md.read_text()

    @pytest.mark.parametrize('char_limit', [500, 1000, 600_000])
    def test_markdown_handle_char_limit(
        self, playbook_mgr: PlaybookAlertMgr, char_limit, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(
            rf'^test_markdown_handle_char_limit\[{re.escape(node_id)}\]_\d+\.json$'
        )
        files = sorted(f for f in Path(VULN_MOCK).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        pba = playbook_mgr.fetch(
            alert_id='task:dcdb0cd6-0817-4e97-a350-5a64e7c99817',
            category=PACategory.CYBER_VULNERABILITY.value,
        )

        pba_md = pba.markdown(character_limit=char_limit)
        assert len(pba_md) <= char_limit

    def test_markdown_without_all_panels(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [
            mock_request(VULN_MOCK / 'test_markdown_without_all_panels_0.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        pba_md = playbook_mgr.fetch(
            alert_id='task:dcdb0cd6-0817-4e97-a350-5a64e7c99817',
            category=PACategory.CYBER_VULNERABILITY.value,
            panels=['status'],
        ).markdown()

        assert 'Vulnerability Overview' in pba_md
        assert 'CVE-2024-38475' in pba_md
        assert 'Assessments' not in pba_md

    def test_markdown_without_ai(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(VULN_MOCK / 'test_markdown_without_ai_0.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        d = playbook_mgr.fetch('task:9273bf0e-a56c-487e-9eea-05bb2de028f6', 'cyber_vulnerability')
        mocks = [
            mock_request(VULN_MOCK / 'test_markdown_without_ai_1.json'),
        ]
        lookup = LookupMgr()
        mocker.patch.object(lookup.rf_client, 'request', side_effect=mocks)
        vuln = lookup.lookup(d.panel_status.entity_name, 'vulnerability', fields=['cvssv3'])

        assert d.markdown(extra_context=[vuln])

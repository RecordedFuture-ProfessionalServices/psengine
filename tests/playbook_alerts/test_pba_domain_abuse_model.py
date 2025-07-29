import re
from pathlib import Path

import pytest

from psengine.playbook_alerts import PACategory
from psengine.playbook_alerts.models.pba_domain_abuse import (
    DomainAbusePanelEvidenceDns,
    DomainAbusePanelEvidenceSummary,
    DomainAbusePanelEvidenceWhois,
    DomainAbusePanelStatus,
)
from psengine.playbook_alerts.playbook_alert_mgr import PlaybookAlertMgr
from tests.playbook_alerts.conftest import DA_MOCK

CONTEXT_LIST = [
    'Active Mail Server',
    'C&C Server',
    'Phishing Host',
    'Parked / Ad hosting website',
    'Domain for sale',
    'Logotype detected',
    'Domain reregistration',
    'Login Form',
]


class Test_DomainAbuse:
    data = [
        ('panel_action', list),
        ('panel_status', DomainAbusePanelStatus),
        ('panel_evidence_summary', DomainAbusePanelEvidenceSummary),
        ('panel_evidence_dns', DomainAbusePanelEvidenceDns),
        ('panel_evidence_whois', DomainAbusePanelEvidenceWhois),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_panels(self, alerts_factory, attribute, type_to_check):
        domain_abuse_alerts = alerts_factory(PACategory.DOMAIN_ABUSE.value)
        for alert in domain_abuse_alerts:
            attr = getattr(alert, attribute)
            assert attr is not None
            assert isinstance(attr, type_to_check)

    def test_category(self, alerts_factory):
        domain_abuse_alerts = alerts_factory(PACategory.DOMAIN_ABUSE.value)
        for alert in domain_abuse_alerts:
            assert alert.category == PACategory.DOMAIN_ABUSE.value

    data = [
        ('ip_list', 'panel_evidence_dns'),
        ('mx_list', 'panel_evidence_dns'),
        ('ns_list', 'panel_evidence_dns'),
        ('body', 'panel_evidence_whois'),
    ]

    @pytest.mark.parametrize(('key', 'panel'), data)
    def test_keys_in_panel_evidence(self, alerts_factory, key, panel):
        domain_abuse_alerts = alerts_factory(PACategory.DOMAIN_ABUSE.value)
        for alert in domain_abuse_alerts:
            pnl = getattr(alert, panel)
            assert key in dir(pnl)
            assert isinstance(getattr(pnl, key), list)

    data = [
        ('image_ids', list),
        ('images', dict),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_non_log_getters(self, alerts_factory, attribute, type_to_check):
        domain_abuse_alerts = alerts_factory(PACategory.DOMAIN_ABUSE.value)
        for alert in domain_abuse_alerts:
            attr = getattr(alert, attribute)
            assert isinstance(attr, type_to_check)

    data = [
        ('image_ids', str),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_isinstance_subtype(self, alerts_factory, attribute, type_to_check):
        domain_abuse_alerts = alerts_factory(PACategory.DOMAIN_ABUSE.value)
        for alert in domain_abuse_alerts:
            attr = getattr(alert, attribute)
            assert all(isinstance(x, type_to_check) for x in attr)

    attributes = [
        'log_dns_changes',
        'log_whois_changes',
        'log_logotype_changes',
        'log_malicious_dns_changes',
        'log_reregistration_changes',
        'log_malicious_url_changes',
        'log_screenshot_mentions_changes',
    ]

    @pytest.mark.parametrize('attribute', attributes)
    def test_log_getters(self, alerts_factory, attribute):
        domain_abuse_alerts = alerts_factory(PACategory.DOMAIN_ABUSE.value)
        for alert in domain_abuse_alerts:
            attr = getattr(alert, attribute)
            assert isinstance(attr, list)
            assert all(isinstance(log, dict) for log in attr)

    def test_markdown(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(DA_MOCK / 'test_markdown_0.json'),
            mock_request(DA_MOCK / 'test_markdown_1.json'),
            *[
                make_binary_response(
                    (DA_MOCK / f'test_markdown_{i}.file').read_bytes(),
                    {'Content-Disposition': 'filename=abc.png'},
                )
                for i in range(2, 11)
            ],
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch_bulk(category='domain_abuse', fetch_images=True)
        data = [d.markdown() for d in data]

        assert all(isinstance(d, str) for d in data)
        assert any('Screenshot Count' in d for d in data)

    def test_markdown_handle_fetch_images_False(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [
            mock_request(DA_MOCK / 'test_markdown_handle_fetch_images_False_0.json'),
            mock_request(DA_MOCK / 'test_markdown_handle_fetch_images_False_1.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch_bulk(category='domain_abuse', fetch_images=False)
        data = [d.markdown() for d in data]

        assert all(isinstance(d, str) for d in data)
        assert all('Screenshot Count' not in d for d in data)

    def test_markdown_fetch(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(DA_MOCK / 'test_markdown_fetch_0.json'),
            make_binary_response(
                (DA_MOCK / 'test_markdown_fetch_1.file').read_bytes(),
                {'Content-Disposition': 'filename=abc.png'},
            ),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch(
            alert_id='task:d2a5f67d-bd83-43b3-bc23-af0757275317', category='domain_abuse'
        )
        data = data.markdown()
        assert data == (Path(__file__).parent / 'markdown' / 'domain_abuse.md').read_text()

    @pytest.mark.parametrize('char_limit', [500, 1000, 600_000])
    def test_markdown_handle_char_limit(
        self,
        playbook_mgr: PlaybookAlertMgr,
        char_limit,
        mocker,
        mock_request,
        request,
        make_binary_response,
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(
            rf'^test_markdown_handle_char_limit\[{re.escape(node_id)}\]_\d+\.json$'
        )
        files = sorted(f for f in Path(DA_MOCK).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocks.append(
            make_binary_response(
                DA_MOCK / 'test_markdown_handle_char_limit[600000]_1.file',
                {'Content-Disposition': 'filename=abc.png'},
            )
        )
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch(
            alert_id='task:d2a5f67d-bd83-43b3-bc23-af0757275317', category='domain_abuse'
        )

        data = data.markdown(character_limit=char_limit)
        assert len(data) <= char_limit
        assert 'data:image/png;base64,' not in data

    def test_markdown_alert_without_records(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [mock_request(DA_MOCK / 'test_markdown_alert_without_records_0.json')]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch(
            alert_id='task:f7278a20-9ddd-4f13-932e-e38697c11b94', category='domain_abuse'
        )
        assert 'DNS Records' not in data.markdown()

    def test_markdown_alerts_without_all_panels(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [mock_request(DA_MOCK / 'test_markdown_alerts_without_all_panels_0.json')]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch(
            alert_id='task:f7278a20-9ddd-4f13-932e-e38697c11b94',
            category='domain_abuse',
            panels=['status'],
        ).markdown()

        assert 'Domain Abuse' in data
        assert 'Targets' in data
        assert 'clubpenguin.com.br' in data

    def test_markdown_defanged_iocs(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(DA_MOCK / 'test_markdown_defanged_iocs_0.json'),
            make_binary_response(
                (DA_MOCK / 'test_markdown_defanged_iocs_1.file').read_bytes(),
                {'Content-Disposition': 'filename=abc.png'},
            ),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch(
            alert_id='task:7b1cfe72-dfdd-4e88-a4f7-d27c79d097df', category='domain_abuse'
        )
        data = data.markdown(defang_iocs=True)
        assert data == (Path(__file__).parent / 'markdown' / 'domain_abuse_defang.md').read_text()

    def test_markdown_defang_whois(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(DA_MOCK / 'test_markdown_defang_whois_0.json'),
            make_binary_response(
                (DA_MOCK / 'test_markdown_defang_whois_1.file').read_bytes(),
                {'Content-Disposition': 'filename=abc.png'},
            ),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch(
            alert_id='task:360e1f76-1a43-4393-ae7b-91c61420b6cc', category='domain_abuse'
        )
        data = data.markdown(defang_iocs=True)
        assert 'ns1[.]dnsowl[.]com, ns2[.]dnsowl[.]com, ns3[.]dnsowl[.]com' in data
        assert '**Entity:** jroffer[.]com' in data

import re
from pathlib import Path

import pytest

from psengine.analyst_notes.note_mgr import AnalystNoteMgr
from psengine.enrich.lookup_mgr import LookupMgr
from psengine.enrich.soar_mgr import SoarMgr
from psengine.playbook_alerts import PACategory
from psengine.playbook_alerts.models.pba_third_party_risk import TPRPanelEvidence, TPRPanelStatus
from psengine.playbook_alerts.playbook_alerts import PBA_ThirdPartyRisk
from tests.playbook_alerts.conftest import TPR_MOCK


class Test_ThirdPartyRisk:
    data = [
        ('panel_status', TPRPanelStatus),
        ('panel_evidence_summary', TPRPanelEvidence),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_panels(self, alerts_factory, attribute, type_to_check):
        third_party_alerts = alerts_factory(PACategory.THIRD_PARTY_RISK.value)
        for alert in third_party_alerts:
            attr = getattr(alert, attribute)
            assert attr is not None
            assert isinstance(attr, type_to_check)

    def test_category(self, alerts_factory):
        third_party_alerts = alerts_factory(PACategory.THIRD_PARTY_RISK.value)
        for alert in third_party_alerts:
            assert alert.category == PACategory.THIRD_PARTY_RISK.value

    @pytest.mark.parametrize('panel', ['status', 'summary', 'log'])
    def test_for_each_panel(self, playbook_mgr, panel, mocker, mock_request, request):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_for_each_panel\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(TPR_MOCK).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        mocker_fetch = mocker.spy(playbook_mgr, 'fetch')
        mocker_post = mocker.spy(playbook_mgr.rf_client, 'request')
        p_alert = playbook_mgr.fetch(
            category=PACategory.THIRD_PARTY_RISK.value,
            alert_id='task:2836006c-5e63-4039-8ede-d1682c5efc50',
            panels=[panel],
            fetch_images=False,
        )
        assert isinstance(p_alert, PBA_ThirdPartyRisk)
        assert mocker_fetch.call_args[1]['panels'] == [panel]
        assert sorted(mocker_post.call_args[1]['data']['panels']) == sorted({'status', panel})

    def test_log_getters_v2(self, alerts_factory):
        third_party_alerts = alerts_factory(PACategory.THIRD_PARTY_RISK.value)
        for alert in third_party_alerts:
            assert isinstance(alert.log_third_party_assessment_changes, list)
            assert all(isinstance(log, dict) for log in alert.log_third_party_assessment_changes)

    ids = [
        'task:2836006c-5e63-4039-8ede-d1682c5efc50',
        'task:48889a06-e466-4495-a33d-8bcf0c2678b7',
        'task:59c3f3ed-617f-4fb7-872a-74d672b99682',
        'task:9b3c2dda-34f2-4d98-b22c-e46966820626',
        'task:19491482-70d3-410f-a26e-bd52d261816d',
        'task:426fb575-c8e3-4226-a7a4-0a67c3a5c546',
        'task:a1ccb1c8-5554-42af-b794-6177e6e2192a',
        'task:a801c6ca-6071-4dcf-9586-b807ccc225d2',
        'task:3f3f9a45-0343-4865-a80a-b81acf75d6ff',
        'task:c89f8024-0462-4a50-88a9-f7e86056d485',
    ]

    @pytest.mark.parametrize('html', [True, False])
    @pytest.mark.parametrize('id_', ids, ids=range(len(ids)))
    def test_markdown(
        self,
        playbook_mgr,
        id_,
        html,
        mocker,
        mock_request,
        request,
    ):
        node_id = request.node.callspec.id

        pattern = re.compile(rf'^test_markdown\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(TPR_MOCK).iterdir() if pattern.match(f.name))
        mocks = [mock_request(f) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        file = Path(__file__).parent / 'markdown' / f'tpr_{id_.split("-")[-1]}_html_{html}.md'
        alert = playbook_mgr.fetch(id_, 'third_party_risk')
        data = alert.markdown(html_tags=html)

        assert data == file.read_text()

    panels = [
        ['status'],
        ['summary'],
        ['log'],
        ['status', 'summary'],
        ['status', 'log'],
        ['summary', 'log'],
        ['status', 'summary', 'log'],
    ]

    @pytest.mark.parametrize('panels', panels)
    def test_markdown_for_each_panel(
        self,
        playbook_mgr,
        panels,
        mocker,
        mock_request,
        request,
    ):
        node_id = request.node.callspec.id

        pattern = re.compile(rf'^test_markdown_for_each_panel\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(TPR_MOCK).iterdir() if pattern.match(f.name))
        mocks = [mock_request(f) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        file = Path(__file__).parent / 'markdown' / f'tpr_{"_".join(panels)}.md'
        alert = playbook_mgr.fetch('task:80a78452-d38b-40ea-9a6f-b651698119d0', 'third_party_risk')
        data = alert.markdown()

        assert data == file.read_text()

    ids = ['task:c4fa965e-888c-40ed-842e-8566e3f1efb5', 'task:ddbda677-5832-4022-8372-0381fab92c79']

    @pytest.mark.parametrize('id_', ids, ids=range(len(ids)))
    def test_markdown_without_note(
        self,
        playbook_mgr,
        id_,
        mocker,
        mock_request,
        request,
    ):
        node_id = request.node.callspec.id

        pattern = re.compile(rf'^test_markdown_without_note\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(TPR_MOCK).iterdir() if pattern.match(f.name))
        mocks = [mock_request(f) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        file = Path(__file__).parent / 'markdown' / f'tpr_without_note_{id_.split("-")[-1]}.md'
        alert = playbook_mgr.fetch(id_, 'third_party_risk')
        data = alert.markdown()

        assert file.read_text() == data

    @pytest.mark.parametrize('id_', ids, ids=range(len(ids)))
    def test_markdown_with_note(self, playbook_mgr, id_, mocker, mock_request, request):
        node_id = request.node.callspec.id
        alert = mock_request(TPR_MOCK / f'test_markdown_with_note[{node_id}]_0.json')
        note = mock_request(TPR_MOCK / f'test_markdown_with_note[{node_id}]_1.json')

        note_mgr = AnalystNoteMgr()
        mocker.patch.object(playbook_mgr.rf_client, 'request', return_value=alert)
        mocker.patch.object(note_mgr.rf_client, 'request', return_value=note)

        file = Path(__file__).parent / 'markdown' / f'tpr_with_note_{id_.split("-")[-1]}.md'
        alert = playbook_mgr.fetch(id_, 'third_party_risk')
        notes = [note_mgr.lookup(id_) for id_ in alert.all_insikt_notes]
        data = alert.markdown(extra_context=notes)

        assert file.read_text() == data

    def test_markdown_with_soar(self, playbook_mgr, mocker, mock_request):
        alert = mock_request(TPR_MOCK / 'test_markdown_with_soar_0.json')
        enrich = mock_request(TPR_MOCK / 'test_markdown_with_soar_1.json')

        soar = SoarMgr()
        mocker.patch.object(playbook_mgr.rf_client, 'request', return_value=alert)
        mocker.patch.object(soar.rf_client, 'request', return_value=enrich)

        id_ = 'task:25896b57-cf1b-4d82-b085-6b3d191c6ed5'
        file = Path(__file__).parent / 'markdown' / 'tpr_with_soar.md'
        alert = playbook_mgr.fetch(id_, 'third_party_risk')
        ips = soar.soar(ip=alert.all_ip_addresses)

        data = alert.markdown(extra_context=ips)

        assert file.read_text() == data

    def test_markdown_with_lookup(self, playbook_mgr, mocker, mock_request):
        alert = mock_request(TPR_MOCK / 'test_markdown_with_lookup_0.json')
        enrichs = [
            mock_request(TPR_MOCK / f'test_markdown_with_lookup_{i}.json') for i in range(1, 7)
        ]

        lookup = LookupMgr()
        mocker.patch.object(playbook_mgr.rf_client, 'request', return_value=alert)
        mocker.patch.object(lookup.rf_client, 'request', side_effect=enrichs)

        id_ = 'task:25896b57-cf1b-4d82-b085-6b3d191c6ed5'
        file = Path(__file__).parent / 'markdown' / 'tpr_with_lookup.md'
        alert = playbook_mgr.fetch(id_, 'third_party_risk')
        ips = lookup.lookup_bulk(alert.all_ip_addresses, 'ip')

        data = alert.markdown(extra_context=ips)

        assert file.read_text() == data

    @pytest.mark.parametrize('html', [True, False])
    def test_markdown_observed_traffic(self, playbook_mgr, html, request, mocker, mock_request):
        node_id = request.node.callspec.id
        alert = mock_request(TPR_MOCK / f'test_markdown_observed_traffic[{node_id}]_0.json')
        mocker.patch.object(playbook_mgr.rf_client, 'request', return_value=alert)

        id_ = 'task:80a78452-d38b-40ea-9a6f-b651698119d0'
        file = Path(__file__).parent / 'markdown' / f'tpr_observed_traffic_html_{html}.md'
        alert = playbook_mgr.fetch(id_, 'third_party_risk')

        data = alert.markdown(html_tags=html)

        assert file.read_text() == data

    @pytest.mark.parametrize('html', [True, False])
    def test_markdown_observed_traffic_enriched(
        self, playbook_mgr, html, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        alert = mock_request(
            TPR_MOCK / f'test_markdown_observed_traffic_enriched[{node_id}]_0.json'
        )
        enrichs = [
            mock_request(TPR_MOCK / f'test_markdown_observed_traffic_enriched[{node_id}]_{i}.json')
            for i in range(1, 7)
        ]

        lookup = LookupMgr()
        mocker.patch.object(playbook_mgr.rf_client, 'request', return_value=alert)
        mocker.patch.object(lookup.rf_client, 'request', side_effect=enrichs)

        id_ = 'task:80a78452-d38b-40ea-9a6f-b651698119d0'
        file = Path(__file__).parent / 'markdown' / f'tpr_observed_traffic_enriched_html_{html}.md'
        alert = playbook_mgr.fetch(id_, 'third_party_risk')
        ips = lookup.lookup_bulk(alert.all_ip_addresses, 'ip')

        data = alert.markdown(html_tags=html, extra_context=ips)

        assert file.read_text() == data

    @pytest.mark.parametrize('html', [True, False])
    def test_markdown_observed_traffic_soar(
        self, playbook_mgr, html, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        alert = mock_request(TPR_MOCK / f'test_markdown_observed_traffic_soar[{node_id}]_0.json')
        enrichs = [
            mock_request(TPR_MOCK / f'test_markdown_observed_traffic_soar[{node_id}]_1.json')
        ]
        soar = SoarMgr()
        mocker.patch.object(playbook_mgr.rf_client, 'request', return_value=alert)
        mocker.patch.object(soar.rf_client, 'request', side_effect=enrichs)

        id_ = 'task:80a78452-d38b-40ea-9a6f-b651698119d0'
        file = Path(__file__).parent / 'markdown' / f'tpr_observed_traffic_soar_html_{html}.md'
        alert = playbook_mgr.fetch(id_, 'third_party_risk')
        ips = soar.soar(ip=alert.all_ip_addresses)

        data = alert.markdown(html_tags=html, extra_context=ips)

        assert file.read_text() == data

    def test_markdown_cyber_trends(self, playbook_mgr, mocker, mock_request):
        alert = mock_request(TPR_MOCK / 'test_markdown_cyber_trends_0.json')
        mocker.patch.object(playbook_mgr.rf_client, 'request', return_value=alert)
        id_ = 'task:a801c6ca-6071-4dcf-9586-b807ccc225d2'
        file = Path(__file__).parent / 'markdown' / 'tpr_cyber_trend.md'
        alert = playbook_mgr.fetch(id_, 'third_party_risk')

        data = alert.markdown()

        assert file.read_text() == data

    def test_markdown_reference(self, playbook_mgr, mocker, mock_request):
        alert = mock_request(TPR_MOCK / 'test_markdown_reference_0.json')
        mocker.patch.object(playbook_mgr.rf_client, 'request', return_value=alert)

        id_ = 'task:aa7eed0a-0c55-4b16-b2e3-062a3b24111d'
        file = Path(__file__).parent / 'markdown' / 'tpr_reference.md'
        alert = playbook_mgr.fetch(id_, 'third_party_risk')

        data = alert.markdown()

        assert file.read_text() == data

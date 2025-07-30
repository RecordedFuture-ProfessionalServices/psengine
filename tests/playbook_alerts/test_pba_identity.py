import re
from pathlib import Path

import pytest

from psengine.playbook_alerts import PACategory, PBA_IdentityNovelExposure, PlaybookAlertMgr
from psengine.playbook_alerts.models.pba_identity_exposures import (
    IdentityPanelEvidence,
    IdentityPanelStatus,
)
from tests.playbook_alerts.conftest import IDENT_MOCK


class Test_IdentityNovelExposures:
    data = [
        ('panel_status', IdentityPanelStatus),
        ('panel_evidence_summary', IdentityPanelEvidence),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_panels(self, alerts_factory, attribute, type_to_check):
        identity_alerts = alerts_factory(PACategory.IDENTITY_NOVEL_EXPOSURES.value)
        for alert in identity_alerts:
            attr = getattr(alert, attribute)
            assert attr is not None
            assert isinstance(attr, type_to_check)

    def test_category(self, alerts_factory):
        identity_alerts = alerts_factory(PACategory.IDENTITY_NOVEL_EXPOSURES.value)
        for alert in identity_alerts:
            assert alert.category == PACategory.IDENTITY_NOVEL_EXPOSURES.value

    def test_identity_novel_exposures(self, alerts_factory):
        identity_novel_exposures_alerts = alerts_factory(PACategory.IDENTITY_NOVEL_EXPOSURES.value)
        for alert in identity_novel_exposures_alerts:
            assert isinstance(alert, PBA_IdentityNovelExposure)

    @pytest.mark.parametrize('panel', ['status', 'summary', 'log'])
    def test_for_each_panel(
        self, playbook_mgr: PlaybookAlertMgr, panel, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_for_each_panel\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(IDENT_MOCK).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        mocker_fetch = mocker.spy(playbook_mgr, 'fetch')
        mocker_post = mocker.spy(playbook_mgr.rf_client, 'request')
        p_alert = playbook_mgr.fetch(
            category=PACategory.IDENTITY_NOVEL_EXPOSURES.value,
            alert_id='task:772eb0bc-807f-4981-a1d5-99710ec30172',
            panels=[panel],
            fetch_images=False,
        )
        assert isinstance(p_alert, PBA_IdentityNovelExposure)
        assert mocker_fetch.call_args[1]['panels'] == [panel]
        assert sorted(mocker_post.call_args[1]['data']['panels']) == sorted({'status', panel})

    data = [
        ('assessment_names', list),
        ('technology_names', list),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_non_log_getters(self, alerts_factory, attribute, type_to_check):
        identity_alerts = alerts_factory(PACategory.IDENTITY_NOVEL_EXPOSURES.value)
        for alert in identity_alerts:
            attr = getattr(alert, attribute)
            assert isinstance(attr, type_to_check)

    def test_markdown(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(IDENT_MOCK / 'test_markdown_0.json'),
            mock_request(IDENT_MOCK / 'test_markdown_1.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        pbas = playbook_mgr.fetch_bulk(category=PACategory.IDENTITY_NOVEL_EXPOSURES.value)
        pbdas_md = [d.markdown() for d in pbas]

        assert all(isinstance(d, str) for d in pbdas_md)
        assert any('Actions to Consider' in d for d in pbdas_md)

    def test_markdown_password_clear(
        self, playbook_mgr: PlaybookAlertMgr, tests_dir, mocker, mock_request
    ):
        mocks = [
            mock_request(IDENT_MOCK / 'test_markdown_password_clear_0.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        pba = playbook_mgr.fetch(
            alert_id='task:af4426fe-7818-4fab-9644-6273182e73eb',
            category=PACategory.IDENTITY_NOVEL_EXPOSURES.value,
        )
        markdown = pba.markdown()

        expected_md = (
            Path(tests_dir) / 'playbook_alerts' / 'markdown' / 'identity_exposure_password_clear.md'
        )
        assert markdown == expected_md.read_text()

    def test_markdown_password_hint(
        self, playbook_mgr: PlaybookAlertMgr, tests_dir, mocker, mock_request
    ):
        mocks = [
            mock_request(IDENT_MOCK / 'test_markdown_password_hint_0.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)
        pba = playbook_mgr.fetch(
            alert_id='task:af4426fe-7818-4fab-9644-6273182e73eb',
            category=PACategory.IDENTITY_NOVEL_EXPOSURES.value,
        )
        # So we dont rotate tokens to an org that does not serve clear text passwords
        # just clear the value to force the markdown to show the hint instead
        pba.panel_evidence_summary.exposed_secret.details.clear_text_value = None
        markdown = pba.markdown()

        expected_md = (
            Path(tests_dir) / 'playbook_alerts' / 'markdown' / 'identity_exposure_password_hint.md'
        )
        assert markdown == expected_md.read_text()

    @pytest.mark.parametrize('char_limit', [500, 1000, 600_000])
    def test_markdown_handle_char_limit(
        self,
        playbook_mgr: PlaybookAlertMgr,
        char_limit,
        mocker,
        mock_request,
        request,
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(
            rf'^test_markdown_handle_char_limit\[{re.escape(node_id)}\]_\d+\.json$'
        )
        files = sorted(f for f in Path(IDENT_MOCK).iterdir() if pattern.match(f.name))
        mocks = [mock_request(f) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        pba = playbook_mgr.fetch(
            alert_id='task:af4426fe-7818-4fab-9644-6273182e73eb',
            category=PACategory.IDENTITY_NOVEL_EXPOSURES.value,
        )

        pba_md = pba.markdown(character_limit=char_limit)
        assert len(pba_md) <= char_limit

    def test_markdown_alert_without_compromised_host(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [
            mock_request(IDENT_MOCK / 'test_markdown_alert_without_compromised_host_0.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        pba = playbook_mgr.fetch(
            alert_id='task:fbbb48f7-ca0d-49a9-9dbf-b4518df4461b',
            category=PACategory.IDENTITY_NOVEL_EXPOSURES.value,
        )
        assert '**Compromised Host:** ' not in pba.markdown()

    def test_markdown_without_all_panels(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [
            mock_request(IDENT_MOCK / 'test_markdown_without_all_panels_0.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        pba_md = playbook_mgr.fetch(
            alert_id='task:af4426fe-7818-4fab-9644-6273182e73eb',
            category=PACategory.IDENTITY_NOVEL_EXPOSURES.value,
            panels=['status'],
        ).markdown()

        assert 'Exposure' in pba_md
        assert '**Identity:** goran.z.radovanovic@norsegods.online' in pba_md

import re
from pathlib import Path

import pytest

from psengine.playbook_alerts import PACategory
from psengine.playbook_alerts.models.pba_geopolitics_facility import (
    GeopolPanelEvents,
    GeopolPanelEvidence,
    GeopolPanelOverview,
    GeopolPanelStatus,
)
from psengine.playbook_alerts.playbook_alert_mgr import PlaybookAlertMgr
from psengine.playbook_alerts.playbook_alerts import PBA_GeopoliticsFacility
from tests.playbook_alerts.conftest import GEO_MOCK


class Test_Geopol:
    data = [
        ('panel_status', GeopolPanelStatus),
        ('panel_evidence_summary', GeopolPanelEvidence),
        ('panel_overview', GeopolPanelOverview),
        ('panel_events_summary', GeopolPanelEvents),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_panels(self, alerts_factory, attribute, type_to_check):
        alerts = alerts_factory(PACategory.GEOPOLITICS_FACILITY.value)
        for alert in alerts:
            attr = getattr(alert, attribute)
            assert attr is not None
            assert isinstance(attr, type_to_check)

    def test_category(self, alerts_factory):
        third_party_alerts = alerts_factory(PACategory.GEOPOLITICS_FACILITY.value)
        for alert in third_party_alerts:
            assert alert.category == PACategory.GEOPOLITICS_FACILITY.value

    @pytest.mark.parametrize('panel', ['status', 'overview', 'events', 'log', 'summary'])
    def test_for_each_panel(
        self, playbook_mgr: PlaybookAlertMgr, panel, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_for_each_panel\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(GEO_MOCK).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        mocker_fetch = mocker.spy(playbook_mgr, 'fetch')
        mocker_post = mocker.spy(playbook_mgr.rf_client, 'request')
        p_alert = playbook_mgr.fetch(
            category=PACategory.GEOPOLITICS_FACILITY.value,
            alert_id='task:3c479160-36ca-4bd0-9fa4-23a226b25bfe',
            panels=[panel],
            fetch_images=False,
        )
        assert isinstance(p_alert, PBA_GeopoliticsFacility)
        assert mocker_fetch.call_args[1]['panels'] == [panel]
        assert sorted(mocker_post.call_args[1]['data']['panels']) == sorted({'status', panel})

    panels = [
        ['status'],
        ['overview'],
        ['events'],
        ['log'],
        ['summary'],
        ['status', 'overview'],
        ['status', 'events'],
        ['status', 'log'],
        ['status', 'summary'],
        ['overview', 'events'],
        ['overview', 'log'],
        ['overview', 'summary'],
        ['events', 'log'],
        ['events', 'summary'],
        ['log', 'summary'],
        ['status', 'overview', 'events'],
        ['status', 'overview', 'log'],
        ['status', 'overview', 'summary'],
        ['status', 'events', 'log'],
        ['status', 'events', 'summary'],
        ['status', 'log', 'summary'],
        ['overview', 'events', 'log'],
        ['overview', 'events', 'summary'],
        ['overview', 'log', 'summary'],
        ['events', 'log', 'summary'],
        ['status', 'overview', 'events', 'log'],
        ['status', 'overview', 'events', 'summary'],
        ['status', 'overview', 'log', 'summary'],
        ['status', 'events', 'log', 'summary'],
        ['overview', 'events', 'log', 'summary'],
        ['status', 'overview', 'events', 'log', 'summary'],
    ]

    @pytest.mark.parametrize('panel', panels)
    def test_markdown_for_each_panel(
        self,
        playbook_mgr: PlaybookAlertMgr,
        panel,
        mocker,
        mock_request,
        request,
        make_binary_response,
    ):
        node_id = request.node.callspec.id
        pattern_json = re.compile(
            rf'^test_markdown_for_each_panel\[{re.escape(node_id)}\]_\d+\.json$'
        )
        pattern_file = re.compile(
            rf'^test_markdown_for_each_panel\[{re.escape(node_id)}\]_\d+\.file$'
        )
        jsons = sorted(f for f in Path(GEO_MOCK).iterdir() if pattern_json.match(f.name))
        files = sorted(f for f in Path(GEO_MOCK).iterdir() if pattern_file.match(f.name))

        mocks = [mock_request(f) for f in jsons]
        mocks += [make_binary_response((GEO_MOCK / f).read_bytes(), {}) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        file = Path(__file__).parent / 'markdown' / f'geopol_{"_".join(panel)}.md'
        alert = playbook_mgr.fetch(
            'task:254a4d64-41f3-434e-a71e-c962c852b099',
            PACategory.GEOPOLITICS_FACILITY.value,
            panels=panel,
        )
        data = alert.markdown()
        assert data == file.read_text()

    def test_markdown_alert_without_image(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [
            mock_request(GEO_MOCK / 'test_markdown_alert_without_image_0.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        file = Path(__file__).parent / 'markdown' / 'geopol_without_image.md'
        alert = playbook_mgr.fetch(
            'task:254a4d64-41f3-434e-a71e-c962c852b099',
            PACategory.GEOPOLITICS_FACILITY.value,
            panels=['status', 'overview', 'events', 'log', 'summary'],
        )
        data = alert.markdown()
        assert data == file.read_text()

    def test_markdown_with_char_limit(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(GEO_MOCK / 'test_markdown_with_char_limit_0.json'),
            *[
                make_binary_response(
                    (GEO_MOCK / f'test_markdown_with_char_limit_{i}.file').read_bytes(),
                    {'Content-Disposition': 'filename=abc.png'},
                )
                for i in range(1, 8)
            ],
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        alert = playbook_mgr.fetch(
            'task:254a4d64-41f3-434e-a71e-c962c852b099',
            PACategory.GEOPOLITICS_FACILITY.value,
            panels=['status', 'overview', 'events', 'log', 'summary'],
        )
        data = alert.markdown(character_limit=5000)
        assert 'Image' not in data

    def test_markdown_fetch_image_off(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(GEO_MOCK / 'test_markdown_fetch_image_off_0.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)
        alert = playbook_mgr.fetch(
            'task:254a4d64-41f3-434e-a71e-c962c852b099',
            PACategory.GEOPOLITICS_FACILITY.value,
            panels=['status', 'overview', 'events', 'log', 'summary'],
            fetch_images=False,
        )
        data = alert.markdown()
        assert 'Image' not in data

import re
from pathlib import Path

import pytest

from psengine.playbook_alerts import PACategory
from psengine.playbook_alerts.models.pba_social_media_impersonation import (
    SocialMediaImpersonationPanelEvidenceSummary,
)
from psengine.playbook_alerts.playbook_alert_mgr import PlaybookAlertMgr
from psengine.playbook_alerts.playbook_alerts import PBA_SocialMediaImpersonation
from tests.playbook_alerts.conftest import SOCIAL_MEDIA_MOCK


class Test_SocialMediaImpersonation:
    data = [('panel_evidence_summary', SocialMediaImpersonationPanelEvidenceSummary)]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_panels(self, alerts_factory, attribute, type_to_check):
        alerts = alerts_factory(PACategory.SOCIAL_MEDIA_IMPERSONATION.value)
        for alert in alerts:
            attr = getattr(alert, attribute)
            assert attr is not None
            assert isinstance(attr, type_to_check)

    def test_category(self, alerts_factory):
        alerts = alerts_factory(PACategory.SOCIAL_MEDIA_IMPERSONATION.value)
        for alert in alerts:
            assert alert.category == PACategory.SOCIAL_MEDIA_IMPERSONATION.value

    @pytest.mark.parametrize('panel', ['summary'])
    def test_for_each_panel(
        self, playbook_mgr: PlaybookAlertMgr, panel, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_for_each_panel\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(SOCIAL_MEDIA_MOCK).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        mocker_fetch = mocker.spy(playbook_mgr, 'fetch')
        mocker_post = mocker.spy(playbook_mgr.rf_client, 'request')
        p_alert = playbook_mgr.fetch(
            category=PACategory.SOCIAL_MEDIA_IMPERSONATION.value,
            alert_id='task:230d3ddf-4211-4166-8beb-cb5e46499661',
            panels=[panel],
            fetch_images=False,
        )
        assert isinstance(p_alert, PBA_SocialMediaImpersonation)
        assert mocker_fetch.call_args[1]['panels'] == [panel]
        assert sorted(mocker_post.call_args[1]['data']['panels']) == sorted({'status', panel})

    def test_markdown(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(SOCIAL_MEDIA_MOCK / 'test_markdown_0.json'),
            mock_request(SOCIAL_MEDIA_MOCK / 'test_markdown_1.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch_bulk(category=PACategory.SOCIAL_MEDIA_IMPERSONATION.value)
        data = [d.markdown() for d in data]

        assert all(isinstance(d, str) for d in data)

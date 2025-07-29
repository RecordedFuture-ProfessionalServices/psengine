import re
from pathlib import Path

import pytest

from psengine.playbook_alerts import PACategory, PBA_CodeRepoLeakage, PlaybookAlertMgr
from psengine.playbook_alerts.models.pba_code_repo_leak import (
    CodeRepoPanelEvidence,
    CodeRepoPanelStatus,
)
from tests.playbook_alerts.conftest import CODE_REPO_MOCK


class Test_CodeRepoLeakage:
    def test_code_repo_leakage(self, alerts_factory):
        code_repo_alerts = alerts_factory(PACategory.CODE_REPO_LEAKAGE.value)
        for alert in code_repo_alerts:
            assert isinstance(alert, PBA_CodeRepoLeakage)

    data = [
        ('panel_status', CodeRepoPanelStatus),
        ('panel_evidence_summary', CodeRepoPanelEvidence),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_panels(self, alerts_factory, attribute, type_to_check):
        code_repo_alerts = alerts_factory(PACategory.CODE_REPO_LEAKAGE.value)
        for alert in code_repo_alerts:
            attr = getattr(alert, attribute)
            assert attr is not None
            assert isinstance(attr, type_to_check)

    @pytest.mark.parametrize('panel', ['status', 'summary', 'log'])
    def test_for_each_panel(
        self, playbook_mgr: PlaybookAlertMgr, panel, mocker, mock_request, request
    ):
        node_id = request.node.callspec.id
        pattern = re.compile(rf'^test_for_each_panel\[{re.escape(node_id)}\]_\d+\.json$')
        files = sorted(f for f in Path(CODE_REPO_MOCK).iterdir() if pattern.match(f.name))

        mocks = [mock_request(f) for f in files]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        mocker_fetch = mocker.spy(playbook_mgr, 'fetch')
        mocker_post = mocker.spy(playbook_mgr.rf_client, 'request')
        p_alert = playbook_mgr.fetch(
            category=PACategory.CODE_REPO_LEAKAGE.value,
            alert_id='task:808123fa-6025-4d64-8652-04ad81c515b9',
            panels=[panel],
        )
        assert isinstance(p_alert, PBA_CodeRepoLeakage)
        assert mocker_fetch.call_args[1]['panels'] == [panel]
        assert sorted(mocker_post.call_args[1]['data']['panels']) == sorted({'status', panel})

    def test_category(self, alerts_factory):
        code_repo_alerts = alerts_factory(PACategory.CODE_REPO_LEAKAGE.value)
        for alert in code_repo_alerts:
            assert alert.category == PACategory.CODE_REPO_LEAKAGE.value

    def test_log_getters(self, alerts_factory):
        code_repo_alerts = alerts_factory(PACategory.CODE_REPO_LEAKAGE.value)
        for alert in code_repo_alerts:
            assert isinstance(alert.panel_log_v2, list)
            assert all(
                isinstance(log, dict) for log in alert.log_code_repo_leakage_evidence_changes
            )

    def test_markdown_fetch(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [mock_request(CODE_REPO_MOCK / 'test_markdown_fetch_0.json')]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch(
            alert_id='task:1be2cbe8-8a0f-494a-89a2-ebfd738bca05', category='code_repo_leakage'
        )
        data = data.markdown()
        assert data == (Path(__file__).parent / 'markdown' / 'code_repo.md').read_text()

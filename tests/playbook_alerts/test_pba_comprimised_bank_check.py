import pytest

from psengine.playbook_alerts import PACategory
from psengine.playbook_alerts.models.pba_compromised_bank_checks import (
    CompromisedBankCheckPanelEvidenceSummary,
    CompromisedBankCheckPanelStatus,
)
from psengine.playbook_alerts.playbook_alert_mgr import PlaybookAlertMgr
from tests.playbook_alerts.conftest import BANK_CHECK_MOCK


class Test_CompromisedBankCheck:
    data = [
        ('panel_status', CompromisedBankCheckPanelStatus),
        ('panel_evidence_summary', CompromisedBankCheckPanelEvidenceSummary),
    ]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_panels(self, alerts_factory, attribute, type_to_check):
        compromised_bank_check_alerts = alerts_factory(PACategory.COMPROMISED_BANK_CHECKS.value)
        for alert in compromised_bank_check_alerts:
            attr = getattr(alert, attribute)
            assert attr is not None
            assert isinstance(attr, type_to_check)

    def test_category(self, alerts_factory):
        compromised_bank_check_alerts = alerts_factory(PACategory.COMPROMISED_BANK_CHECKS.value)
        for alert in compromised_bank_check_alerts:
            assert alert.category == PACategory.COMPROMISED_BANK_CHECKS.value

    data = [('images', dict)]

    @pytest.mark.parametrize(('attribute', 'type_to_check'), data)
    def test_non_alert_gettters(self, alerts_factory, attribute, type_to_check):
        compromised_bank_check_alerts = alerts_factory(PACategory.COMPROMISED_BANK_CHECKS.value)
        for alert in compromised_bank_check_alerts:
            attr = getattr(alert, attribute)
            assert isinstance(attr, type_to_check)

    def test_markdown(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(BANK_CHECK_MOCK / 'test_markdown_0.json'),
            mock_request(BANK_CHECK_MOCK / 'test_markdown_1.json'),
            *[
                make_binary_response(
                    (BANK_CHECK_MOCK / f'test_markdown_{i}.file').read_bytes(),
                    {'Content-Disposition': 'filename=abc.png'},
                )
                for i in range(2, 12)
            ],
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch_bulk(category='fraud_compromised_checks', fetch_images=True)
        data = [d.markdown() for d in data]

        assert all(isinstance(d, str) for d in data)
        assert any('Images' in d for d in data)

    def test_markdown_fetch_images_false(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [
            mock_request(BANK_CHECK_MOCK / 'test_markdown_0.json'),
            mock_request(BANK_CHECK_MOCK / 'test_markdown_1.json'),
        ]

        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.fetch_bulk(category='domain_abuse', fetch_images=False)
        data = [d.markdown() for d in data]

        assert all(isinstance(d, str) for d in data)
        assert all('Images' not in d for d in data)

    def test_markdown_character_limit(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request, make_binary_response
    ):
        mocks = [
            mock_request(BANK_CHECK_MOCK / 'test_markdown_single_alert.json'),
            *[
                make_binary_response(
                    (BANK_CHECK_MOCK / f'test_markdown_{i}.file').read_bytes(),
                    {'Content-Disposition': 'filename=abc.png'},
                )
                for i in range(2, 12)
            ],
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        alert = playbook_mgr.fetch(
            'task:298b983c-cc0c-4f8b-9075-8d525dc098a9', PACategory.COMPROMISED_BANK_CHECKS.value
        )
        markdown = alert.markdown(character_limit=5000)
        assert 'Images' not in markdown
        assert len(markdown) <= 5000

    def test_markdown_single_alert_no_images(
        self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request
    ):
        mocks = [
            mock_request(BANK_CHECK_MOCK / 'test_markdown_single_alert.json')
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        alert = playbook_mgr.fetch(
            'task:298b983c-cc0c-4f8b-9075-8d525dc098a9', PACategory.COMPROMISED_BANK_CHECKS.value,
            fetch_images=False
        )
        markdown = alert.markdown()
        assert "Images" not in markdown


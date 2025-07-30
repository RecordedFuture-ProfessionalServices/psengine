import pytest
from pydantic_core import ValidationError

from psengine.playbook_alerts import PACategory, PBA_Generic
from psengine.playbook_alerts.playbook_alert_mgr import PlaybookAlertMgr
from tests.playbook_alerts.conftest import BASE_MOCK_DIR


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
        generic = PBA_Generic.model_validate(generic.model_dump())
        generic.category = 'moise'
        with pytest.raises(NotImplementedError):
            generic.markdown()

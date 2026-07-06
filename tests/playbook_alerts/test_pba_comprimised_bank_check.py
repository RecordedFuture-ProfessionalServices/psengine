import re
from pathlib import Path

import pytest

from psengine.playbook_alerts import PACategory
from psengine.playbook_alerts.models.pba_compromised_bank_checks import (
    CompromisedBankCheckPanelStatus,
    CompromisedBankCheckPanelEvidenceSummary,
)


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

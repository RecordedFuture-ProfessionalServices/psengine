import json
from pathlib import Path

import pytest

from psengine.playbook_alerts.mappings import CATEGORY_TO_OBJECT_MAP
from psengine.playbook_alerts.pa_category import PACategory
from psengine.playbook_alerts.playbook_alert_mgr import PlaybookAlertMgr

ALERT_TYPE_FNAME_MAP = {
    PACategory.CODE_REPO_LEAKAGE.value: 'code_repo_leakage.json',
    PACategory.COMPROMISED_BANK_CHECKS.value: 'compromised_bank_checks.json',
    PACategory.DOMAIN_ABUSE.value: 'domain_abuse.json',
    PACategory.CYBER_VULNERABILITY.value: 'cyber_vulnerability.json',
    PACategory.IDENTITY_NOVEL_EXPOSURES.value: 'identity_novel_exposures.json',
    PACategory.THIRD_PARTY_RISK.value: 'third_party_risk.json',
    PACategory.GEOPOLITICS_FACILITY.value: 'geopol.json',
    PACategory.MALWARE_REPORT.value: 'malware_report.json',
    PACategory.MALICIOUS_SITES.value: 'malicious_sites.json',
}

BASE_MOCK_DIR = Path(__file__).parent / 'mocks'
BANK_CHECK_MOCK = Path(__file__).parent / 'mocks' / 'bank_checks'
CODE_REPO_MOCK = Path(__file__).parent / 'mocks' / 'code_repo'
MALW_MOCK = Path(__file__).parent / 'mocks' / 'malware'
MALICIOUS_SITES_MOCK = Path(__file__).parent / 'mocks' / 'malicious_sites'
VULN_MOCK = Path(__file__).parent / 'mocks' / 'vuln'
DA_MOCK = Path(__file__).parent / 'mocks' / 'domain_abuse'
GEO_MOCK = Path(__file__).parent / 'mocks' / 'geopol'
IDENT_MOCK = Path(__file__).parent / 'mocks' / 'identity'
TPR_MOCK = Path(__file__).parent / 'mocks' / 'tpr'
MGR_MOCK = Path(__file__).parent / 'mocks' / 'mgr'
MODEL_MOCK = Path(__file__).parent / 'mocks' / 'models'


def load_raw_p_alerts(tests_dir, file_name):
    input_alerts = Path(tests_dir) / 'static' / 'playbook_alerts' / file_name
    with open(input_alerts) as f:
        return json.load(f)


@pytest.fixture
def alerts_factory(tests_dir):
    def _make_alerts(alert_type):
        if alert_type not in ALERT_TYPE_FNAME_MAP:
            raise ValueError(f"Alert type '{alert_type}' not valid")
        raw_alerts = load_raw_p_alerts(tests_dir, ALERT_TYPE_FNAME_MAP[alert_type])
        return [CATEGORY_TO_OBJECT_MAP[alert_type](**alert['data']) for alert in raw_alerts]

    return _make_alerts


@pytest.fixture
def playbook_mgr():
    return PlaybookAlertMgr()

import importlib

import pytest

from psengine import endpoints


class Test_Endpoints:
    def test_prod_endpoints(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv('RF_BASE_URL', raising=False)

        # after mocking the environment variable, we need to reload the endpoints module
        # so it can pick up the new value for the endpoint constants
        importlib.reload(endpoints)

        assert endpoints.EP_CLASSIC_ALERTS_RULES == 'https://api.recordedfuture.com/v2/alert/rule'
        assert endpoints.EP_CLASSIC_ALERTS_ID == 'https://api.recordedfuture.com/v3/alerts/{}'
        assert endpoints.EP_CLASSIC_ALERTS_SEARCH == 'https://api.recordedfuture.com/v3/alerts/'
        assert (
            endpoints.EP_CLASSIC_ALERTS_UPDATE == 'https://api.recordedfuture.com/v2/alert/update'
        )
        assert endpoints.EP_FUSION_FILES == 'https://api.recordedfuture.com/v2/fusion/files'
        assert endpoints.EP_PLAYBOOK_ALERT == 'https://api.recordedfuture.com/playbook-alert'
        assert (
            endpoints.EP_PLAYBOOK_ALERT_SEARCH
            == 'https://api.recordedfuture.com/playbook-alert/search'
        )
        assert (
            endpoints.EP_PLAYBOOK_ALERT_COMMON
            == 'https://api.recordedfuture.com/playbook-alert/common'
        )
        assert (
            endpoints.EP_PLAYBOOK_ALERT_DOMAIN_ABUSE
            == 'https://api.recordedfuture.com/playbook-alert/domain_abuse'
        )
        assert (
            endpoints.EP_PLAYBOOK_ALERT_CYBER_VULNERABILITY
            == 'https://api.recordedfuture.com/playbook-alert/vulnerability'
        )
        assert (
            endpoints.EP_PLAYBOOK_ALERT_CODE_REPO_LEAKAGE
            == 'https://api.recordedfuture.com/playbook-alert/code_repo_leakage'
        )
        assert (
            endpoints.EP_PLAYBOOK_ALERT_THIRD_PARTY_RISK
            == 'https://api.recordedfuture.com/playbook-alert/third_party_risk'
        )
        assert (
            endpoints.EP_PLAYBOOK_ALERT_IDENTITY_NOVEL_EXPOSURES
            == 'https://api.recordedfuture.com/playbook-alert/identity_novel_exposures'
        )
        assert endpoints.EP_ENTITY_MATCH == 'https://api.recordedfuture.com/entity-match/match'
        assert endpoints.EP_LIST == 'https://api.recordedfuture.com/list'
        assert endpoints.EP_CREATE_LIST == 'https://api.recordedfuture.com/list/create'
        assert endpoints.EP_SEARCH_LIST == 'https://api.recordedfuture.com/list/search'

    def test_custom_endpoints(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv('RF_BASE_URL', 'http://newbaseurl.com:8080/api/v3')

        # after mocking the environment variable, we need to reload the endpoints module
        # so it can pick up the new value for the endpoint constants
        importlib.reload(endpoints)

        assert endpoints.EP_CLASSIC_ALERTS_RULES == 'http://newbaseurl.com:8080/api/v3/alert/rule'
        assert endpoints.EP_CLASSIC_ALERTS_ID == 'http://newbaseurl.com:8080/api/v3/v3/alerts/{}'
        assert (
            endpoints.EP_PLAYBOOK_ALERT_CODE_REPO_LEAKAGE
            == 'http://newbaseurl.com:8080/api/v3/playbook-alert/code_repo_leakage'
        )

        monkeypatch.setenv('RF_BASE_URL', 'http://localhost:8080/api/v3')

        importlib.reload(endpoints)

        assert endpoints.EP_CLASSIC_ALERTS_RULES == 'http://localhost:8080/api/v3/alert/rule'

        monkeypatch.setenv('RF_BASE_URL', 'https://newbaseurl.com')

        importlib.reload(endpoints)

        assert (
            endpoints.EP_PLAYBOOK_ALERT_CODE_REPO_LEAKAGE
            == 'https://newbaseurl.com/playbook-alert/code_repo_leakage'
        )
        assert endpoints.EP_DETECTION_RULES == 'https://newbaseurl.com/detection-rule/search'

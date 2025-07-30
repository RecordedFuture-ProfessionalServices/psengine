import pytest

from psengine.playbook_alerts import (
    SearchIn,
    UpdateAlertIn,
)
from psengine.playbook_alerts.playbook_alert_mgr import PlaybookAlertMgr
from tests.playbook_alerts.conftest import MODEL_MOCK


class Test_PBAModels:
    def test_store_image(self, playbook_mgr, mocker, mock_request):
        mock = mock_request(MODEL_MOCK / 'test_store_image_0.json')
        mocker.patch.object(playbook_mgr.rf_client, 'request', return_value=mock)

        alert = playbook_mgr.fetch('task:28d92c9f-efd5-4a3a-a09b-7cd7ede909a4', 'domain_abuse')
        alert.store_image('img:58765072-691a-49f5-b52e-c69776b2c803', '1234')
        assert len(alert._images) == 1

    def test_hash(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mocks = [
            mock_request(MODEL_MOCK / 'test_hash_0.json'),
            mock_request(MODEL_MOCK / 'test_hash_1.json'),
        ]
        mocker.patch.object(playbook_mgr.rf_client, 'request', side_effect=mocks)

        data = playbook_mgr.search(category='domain_abuse')

        pbas = playbook_mgr.fetch_bulk([(d.playbook_alert_id, 'domain_abuse') for d in data.data])
        pba_zero = {pbas[0], pbas[0], pbas[0], pbas[0], pbas[0]}

        assert len(set(pbas)) == 3
        assert len(pba_zero) == 1
        assert pbas[0] == pbas[0]
        assert pbas[0] != pbas[1]
        assert pbas[0] > pbas[1]


class Test_Search_Endpoint:
    payload = [
        {},
        {'limit': 25},
        {'order_by': 'created', 'direction': 'desc'},
        {'entity': ['idn:google.com', 'idn:mail.google.mail.pl']},
        {'statuses': ['New', 'Resolved']},
        {'priority': ['High']},
        {'category': ['domain_abuse', 'cyber_vulnerability']},
        {
            'created_range': {
                'from': '2024-03-11T00:00:00.000Z',
                'until': '2024-03-12T00:00:00.000Z',
            }
        },
        {'updated_range': {'from': '2023-07-18T17:32:28Z', 'until': '2023-07-21T17:32:28Z'}},
        {
            'limit': 10,
            'order_by': 'created',
            'direction': 'asc',
            'entity': ['idn:google.com', 'idn:mail.google.mail.pl'],
        },
        {'updated_range': {'until': '2023-07-21T17:32:28Z'}},
    ]

    @pytest.mark.parametrize('payload', payload)
    def test_payload_validate(self, payload):
        SearchIn.model_validate(payload)

    def test_response_validate(self, playbook_mgr: PlaybookAlertMgr, mocker, mock_request):
        mock = mock_request(MODEL_MOCK / 'test_response_validate_0.json')
        mocker.patch.object(playbook_mgr.rf_client, 'request', return_value=mock)
        playbook_mgr.search()


class Test_Preview_Endpoint:
    payloads = [
        {
            'priority': 'High',
            'status': 'Resolved',
            'assignee': 'uhash:40wXmPVONA',
            'log_entry': 'This has been handled.',
            'reopen': 'Never',
            'added_actions_taken': [
                'cyber_vulnerability.patched',
                'brand_mentions_on_code_repository.keys_rotated',
                'domain_abuse.takedown',
                'third_party_risk.vendor_mitigated_findings',
                'identity_novel_exposures.enforced_password_reset',
            ],
            'removed_actions_taken': [
                'cyber_vulnerability.patched',
                'brand_mentions_on_code_repository.keys_rotated',
                'domain_abuse.takedown',
                'third_party_risk.vendor_mitigated_findings',
                'identity_novel_exposures.enforced_password_reset',
            ],
        },
        {'priority': 'High'},
        {'status': 'Resolved'},
        {'assignee': 'uhash:40wXmPVONA'},
        {'log_entry': 'This has been handled.'},
    ]

    @pytest.mark.parametrize('payload', payloads)
    def test_put_preview(self, payload):
        UpdateAlertIn.model_validate(payload)

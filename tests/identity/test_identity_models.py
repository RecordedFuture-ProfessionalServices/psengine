from datetime import datetime

import pytest
from pydantic import ValidationError

from psengine.identity.models.common_models import (
    FilterIn,
    IdentityOrgIn,
    PasswordHash,
)
from psengine.identity.models.detections import DetectionsFilterIn


class Test_IdentityModels:
    dt = datetime(2025, 5, 20, 18, 34, 20)
    PAYLOADS = [
        ({}, {}),
        (
            {
                'first_downloaded_gte': dt,
                'latest_downloaded_gte': dt,
                'exfiltration_date_gte': dt,
                'properties': ['Letter', 'Number', 'Symbol'],
                'breach_properties': {
                    'date': dt,
                },
                'dump_properties': {
                    'name': 'dump_name',
                },
                'username_properties': ['Email'],
                'authorization_technologies': ['technology_a', 'technology_b'],
                'authorization_protocols': ['protocol_a'],
                'malware_families': ['malware'],
            },
            {
                'first_downloaded_gte': '2025-05-20T18:34:20',
                'latest_downloaded_gte': '2025-05-20T18:34:20',
                'exfiltration_date_gte': '2025-05-20T18:34:20',
                'properties': ['Letter', 'Number', 'Symbol'],
                'breach_properties': {
                    'date': '2025-05-20T18:34:20',
                },
                'dump_properties': {
                    'name': 'dump_name',
                },
                'username_properties': ['Email'],
                'authorization_technologies': ['technology_a', 'technology_b'],
                'authorization_protocols': ['protocol_a'],
                'malware_families': ['malware'],
            },
        ),
        (
            {
                'first_downloaded_gte': dt,
                'latest_downloaded_gte': dt,
                'exfiltration_date_gte': dt,
                'properties': ['Letter', 'Number', 'Symbol'],
                'username_properties': ['Email'],
                'authorization_technologies': ['technology_a', 'technology_b'],
                'authorization_protocols': ['protocol_a'],
                'malware_families': ['malware'],
            },
            {
                'first_downloaded_gte': '2025-05-20T18:34:20',
                'latest_downloaded_gte': '2025-05-20T18:34:20',
                'exfiltration_date_gte': '2025-05-20T18:34:20',
                'properties': ['Letter', 'Number', 'Symbol'],
                'username_properties': ['Email'],
                'authorization_technologies': ['technology_a', 'technology_b'],
                'authorization_protocols': ['protocol_a'],
                'malware_families': ['malware'],
            },
        ),
    ]

    @pytest.mark.parametrize(('payload', 'expected'), PAYLOADS)
    def test_FilterIn(self, payload, expected):
        data = FilterIn.model_validate(payload).json()
        assert data == expected

    BAD_FILTERS = [
        {'first_downloaded_gte': 'string_input'},
        {'first_downloaded_gte': []},
        {'properties': 'string_input'},
        {'properties': 1000},
        {'properties': ['Letter2']},
    ]

    @pytest.mark.parametrize(('payload'), BAD_FILTERS)
    def test_FilterIn_raises_ValidationError(self, payload):
        with pytest.raises(ValidationError):
            FilterIn(**payload)

    BAD_USERNAME_PROPERTIES = [
        {'username_properties': []},
        {'username_properties': ['']},
        {'username_properties': ['Email', 'value']},
        {'username_properties': ['Email', 1]},
        {'username_properties': ['email']},
    ]

    @pytest.mark.parametrize(('payload'), BAD_USERNAME_PROPERTIES)
    def test_FilterIn_raises_ValueError(self, payload):
        with pytest.raises(ValueError, match=r'.*username_properties.*'):
            FilterIn(**payload)

    ORG_IDS = [
        {'organization_id': 'uhash:abcdef'},
        {'organization_id': 'uhash:123456'},
        {'organization_id': 'uhash:a1b2c3'},
        {'organization_id': 'a1b2c3'},
    ]

    @pytest.mark.parametrize(('org_id'), ORG_IDS)
    def test_validate_org_id(self, org_id):
        data = IdentityOrgIn(**org_id)
        assert data.organization_id is not None
        assert data.organization_id.startswith('uhash:')

    BAD_ORG_IDS = [
        {'organization_id': 123456},
        {'organization_id': []},
    ]

    @pytest.mark.parametrize(('org_id'), BAD_ORG_IDS)
    def test_validate_org_id_raises_ValidationError(self, org_id):
        with pytest.raises(ValidationError):
            IdentityOrgIn(**org_id)

    DETECTIONS_IN = [
        ({}, {}),
        (
            {
                'novel_only': True,
                'domains': ['norsegods.online'],
                'detection_type': 'Workforce',
            },
            {
                'novel_only': True,
                'domains': ['norsegods.online'],
                'detection_type': 'Workforce',
            },
        ),
        (
            {
                'novel_only': True,
                'domains': 'norsegods.online',
                'detection_type': 'Workforce',
            },
            {
                'novel_only': True,
                'domains': ['norsegods.online'],
                'detection_type': 'Workforce',
            },
        ),
        (
            {
                'domains': 'norsegods.online',
                'detection_type': 'External',
            },
            {
                'domains': ['norsegods.online'],
                'detection_type': 'External',
            },
        ),
        (
            {
                'novel_only': 1,
                'domains': 'norsegods.online',
                'detection_type': 'External',
            },
            {
                'novel_only': True,
                'domains': ['norsegods.online'],
                'detection_type': 'External',
            },
        ),
    ]

    @pytest.mark.parametrize(('payload', 'expected'), DETECTIONS_IN)
    def test_DetectionsFilterIn(self, payload, expected):
        data = DetectionsFilterIn(**payload).json()
        assert data == expected

    BAD_DETECTIONS_IN = [
        {'domains': [1, 2, 3]},
        {'domains': {'domain': 'norsegods.online'}},
        {'detection_type': ['Workforce', 'External']},
        {'detection_type': 'bad_type'},
    ]

    @pytest.mark.parametrize(('payload'), BAD_DETECTIONS_IN)
    def test_DetectionsFilterIn_raises_ValidationError(self, payload):
        with pytest.raises(ValidationError):
            DetectionsFilterIn(**payload)

    def test_password_hash(self):
        with pytest.raises(ValueError, match=r'One of `hash` or `hash_prefix` must be supplied'):
            PasswordHash(algorithm='SHA1')

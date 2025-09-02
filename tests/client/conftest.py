import os
from pathlib import Path

import pytest

from psengine.base_http_client import BaseHTTPClient

MOCK_DIR = Path(__file__).parent / 'mocks'
RF_TOKEN = 'RF_TOKEN'  # noqa: S105


@pytest.fixture
def base_client():
    return BaseHTTPClient()


@pytest.fixture
def rf_token():
    return os.environ.get(RF_TOKEN)

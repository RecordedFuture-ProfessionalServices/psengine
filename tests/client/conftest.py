import os
from pathlib import Path

import pytest

from psengine.base_http_client import BaseHTTPClient
from psengine.rf_client import RFClient

MOCK_DIR = Path(__file__).parent / 'mocks'
RF_TOKEN = 'RF_TOKEN'  # noqa: S105


@pytest.fixture
def base_client():
    return BaseHTTPClient()


@pytest.fixture
def rf_token():
    return os.environ.get(RF_TOKEN)


@pytest.fixture
def rfc():
    return RFClient()


@pytest.fixture
def make_request_side_effect():
    """
    Returns a factory that builds a side_effect function which:
      - yields from `responses` (an iterable of mocked Response objects)
      - snapshots kwargs['params'] and/or kwargs['data'] at call time
    """

    def _factory(responses, *, capture_params=False, capture_data=False):
        it = iter(responses)
        captured = {'params': [], 'data': []}

        def _side_effect(*args, **kwargs):  # noqa: ARG001
            if capture_params:
                p = kwargs.get('params')
                captured['params'].append(None if p is None else dict(p))
            if capture_data:
                d = kwargs.get('data')
                captured['data'].append(None if d is None else dict(d))
            return next(it)

        return _side_effect, captured

    return _factory

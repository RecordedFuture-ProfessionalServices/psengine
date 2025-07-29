import os
from pathlib import Path

import pytest

MOCK_DIR = Path(__file__).parent / 'mocks'


@pytest.fixture
def csv_filepath(tests_dir):
    return os.path.join(tests_dir, 'static', 'csv', 'test.csv')

import gzip
import io
import json
import sys
from os.path import abspath, dirname
from pathlib import Path

import pytest
from requests import Response

from psengine.analyst_notes.note_mgr import AnalystNoteMgr

ROOT_DIR = dirname(abspath(__file__))
sys.path.append(ROOT_DIR)


def validation_match(note_pattern: str, py310_fallback: str = 'Field required') -> str:
    """Return the regex to match a `ValidationError` message across Python versions.

    `psengine.helpers.validation.validate_list` attaches an entity-identifying note to the raised
    `ValidationError` via `BaseException.add_note`, which only exists on 3.11+. On 3.10 the note
    isn't attached, so tests fall back to matching a substring of the underlying pydantic message.
    """
    return note_pattern if sys.version_info >= (3, 11) else py310_fallback


@pytest.fixture
def mock_request(mocker):
    """return a requests.Response object from a json file."""

    def _inner(file, status_code=200):
        mock = mocker.Mock(spec=Response)
        mock.json.return_value = json.loads(Path(file).read_text())
        mock.status_code = status_code
        return mock

    return _inner


@pytest.fixture
def make_response(mocker):
    """return a requests.Response object from a dict."""

    def _inner(data: dict):
        mock = mocker.Mock(spec=Response)
        mock.json.return_value = data
        mock.status_code = 200
        return mock

    return _inner


@pytest.fixture
def make_binary_response(mocker):
    """return a requests.Response object from a binary."""

    def _inner(data, headers):
        mock = mocker.Mock(spec=Response)
        mock.content = data
        mock.headers = headers
        mock.status_code = 200
        return mock

    return _inner


@pytest.fixture
def make_csv_response(mocker):
    """return a requests.Response object from a csv file or string-like value."""

    def _inner(
        csv_source,
        *,
        gzip_compress: bool = True,
        status_code: int = 200,
    ):
        csv_text = Path(csv_source).read_text() if isinstance(csv_source, Path) else csv_source

        data_bytes = csv_text.encode()
        headers = {
            'content-disposition': 'attachment;filename=test.csv',
            'content-type': 'text/csv',
        }

        if gzip_compress:
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode='wb') as gz:
                gz.write(data_bytes)
            data_bytes = buf.getvalue()
            headers['content-encoding'] = 'gzip'

        mock: Response = mocker.Mock(spec=Response)
        mock.content = data_bytes
        mock.text = csv_text
        mock.raw = io.BytesIO(data_bytes)
        mock.iter_content.return_value = [data_bytes]
        mock.iter_lines.side_effect = lambda *a, **kw: csv_text.splitlines()  # noqa: ARG005
        mock.headers = headers
        mock.status_code = status_code

        return mock

    return _inner


@pytest.fixture
def an_mgr():
    return AnalystNoteMgr()


@pytest.fixture
def tests_dir():
    return ROOT_DIR

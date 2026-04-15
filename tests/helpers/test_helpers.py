import os
import pathlib
import re
import sys
from unittest import mock
from unittest.mock import patch

import pytest
from requests.exceptions import (
    ConnectionError,  # noqa: A004
    ConnectTimeout,
    HTTPError,
    JSONDecodeError,
    ReadTimeout,
    SSLError,
)

from psengine import ReadFileError, WriteFileError
from psengine.analyst_notes.errors import AnalystNoteSearchError
from psengine.analyst_notes.note_mgr import AnalystNoteMgr
from psengine.classic_alerts.classic_alert_mgr import ClassicAlertMgr
from psengine.classic_alerts.errors import AlertFetchError
from psengine.detection.detection_mgr import DetectionMgr
from psengine.detection.errors import DetectionRuleFetchError
from psengine.enrich.soar_mgr import EnrichmentSoarError, SoarMgr
from psengine.entity_lists import EntityListMgr, ListApiError
from psengine.entity_match import EntityMatchMgr, MatchApiError
from psengine.helpers import FileHelpers, FormattingHelpers, OSHelpers, TimeHelpers, dump_models
from psengine.playbook_alerts.errors import PlaybookAlertFetchError
from psengine.playbook_alerts.playbook_alert_mgr import PlaybookAlertMgr
from psengine.risklists.errors import RiskListNotAvailableError
from psengine.risklists.risklist_mgr import RisklistMgr
from tests.helpers.conftest import MOCK_DIR


class Test_TimeHelpers:
    @pytest.mark.parametrize('times', ['1h', '7D'])
    def test_rel_time_to_date(self, times):
        date = TimeHelpers.rel_time_to_date(times)
        match = bool(re.match(r'(^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$)', date))
        assert match is True

    @pytest.mark.parametrize(
        ('time', 'expected'),
        [
            ('1d', True),
            ('1D', True),
            ('-7d', True),
            ('7D', True),
            ('-1h', True),
            ('1H', True),
            ('1h', True),
            ('7H', True),
            ('-20d', True),
            ('30D', True),
            ('70d', True),
            ('-90D', True),
            ('120h', True),
            ('30H', True),
            ('-300h', True),
            ('58H', True),
            ('+1D', True),
            ('+7d', True),
            ('1hour', False),
            ('1HOUR', False),
            ('tendays', False),
            ('1', False),
            ('7', False),
            ('7minutes', False),
            ('10y', False),
            ('120hours', False),
            (None, False),
        ],
    )
    def test_is_rel_time_valid(self, time, expected):
        assert TimeHelpers.is_rel_time_valid(time) is expected

    def test_rel_time_to_date_start_time(self):
        new_time = TimeHelpers.rel_time_to_date('1h', '2024-01-22 13:55:21')
        assert new_time == '2024-01-22T12:55'

    @pytest.mark.parametrize(
        ('rel_time', 'start', 'expected'),
        [
            ('1h', '2022-12-31 00:00:00', '2022-12-30T23:00'),
            ('-1h', '2022-12-31 00:00:00', '2022-12-30T23:00'),
            ('+1h', '2022-12-31 23:00:00', '2023-01-01T00:00'),
            ('+1d', '2023-12-31 23:20:00', '2024-01-01T23:20'),
        ],
    )
    def test_rel_time_to_date_start_time_increment(self, rel_time, start, expected):
        new_time = TimeHelpers.rel_time_to_date(rel_time, start)
        assert new_time == expected

    @pytest.mark.parametrize(
        ('time', 'error'),
        [
            ('1h', None),
            ('-1h', None),
            ('--1h', ValueError),
            ('1hour', ValueError),
            ('2017', ValueError),
        ],
    )
    def test_rel_time_to_date_raises_ValueError(self, time, error):
        if error is None:
            assert TimeHelpers.rel_time_to_date(time)
        else:
            with pytest.raises(
                error,
                match=re.escape(
                    f"Invalid relative time '{time}'. Accepted format: [-|+]?[integer][h|d]"
                ),
            ):
                TimeHelpers.rel_time_to_date(time)

    @pytest.mark.parametrize(
        ('time_range', 'expected'),
        [
            ('[2021-08-08T13:11 TO 2021-08-08T13:11]', False),
            ('[2021-08-08T13:11,2021-08-08T13:11', False),
            ('(2021-08-08,2021-08-08T13:11', False),
            ('2021,2023]', False),
            (',2023-11-12)', False),
            ('1HOUR', False),
            ('tendays', False),
            ('1', False),
            ('7', False),
            ('7minutes', False),
            ('10y', False),
            ('120hours', False),
            (None, False),
            ('[-24h,]', True),
            ('(-72d, -7d]', True),
            ('[2017-07-31,2017-07-30]', True),
            ('[2017-07-30,2017-07-31]', True),
            ('[2017-07-30T10:18:06,2017-07-31]', True),
            ('(2017-07-30,2017-07-31)', True),
            ('[2017-07-30,2017-07-31)', True),
            ('[2017-07-30,)', True),
            ('[,2017-07-31)', True),
            ('[,]', True),
        ],
    )
    def test_is_valid_time_range(self, time_range, expected):
        assert TimeHelpers.is_valid_time_range(time_range) is expected


class Test_OSHelper:
    def test_os_platform(self):
        # Unfortunatelly, this will return a different value depending on the OS it runs on
        # so can not be properly tested, hence we make sure it returns something
        os_info = OSHelpers.os_platform()

        assert len(os_info)
        assert isinstance(os_info, str)

    def test_mkdir_raises_ValueError(self):
        with pytest.raises(ValueError, match='path cannot be empty'):
            OSHelpers.mkdir('')

    def test_mkdir_abs_path_and_access_return_path(self, tmp_path):
        assert OSHelpers.mkdir(tmp_path) == tmp_path

    def test_mkdir_handles_PermissionError(self):
        with patch.object(pathlib.Path, 'mkdir') as mock_path:
            mock_path.side_effect = PermissionError()

            with pytest.raises(WriteFileError):
                OSHelpers.mkdir('tmp_path')

    def test_mkdir_rel_path_success(self, tmp_path):
        directory = tmp_path / 'sub'
        str_directory = directory.as_posix()

        with patch.object(sys, 'path', [str(tmp_path)]):
            result = OSHelpers.mkdir('sub')

        assert result == directory
        assert result.as_posix() == str_directory
        assert os.path.isdir(str_directory)

    def test_mkdir_handles_os_access(self, mocker: mock, tmp_path):
        mock_access = mocker.patch('os.access')
        mock_access.return_value = 0

        with pytest.raises(WriteFileError):
            OSHelpers.mkdir(str(tmp_path))


class Test_FileHelpers:
    def test_read_csv(self, csv_filepath):
        rows_as_tuples = FileHelpers.read_csv(csv_filepath)
        assert len(rows_as_tuples) == 3
        assert rows_as_tuples[0][0] == 'State'
        assert rows_as_tuples[0][1] == 'Population'
        assert rows_as_tuples[1][0] == 'CO'
        assert rows_as_tuples[1][1] == '5812000'
        assert rows_as_tuples[2][0] == 'TX'
        assert rows_as_tuples[2][1] == '29530000'

    def test_read_csv_as_dict_true(self, csv_filepath):
        rows_as_dicts = FileHelpers.read_csv(csv_filepath, as_dict=True)
        assert len(rows_as_dicts) == 2
        assert rows_as_dicts[0]['State'] == 'CO'
        assert rows_as_dicts[0]['Population'] == '5812000'
        assert rows_as_dicts[1]['State'] == 'TX'
        assert rows_as_dicts[1]['Population'] == '29530000'

    def test_read_csv_single_column_true(self, csv_filepath):
        rows_with_one_value = FileHelpers.read_csv(csv_filepath, single_column=True)
        assert len(rows_with_one_value) == 3
        assert rows_with_one_value[0] == 'State'
        assert rows_with_one_value[1] == 'CO'
        assert rows_with_one_value[2] == 'TX'

    @pytest.mark.parametrize(('as_dict', 'single_column'), [(True, True), (4, [1])])
    def test_read_csv_raises_ValueError(self, csv_filepath, as_dict, single_column):
        with pytest.raises(ValueError, match='Cannot use as_dict and single_column together'):
            FileHelpers.read_csv(csv_filepath, as_dict=as_dict, single_column=single_column)

    def test_read_csv_raises_ReadFileError(self):
        with pytest.raises(ReadFileError):
            FileHelpers.read_csv('non_existent_file.csv')

    def test_write_file(self, tmpdir):
        FileHelpers.write_file(b'Hello World', tmpdir, 'test.txt')

    def test_write_file_raises_WriteFileError(self):
        with pytest.raises(WriteFileError):
            FileHelpers.write_file(b'Hello World', '/non_existent_dir', 'test.txt')


def test_dump_model(mocker, mock_request):
    mock = mock_request(MOCK_DIR / 'test_dump_model.json')
    mgr = SoarMgr()

    mocker.patch.object(mgr.rf_client, 'request', return_value=mock)
    data = mgr.soar(ip=['1.1.1.1', '8.8.8.8'])

    dumped_data = dump_models(data)
    assert dumped_data == [
        '{"entity": "1.1.1.1", "is_enriched": true, "content": {"risk": {"score": 0, '
        '"level": 0, "context": {"phishing": {"score": 0, "rule": {"count": 0, '
        '"maxCount": 3}}, "public": {"score": 0, "rule": {"maxCount": 79}, "summary": '
        '[], "mostCriticalRule": ""}, "c2": {"score": 0, "rule": {"count": 0, '
        '"maxCount": 7}}}, "rule": {"count": 0, "maxCount": 79, "summary": [], '
        '"mostCritical": ""}}, "entity": {"id": "ip:1.1.1.1", "name": "1.1.1.1", '
        '"type": "IpAddress"}}}',
        '{"entity": "8.8.8.8", "is_enriched": true, "content": {"risk": {"score": 0, '
        '"level": 0, "context": {"phishing": {"score": 0, "rule": {"count": 0, '
        '"maxCount": 3}}, "public": {"score": 0, "rule": {"maxCount": 79}, "summary": '
        '[], "mostCriticalRule": ""}, "c2": {"score": 0, "rule": {"count": 0, '
        '"maxCount": 7}}}, "rule": {"count": 0, "maxCount": 79, "summary": [], '
        '"mostCritical": ""}}, "entity": {"id": "ip:8.8.8.8", "name": "8.8.8.8", '
        '"type": "IpAddress"}}}',
    ]


methods = [
    (AnalystNoteMgr, 'search', ['abcde'], AnalystNoteSearchError, None),
    (ClassicAlertMgr, 'fetch', ['abcde'], AlertFetchError, None),
    (DetectionMgr, 'fetch', ['abcde'], DetectionRuleFetchError, 'Error in fething of abcde'),
    (EntityListMgr, 'search', ['meow'], ListApiError, None),
    (EntityMatchMgr, 'lookup', ['ip:8.8.8.8'], MatchApiError, None),
    (PlaybookAlertMgr, 'fetch', ['id:asbd'], PlaybookAlertFetchError, None),
    (RisklistMgr, 'fetch_risklist', ['abcde', 'domain'], RiskListNotAvailableError, None),
    (SoarMgr, 'soar', [['8.8.8.8']], EnrichmentSoarError, None),
]

exceptions = [
    HTTPError('moise'),
    ConnectTimeout('moise'),
    ConnectionError('moise'),
    ReadTimeout('moise'),
    OSError('moise'),
    SSLError('moise'),
    JSONDecodeError('moise', '', 0),
    KeyError('moise'),
]


@pytest.mark.parametrize(('mgr', 'method', 'args', 'pse_exception', 'match_string'), methods)
@pytest.mark.parametrize('py_exception', exceptions)
def test_exceptions(mgr, method, args, pse_exception, match_string, py_exception, mocker):
    mgr = mgr()
    mocker.patch.object(mgr.rf_client, 'request', side_effect=py_exception)
    with pytest.raises(pse_exception, match=match_string or 'moise'):  # noqa: PT012
        data = getattr(mgr, method)(*args)
        if isinstance(mgr, RisklistMgr):
            next(data)


class Test_FormattingHelpers:
    data = [
        ('ip:1.1.1.1', '1.1.1.1'),
        ('idn:google.com', 'google.com'),
        ('hash:abcde', 'abcde'),
        ('url:https://google.om', 'https://google.om'),
        ('id:abcd', 'abcd'),
    ]

    @pytest.mark.parametrize(('entity', 'expected'), data)
    def test_formatting_removes_id(self, entity, expected):
        assert FormattingHelpers.cleanup_rf_id(entity) == expected

    def test_formatting_doesnt_remove(self):
        assert FormattingHelpers.cleanup_rf_id('abc:test') == 'abc:test'

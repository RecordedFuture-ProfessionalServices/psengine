import logging
import os
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from psengine import WriteFileError
from psengine.logger import LoggingError, RFLogger


@pytest.fixture
def rf_logger():
    rfl = RFLogger()
    yield rfl
    log = rfl.get_logger()
    log.handlers.clear()


@pytest.fixture
def mock_excepthook():
    sys_hook = sys.__excepthook__
    sys.__excepthook__ = Mock()
    yield sys.__excepthook__
    sys.__excepthook__ = sys_hook


class Test_Logger:
    def test_logger_file_handler(self, rf_logger, tmp_path):
        handler = rf_logger._create_file_handler(tmp_path / 'test.log')
        assert isinstance(handler, logging.handlers.RotatingFileHandler)
        assert handler.baseFilename.endswith('test.log')
        assert handler.mode == 'a'
        assert handler.formatter._fmt == (
            '%(asctime)s,%(msecs)03d [%(threadName)s] %(levelname)s'
            ' [%(module)s] %(funcName)s:%(lineno)d - %(message)s'
        )
        assert handler.formatter.datefmt == '%Y-%m-%d %H:%M:%S'

    def test_logger_create_console_handler(self, rf_logger):
        handler = rf_logger._create_console_handler()
        assert isinstance(handler, logging.StreamHandler)
        assert (
            handler.formatter._fmt
            == '%(asctime)s,%(msecs)03d %(levelname)s [%(module)s] - %(message)s'
        )
        assert handler.formatter.datefmt == '%Y-%m-%d %H:%M:%S'

    def test_setup_output_abspath(self, tmp_path, rf_logger):
        assert rf_logger._setup_output(tmp_path.as_posix()) == tmp_path.as_posix()

    def test_setup_output_relpath(self, rf_logger, mocker):
        mock_mkdir = mocker.patch('psengine.helpers.OSHelpers.mkdir')
        mock_mkdir.return_value = 0

        output_path = rf_logger._setup_output('test')
        assert output_path.endswith('/test')
        assert not output_path.startswith('test')
        assert os.path.isabs(output_path)

    def test_setup_output_LoggingError(self, rf_logger, mocker):
        mock_mkdir = mocker.patch('psengine.helpers.OSHelpers.mkdir')
        mock_mkdir.side_effect = WriteFileError()

        with pytest.raises(LoggingError) as exc_info:
            rf_logger._setup_output('test')

        assert str(exc_info.value).startswith('Unable to create logging directory. Cause')

    def test_log_uncaught_exception_keyboard_interrupt(self, rf_logger, capfd, mock_excepthook):
        exc_type, exc_value, exc_traceback = (
            KeyboardInterrupt,
            Exception('keyboard interrupt'),
            None,
        )
        val = rf_logger._log_uncaught_exception(exc_type, exc_value, exc_traceback)

        mock_excepthook.assert_called_once_with(exc_type, exc_value, exc_traceback)
        assert capfd.readouterr() == ('', '')
        assert val is None

    def test_log_uncaught_exception_general(self, mock_excepthook, tmp_path):
        exc_type, exc_value, exc_traceback = (
            Exception,
            Exception('general exception'),
            Exception('general exception').__traceback__,
        )
        logger = RFLogger(
            output=Path(tmp_path / 'psengine_recfut.log').as_posix(), to_console=False, to_file=True
        )
        logger._log_uncaught_exception(exc_type, exc_value, exc_traceback)
        data = (tmp_path / 'psengine_recfut.log').open().read()

        assert 'An unexpected error has occurred:' in data
        assert '========================' in data
        mock_excepthook.assert_not_called()

    def test_get_logger(self, rf_logger):
        assert isinstance(rf_logger.get_logger(), logging.Logger)

    def test_loglevel_info(self, capfd, rf_logger):
        log = rf_logger.get_logger()
        log.info('test info')
        log.debug('test debug')
        captured = capfd.readouterr()
        assert log.level == logging.INFO
        assert 'test info' in captured.err
        assert 'test debug' not in captured.err

    def test_loglevel_warning(self, capfd):
        log = RFLogger(level=logging.WARNING).get_logger()
        log.warning('test warning')
        log.info('test info')
        captured = capfd.readouterr()
        assert log.level == logging.WARNING
        assert 'test warning' in captured.err
        assert 'test info' not in captured.err

    def test_log_setlevel(self, capfd, rf_logger):
        log = rf_logger.get_logger()
        log.setLevel('ERROR')
        log.error('test error')
        log.info('test info')
        captured = capfd.readouterr()
        assert log.level == logging.ERROR
        assert 'test error' in captured.err
        assert 'test info' not in captured.err

    data = [
        (
            'BADLEVEL',
            ValueError,
            'level must be one of: NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL',
        ),
        ('50', ValueError, 'level must be one of: NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL'),
        (['list'], TypeError, ''),
        (999, ValueError, 'level must be one of: NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL'),
    ]

    @pytest.mark.parametrize(('data', 'error', 'match'), data)
    def test_loglevel_error(self, data, error, match):
        with pytest.raises(error, match=match):
            RFLogger(level=data)

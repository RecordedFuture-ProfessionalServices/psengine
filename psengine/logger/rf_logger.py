##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

import logging
import logging.config
import sys
from pathlib import Path

from ..errors import WriteFileError
from ..helpers.helpers import OSHelpers
from .constants import (
    BACKUP_COUNT,
    CONSOLE_FORMAT,
    DATE_FORMAT,
    DEFAULT_PSENGINE_OUTPUT,
    DEFAULT_ROOT_OUTPUT,
    FILE_FORMAT,
    LOGGER_LEVEL,
    LOGGER_LEVEL_INT,
    LOGGER_NAME,
    MAX_BYTES,
)
from .errors import LoggingError


class RFLogger:
    """Sets up logging and gives access to its functions."""

    def __init__(
        self,
        output: str = DEFAULT_PSENGINE_OUTPUT,
        root_output: str = DEFAULT_ROOT_OUTPUT,
        level=logging.INFO,
        propagate: bool = True,
        to_file=True,
        to_console=True,
        console_is_root=True,
    ):
        if to_file is False and to_console is False:
            raise ValueError('At least one of to_file or to_console must be set to True')

        if not isinstance(level, (str, int)):
            raise TypeError('level must be a string or int')
        if isinstance(level, str):
            level = level.upper()
            if level not in LOGGER_LEVEL:
                raise ValueError(f'level must be one of: {", ".join(LOGGER_LEVEL)}')
        if isinstance(level, int) and level not in LOGGER_LEVEL_INT:
            raise ValueError(f'level must be one of: {", ".join(LOGGER_LEVEL)}')

        # Setup logging handlers
        self.logger = logging.getLogger(LOGGER_NAME)
        root_logger = logging.getLogger()

        if to_file:
            psengine_file_handler = self._create_file_handler(output)
            root_file_handler = self._create_file_handler(root_output)
            self.logger.addHandler(psengine_file_handler)
            root_logger.addHandler(root_file_handler)

        if to_console:
            console_handler = self._create_console_handler()
            if console_is_root:
                root_logger.addHandler(console_handler)
            else:
                self.logger.addHandler(console_handler)

        # If false then logging messages are not passed to the handlers of ancestor loggers
        self.logger.propagate = propagate

        logging.captureWarnings(True)

        sys.excepthook = self._log_uncaught_exception

        self.logger.setLevel(level=level)
        self.logger.debug('Logger initialized')

    def _create_file_handler(self, output):
        log_filename = self._setup_output(output)

        file_handler = logging.handlers.RotatingFileHandler(
            log_filename,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
        )
        formatter_file = logging.Formatter(fmt=FILE_FORMAT, datefmt=DATE_FORMAT)
        file_handler.setFormatter(formatter_file)

        return file_handler

    def _create_console_handler(self):
        console_handler = logging.StreamHandler()
        formatter_console = logging.Formatter(fmt=CONSOLE_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(formatter_console)

        return console_handler

    def _setup_output(self, output):
        """Confirms path is valid, returns cwd path and log cfg fullpath.

        Args:
            output (str): logging output path

        Raises:
            LoggingError: Raised when logging path does not exist

        Returns:
            str: cwd path
        """
        output = Path(output)
        if output.is_absolute():
            dir_name = output.parent
            full_path = output
        else:
            main_dir = sys.path[0]
            full_path = Path(main_dir) / output
            dir_name = full_path.parent

        try:
            OSHelpers.mkdir(dir_name)
        except (WriteFileError, ValueError) as err:
            raise LoggingError(f'Unable to create logging directory. Cause: {err}') from err

        return full_path.as_posix()

    def _log_uncaught_exception(self, exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        self.logger.critical(
            'An unexpected error has occurred:\n========================\n',
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    def get_logger(self) -> logging.Logger:
        """Returns self.logger object."""
        return self.logger

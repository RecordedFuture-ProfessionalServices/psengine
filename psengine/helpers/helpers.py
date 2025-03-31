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
import csv
import functools
import json
import logging
import os
import platform
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from inspect import getmodule, isclass, signature
from pathlib import Path
from typing import Callable, Union

from dateutil.parser import parse as date_parse
from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    HTTPError,
    JSONDecodeError,
    ReadTimeout,
    SSLError,
)

from ..common_models import RFBaseModel
from ..constants import ROOT_DIR
from ..errors import ReadFileError, RecordedFutureError, WriteFileError

LOG = logging.getLogger('psengine.helpers')
VALID_TIME_REGEX = r'^(-?)([1-9]?[0-9]+[dDhH])$'
IDS = ['ip:', 'idn:', 'url:', 'hash:', 'id:']


def connection_exceptions(
    ignore_status_code: list[int], exception_to_raise: RecordedFutureError, on_ignore_return=None
):
    """Decorator for handling HTTP related errors.

    Args:
        ignore_status_code (List[int]): list of status codes to be ignored - dont raise exception
        exception_to_raise (Exception): exception to raise in case of error. It should be based on
            the function that is decorated
        on_ignore_return (Any): whatever it is needed to be returned if the ignore_status happens.
        Defaults to None.

    Raises:
        exception_to_raise

    Returns:
        Any: whatever the function decorated returns

    """

    def wrapper(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            self = args[0]

            try:
                return func(*args, **kwargs)
            except HTTPError as err:
                if err.response is not None and err.response.status_code in ignore_status_code:
                    msg = (
                        f"Requested data by {func.__name__} wasn't found or you cannot view it. "
                        f'Error: {err}'
                    )
                    self.log.info(msg)
                    return on_ignore_return

                self.log.error(f'HTTPError in {func.__name__}. Error: {err}')
                raise exception_to_raise(message=str(err)) from err

            except (ConnectTimeout, ConnectionError, ReadTimeout) as err:
                self.log.error(f'Connection error in {func.__name__}. Error: {err}')
                raise exception_to_raise(message=str(err)) from err

            except (OSError, SSLError) as err:
                self.log.error(
                    f'Possible error with custom certificate {err} when calling {func.__name__}'
                )
                raise exception_to_raise(message=str(err)) from err

            except (JSONDecodeError, KeyError) as err:
                self.log.error(f'Incorrect data returned by {func.__name__}. Error: {err}')
                raise exception_to_raise(message=str(err)) from err

        return wrapped

    return wrapper


def dump_models(models) -> list:
    """Return a list of model dumped as json."""
    return (
        [json.dumps(model.json()) for model in models]
        if isinstance(models, list)
        else [json.dumps(models.json())]
    )


def debug_call(func):
    """Print debug logs for public methods."""
    original_func = func
    while hasattr(original_func, '__wrapped__'):
        original_func = original_func.__wrapped__
    func_module = getmodule(original_func)

    sig = signature(func)
    param_names = list(sig.parameters.keys())

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args_to_print = args

        logger = logging.getLogger(func_module.__name__)

        if param_names and param_names[0] in ('self', 'cls') and args:
            args_to_print = args[1:]

        def format_arg(x):
            return str(x)[:50] if isclass(x) and issubclass(x, RFBaseModel) else str(x)[:200]

        kwargs_to_print = {k: v for k, v in kwargs.items() if k != 'headers'}
        args_str = ', '.join(format_arg(x) for x in args_to_print)
        kwargs_str = ', '.join(f'{k}={str(v)!r}' for k, v in kwargs_to_print.items())
        if args_str or kwargs_str:
            sep = ', ' if args_str and kwargs_str else ''
            msg = f'Called {func.__qualname__}({args_str}{sep}{kwargs_str})'
        else:
            msg = f'Called {func.__qualname__}()'

        logger.debug(msg)
        ret_val = func(*args, **kwargs)

        msg = f'{func.__qualname__} ended with return value {str(ret_val)[:50]!r}'
        logger.debug(msg)

        return ret_val

    return wrapper


class TimeHelpers:
    """Helpers for time related functions."""

    @staticmethod
    def rel_time_to_date(relative_time) -> str:
        """Convert a relative time to a date. Minutes not supported.

        Example:
            .. code-block::

                1h - > Return -1h from NOW
                1d - > Return -1d from NOW.

        Args:
            relative_time (str): 7d, 3h, etc..

        Raises:
            ValueError: if the relative time is invalid

        Returns:
            str: time delta, for example: ``2022-08-08T13:11``
        """
        logger = logging.getLogger(__name__)
        match = re.match(VALID_TIME_REGEX, relative_time)
        if match is None:
            raise ValueError(
                f"Invalid relative time '{relative_time}'. Accepted format: [-|][integer][h|d]",
            )
        else:
            relative_time = match.groups()[-1]
            time_now = datetime.utcnow()
            digit = int(re.findall(r'^\d+', relative_time)[0])
            if relative_time.endswith('d'):
                subtracted = (time_now - timedelta(days=digit)).strftime('%Y-%m-%dT%H:%M')
            else:
                subtracted = (time_now - timedelta(hours=digit)).strftime('%Y-%m-%dT%H:%M')
            logger.debug(f'UTC Time now: {time_now}')
            logger.debug(f'Relative time -{relative_time} to date: {subtracted}')

            return subtracted

    @staticmethod
    def is_rel_time_valid(rel_time) -> bool:
        """Helper function to determine if relative time expression is valid.

        Args:
            rel_time (str): relative time

        Returns:
            bool: True if valid, False otherwise
        """
        if rel_time is None:
            return False

        return bool(re.match(VALID_TIME_REGEX, rel_time))

    @staticmethod
    def is_valid_time_range(range_: str) -> bool:
        """Verifies if an ISO 8601 compliant time range was specified.

        Example:

            .. code-block::

                [2017-07-30,2017-07-31]
                (2017-07-30,2017-07-31)
                [2017-07-30,2017-07-31)
                [2017-07-30,)
                [,2017-07-31)
                https://www.elastic.co/guide/en/elasticsearch/reference/current/date.html.

        Args:
            range_ (str): time range

        Returns:
            bool: True if valid, False otherwise
        """
        if range_ is None:
            return False

        match = re.match(r'^(\[|\()(.*)?,\s*(.*)?(\]|\))$', range_)
        if match is None:
            return False

        start_time, end_time = match.groups()[1], match.groups()[2]
        try:
            if start_time != '' and not TimeHelpers.is_rel_time_valid(start_time):
                date_parse(start_time)
            if end_time != '' and not TimeHelpers.is_rel_time_valid(end_time):
                date_parse(end_time)
        except ValueError:
            return False
        return True


class FormattingHelpers:
    """Helpers for formatting related functions."""

    @staticmethod
    def cleanup_ai_insights(ai_insights: str) -> str:
        """Clean up RF AI Insights to avoid markdown rendering issues.

        Args:
            ai_insights (str): ai insights

        Returns:
            str: cleaned up ai insights
        """
        return ai_insights.replace('\n', ' ').replace('1. ', '1.')

    @staticmethod
    def cleanup_rf_id(entity: str) -> str:
        """Remove the Recorded Future id prefix from an entity."""
        for id_ in IDS:
            if id_ in entity:
                return entity.replace(id_, '')
        return entity


class OSHelpers:
    """Helpers for OS related functions."""

    @staticmethod
    def os_platform():
        """Get the OS platform information, for example: ``macOS-13.0-x86_64-i386-64bit``.

        Returns:
            str: OS platform info, if unavailable return None
        """
        return platform.platform(aliased=True, terse=False) or None

    @staticmethod
    def mkdir(path: Union[str, Path]) -> Path:
        """Safely create a directory.

        Args:
            path (str or Path): path to directory

        Raises:
            ValueError: if path is not a string or is empty
            WriteFileError: if directory is not writeable

        Returns:
            Path: path to directory created
        """
        if path == '':
            raise ValueError('path cannot be empty')

        path = Path(path)
        LOG.debug(f'Creating directory: {path.as_posix()}')
        if not path.is_absolute():
            path = Path(sys.path[0]) / path
        if path.is_dir() and os.access(path, os.W_OK):
            return path
        try:
            path.mkdir(parents=True, exist_ok=True)
        except PermissionError as err:
            raise WriteFileError(f'Directory {path} is not writeable') from err
        # In case it already exists, check if it is writeable
        if not os.access(path, os.W_OK):
            raise WriteFileError(f'Directory {path} is not writeable')
        return path


class FileHelpers:
    """Helpers for file related functions."""

    @staticmethod
    def read_csv(
        csv_file: Union[str, Path], as_dict: bool = False, single_column: bool = False
    ) -> list:
        """Reads all rows from a CSV.

        It is the client's responsibility to ensure column headers are handled appropriately.

        Using ``as_dict`` will reader the CSV with ``csv.DictReader``, which treats the first row
        as column headers. For example with CSV

        .. code-block::

            Name,ID,Level
            Patrick,321,4
            Ernest,123,8

        ``as_dict=True`` will return a list of dictionaries keyed by header names

        .. code-block::

            [{'Name': 'Patrick', 'ID': '321', 'Level': '4'},
            {'Name': 'Ernest', 'ID': '123', 'Level': '8'}]


        ``single_column=True`` will return a list of only the first column of the CSV
        as strings (note that ``as_dict=False``, ``single_column=False`` returns a list of lists)::

            ['Name', 'Patrick', 'Ernest']

        ``as_dict=False`` and ``single_column=False`` will return a list of lists::

            [['Name', 'ID', 'Level'], ['Patrick', '321', '4'], ['Ernest', '123', '8']]

        Args:
            csv_file (str or Path): path to CSV file
            as_dict (bool, optional): return entities as a dict. Defaults to False.
            single_column (bool, optional): return only entities (not lists) from first column
                cannot be used with ``as_dict``. Defaults to False.

        Raises:
            ValueError: If both ``as_dict`` and ``single_column`` are True
            ReadFileError: If file is not found or has restricted access

        Returns:
            list of rows from CSV
        """
        if as_dict and single_column:
            raise ValueError('Cannot use as_dict and single_column together')

        csv_file = Path(csv_file)
        if not csv_file.is_absolute():
            LOG.debug(
                f'{csv_file} is not an absolute path. Attempting to find it in {ROOT_DIR}',
            )
            file_path = Path(ROOT_DIR) / csv_file
        else:
            file_path = csv_file
        try:
            with file_path.open() as file_obj:
                if as_dict:
                    reader = csv.DictReader(file_obj)
                    return list(reader)

                reader = csv.reader(file_obj)
                if single_column:
                    return [row[0] for row in reader]

                return list(reader)
        except OSError as oe:
            raise ReadFileError(f'Error reading entity file: {str(oe)}') from oe

    @staticmethod
    def write_file(to_write: str, output_directory: Union[str, Path], fname: str) -> Path:
        """Write bytes to file.

        Args:
            to_write (bytes): bytes to write to file
            output_directory (str or Path): path to directory to write file
            fname (str): name of file to write

        Returns:
            Path: path to file written
        """
        LOG.info(f'Writing file: {fname}')
        output_directory = Path(output_directory)
        try:
            if not output_directory.is_absolute():
                output_directory = OSHelpers.mkdir(output_directory)
            full_path = output_directory / fname
            with full_path.open('wb') as f:
                f.write(to_write)
        except OSError as err:
            raise WriteFileError(f"Error writing file '{err.filename}': {str(err)}") from err

        LOG.info(f'File written to: {full_path.as_posix()}')
        return full_path


class MultiThreadingHelper:
    """Multithreading class."""

    @staticmethod
    def multithread_it(max_workers: int, func: Callable, *, iterator, **kwargs) -> list:
        """Multithreading helper for I/O Operations.

        The class can be used in the following way. Given a single thread code like:

            .. code-block:: python
                :linenos:

                def _lookup_alert(self, alert_id, index, total_num_of_alerts):
                    ...

                def all_alerts(self, alerts):
                    res = []
                    for index, alert_id in enumerate(alert_ids_to_fetch):
                        res.append(self._lookup_alert(alert_id, index, len(alert_ids_to_fetch)))

        It can be rewritten like:

            .. code-block:: python
                :linenos:

                def _lookup_alert(self, alert_id, index, total_num_of_alerts):
                    ...

                def all_alerts(self, alerts):
                    results = MultiThreadingHelper.multithread_it(
                        self.max_workers,
                        self._lookup_alert,
                        iterator=alert_ids_to_fetch,
                        total_num_of_alerts=len(alert_ids_to_fetch)
                    )

        Args:
            max_workers (int): Number of threads to use.
            func (Callable): Function to be executed in parallel.
            iterator (iterator): The list of elements to be dispatched to the threads.
                Example: This can be the list of alerts to download, the IOCs, etc.
            kwargs: Any other argument that the function needs for execution.
                Example: The Alert type, or the IOC type.

        Returns:
            List of objects returned by the calling function.
        """
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(func, element, **kwargs) for element in iterator]

        return [f.result() for f in futures]

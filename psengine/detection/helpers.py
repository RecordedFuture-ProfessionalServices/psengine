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
from pathlib import Path
from typing import Union

from pydantic import validate_call

from ..errors import WriteFileError
from ..helpers import OSHelpers, debug_call
from .detection_rule import DetectionRule

LOG = logging.getLogger('psengine.detection.helpers')


@debug_call
@validate_call
def save_rule(rule: DetectionRule, output_directory: Union[str, Path] = None):
    """Write detection rule content to file. If more than one detection rule is attached to rule,
    all will be saved.

    Args:
        rule (DetectionRule): single detection to write.
        output_directory (Union[str, Path]): a path to write to. If not provided, it will be the
        current working directory.

    Raises:
       WriteFileError: if the path provided is not a directory or it cannot be created.
       WriteFileError: if the write operations fail.

    """
    if not rule.rules:
        LOG.info(f'No rules to write for {rule.id_}')
        return

    output_directory = Path(output_directory).absolute() if output_directory else Path().cwd()
    OSHelpers.mkdir(output_directory)

    for data in rule.rules:
        try:
            full_path = output_directory / data.file_name
            full_path.write_text(data.content)
            LOG.info(f'Wrote: {full_path}')
        except (FileNotFoundError, IsADirectoryError, PermissionError, OSError) as err:  # noqa: PERF203
            raise WriteFileError(f"Could not write file '{data.file_name}': {err}") from err

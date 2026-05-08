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
from typing import Annotated, Optional, Union

from pydantic import validate_call
from typing_extensions import Doc

from ..errors import WriteFileError
from ..helpers import OSHelpers, debug_call
from .detection_rule import DetectionRule

LOG = logging.getLogger('psengine.detection.helpers')


@debug_call
@validate_call
def save_rule(
    rule: Annotated[DetectionRule, Doc('Single detection rule to write.')],
    output_directory: Annotated[
        Optional[Union[str, Path]],
        Doc('Path to write to. If not provided, the current working directory will be used.'),
    ] = None,
):
    """Write detection rule content to file.

    If more than one detection rule is attached to the rule, all will be saved.

    Raises:
        WriteFileError: In one of those cases:

            - If the path provided is not a directory.
            - If the path cannot be created.
            - If the write operations fail.
    """
    if not rule.rules:
        LOG.info(f'No rules to write for {rule.id_}')
        return

    output_directory = Path(output_directory).absolute() if output_directory else Path().cwd()
    OSHelpers.mkdir(output_directory)

    for i, data in enumerate(rule.rules):
        try:
            full_path = output_directory / (data.file_name or f'{rule.id_.replace(":", "_")}_{i}')
            full_path.write_text(data.content)
            LOG.info(f'Wrote: {full_path}')
        except (FileNotFoundError, IsADirectoryError, PermissionError, OSError) as err:  # noqa: PERF203
            raise WriteFileError(f"Could not write file '{data.file_name}': {err}") from err

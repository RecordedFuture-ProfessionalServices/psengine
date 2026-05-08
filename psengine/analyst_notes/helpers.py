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

import json
import logging
from pathlib import Path
from typing import Annotated, Union

from pydantic import validate_call
from typing_extensions import Doc

from ..errors import WriteFileError
from ..helpers import OSHelpers, debug_call
from .note import AnalystNote

LOG = logging.getLogger('psengine.analyst_notes.helpers')


@debug_call
@validate_call
def save_attachment(
    note_id: Annotated[str, Doc('The ID of the AnalystNote.')],
    data: Annotated[Union[bytes, str], Doc('The data returned from `fetch_attachment`.')],
    ext: Annotated[str, Doc('The extension of the attachment, returned by `fetch_attachment`.')],
    output_directory: Annotated[Union[str, Path], Doc('The directory to save the file into.')],
) -> None:
    """Save a YARA, Sigma, Snort, or PDF attachment to a file.

    The file will use the provided extension and the `note_id` to create the filename.
    """
    output_directory = (
        output_directory if isinstance(output_directory, str) else output_directory.as_posix()
    )
    _save_attachment(note_id, data, ext, output_directory)


@debug_call
@validate_call
def save_note(
    note: Annotated[AnalystNote, Doc('The note to save.')],
    output_directory: Annotated[Union[str, Path], Doc('The directory to save the file into.')],
) -> None:
    """Save an `AnalystNote` object to a file named with the note ID."""
    output_directory = (
        output_directory if isinstance(output_directory, str) else output_directory.as_posix()
    )
    _save_attachment(
        note_id=note.id_,
        data=json.dumps(note.json(), indent=4),
        ext='json',
        output_directory=output_directory,
    )


def _save_attachment(
    note_id: str, data: Union[bytes, str], ext: str, output_directory: str
) -> None:
    """Save attachment from bytes or note itself from json.

    Raises:
        WriteFileError: if saving to file fails
    """
    try:
        note_id = note_id.removeprefix('doc:')
        LOG.debug(f"Saving file related to '{note_id}' to disk")

        dir_path = OSHelpers.mkdir(output_directory)
        note_path = Path(dir_path) / f'{note_id}.{ext}'
        note_path.write_bytes(data) if isinstance(data, bytes) else note_path.write_text(data)
    except (FileNotFoundError, IsADirectoryError, PermissionError, OSError) as err:
        raise WriteFileError(f'Failed to save file to disk. Cause: {err.args}') from err

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
from ..helpers import OSHelpers
from .classic_alert import ClassicAlert
from .constants import DEFAULT_CA_OUTPUT_DIR

LOG = logging.getLogger('psengine.classic_alerts.helpers')


@validate_call
def save_image(
    image_bytes: bytes, file_name: str, output_directory: Union[str, Path] = DEFAULT_CA_OUTPUT_DIR
) -> Path:
    """Save an image to disk as a png file.

    Args:
        image_bytes (bytes): The image to save.
        output_directory (str): The directory to save the image to.
        file_name (Union[str, Path]): The file to save the image as. Without a file extension.

    Raises:
        ValidationError if any supplied parameter is of incorrect type.
        WriteFileError: if the write operation fails.
        WriteFileError: if the path provided is not a directory or it cannot be created.
        WriteFileError: if the write operations fail.

    Returns:
        Path: The path to the file written
    """
    try:
        LOG.info(f"Saving image '{file_name}' to disk")
        dir_path = OSHelpers.mkdir(output_directory)
        image_filepath = Path(dir_path) / f'{file_name}.png'
        with Path.open(image_filepath, 'wb') as file:
            file.write(image_bytes)
    except OSError as err:
        raise WriteFileError(
            f'Failed to save classic alert image to disk. Cause: {err.args}',
        ) from err

    return image_filepath


@validate_call
def save_images(
    alert: ClassicAlert, output_directory: Union[str, Path] = DEFAULT_CA_OUTPUT_DIR
) -> dict:
    """Save all images from a ``ClassicAlert`` to disk.

    Args:
        alert (ClassicAlert): The alert to save images from.
        output_directory (Union[str, Path], optional): The directory to save the image to.

    Raises:
        ValidationError if any supplied parameter is of incorrect type.
        WriteFileError: if the write operation fails.
        WriteFileError: if the path provided is not a directory or it cannot be created.
        WriteFileError: if the write operations fail.

    Returns:
        dict: A dictionary of image file paths with the image ID as the key.
    """
    image_file_paths = {}
    for id_, bytes_ in alert.images.items():
        image_file_paths[id_] = save_image(
            image_bytes=bytes_, output_directory=output_directory, file_name=id_
        )

    return image_file_paths

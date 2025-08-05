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
from typing import Annotated, Union

from pydantic import validate_call
from typing_extensions import Doc

from ..errors import WriteFileError
from ..helpers import OSHelpers
from .classic_alert import ClassicAlert
from .constants import DEFAULT_CA_OUTPUT_DIR

LOG = logging.getLogger('psengine.classic_alerts.helpers')


@validate_call
def save_image(
    image_bytes: Annotated[bytes, Doc('The image to save.')],
    file_name: Annotated[str, Doc('The file name to save the image as, without extension.')],
    output_directory: Annotated[
        Union[str, Path], Doc('The directory to save the image to.')
    ] = DEFAULT_CA_OUTPUT_DIR,
) -> Annotated[Path, Doc('The path to the file written.')]:
    """Save an image to disk as a PNG file.

    Raises:
        ValidationError: If any supplied parameter is of incorrect type.
        WriteFileError: In any of the following situations:

            - If the path provided is not a directory
            - If the path provided cannot be created.
            - If the write operation fails.
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
    alert: Annotated[ClassicAlert, Doc('The alert to save images from.')],
    output_directory: Annotated[
        Union[str, Path], Doc('The directory to save the images to.')
    ] = DEFAULT_CA_OUTPUT_DIR,
) -> Annotated[dict, Doc('A dictionary of image file paths with the image ID as the key.')]:
    """Save all images from a `ClassicAlert` to disk.

    Raises:
        ValidationError: If any supplied parameter is of incorrect type.
        WriteFileError: In any of the following situations:

            - If the path provided is not a directory
            - If the path provided cannot be created.
            - If the write operation fails.
    """
    image_file_paths = {}
    for id_, bytes_ in alert.images.items():
        image_file_paths[id_] = save_image(
            image_bytes=bytes_, output_directory=output_directory, file_name=id_
        )

    return image_file_paths

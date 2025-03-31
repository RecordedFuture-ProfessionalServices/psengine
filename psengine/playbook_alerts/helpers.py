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

from ..errors import WriteFileError
from ..helpers import OSHelpers, debug_call
from .constants import DEFAULT_PBA_OUTPUT_DIR
from .playbook_alerts import PBA_DomainAbuse

LOG = logging.getLogger('psengine.playbook_alerts.helpers')


@debug_call
def save_pba_images(
    playbook_alerts: Union[PBA_DomainAbuse, list[PBA_DomainAbuse]],
    output_directory: str = DEFAULT_PBA_OUTPUT_DIR,
) -> None:
    """Save Domain Abuse images/screenshots to disk as a .png file.

    Args:
        playbook_alerts (Union[PBA_DomainAbuse, List[PBA_DomainAbuse]]): Domain Abuse alert(s)
        output_directory (str): The directory to save the images to

    Raises:
        TypeError: If alerts are not PBA_DomainAbuse objects
        WriteFileError: If the image save fails with an OSError
    """
    if not isinstance(playbook_alerts, (list, PBA_DomainAbuse)):
        raise TypeError('Image saving is only supported by Domain Abuse alerts')

    playbook_alerts = playbook_alerts if isinstance(playbook_alerts, list) else [playbook_alerts]
    if not all(isinstance(alert, PBA_DomainAbuse) for alert in playbook_alerts):
        raise TypeError('Image saving is only supported by Domain Abuse alerts')

    for alert in playbook_alerts:
        LOG.info(f'Saving {len(alert.images)} image(s) to disk for alert {alert.playbook_alert_id}')
        for image_id, meta in alert.images.items():
            file_name = f'{alert.playbook_alert_id[5:]}_{image_id[4:]}'
            _save_image(
                file_name=file_name,
                image_bytes=meta['image_bytes'],
                output_directory=output_directory,
            )


def _save_image(
    file_name: str, image_bytes: bytes, output_directory: Union[str, Path] = DEFAULT_PBA_OUTPUT_DIR
) -> None:
    """Save image to disk as a .png file.

    Args:
        file_name (str): File name without the extension
        image_bytes (bytes): Image bytes
        output_directory (str or Path): The directory to save the image to

    Raises:
        WriteFileError: If the image save fails with an OSError
    """
    try:
        LOG.debug(f"Saving image '{file_name}' to disk")
        dir_path = OSHelpers.mkdir(output_directory)
        image_filepath = dir_path / f'{file_name}.png'
        with image_filepath.open('wb') as file:
            file.write(image_bytes)
    except OSError as err:
        raise WriteFileError(
            f'Failed to save playbook alert image to disk. Cause: {err.args}',
        ) from err

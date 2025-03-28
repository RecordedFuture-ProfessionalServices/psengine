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

LOGGER_NAME = 'psengine'

DEFAULT_PSENGINE_OUTPUT = Path('logs') / 'psengine_recfut.log'
DEFAULT_ROOT_OUTPUT = Path('logs') / 'root_recfut.log'

MAX_BYTES = 20480 * 1024
BACKUP_COUNT = 5
LOGGER_LEVEL = ['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
LOGGER_LEVEL_INT = [
    logging.NOTSET,
    logging.DEBUG,
    logging.INFO,
    logging.WARNING,
    logging.ERROR,
    logging.CRITICAL,
]
FILE_FORMAT = (
    '%(asctime)s,%(msecs)03d [%(threadName)s] %(levelname)s [%(module)s] '
    '%(funcName)s:%(lineno)d - %(message)s'
)

CONSOLE_FORMAT = '%(asctime)s,%(msecs)03d %(levelname)s [%(module)s] - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

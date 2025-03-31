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

import sys

#####################
# Multithreading Defaults
#####################
DEFAULT_LIMIT = 10
DEFAULT_MAX_WORKERS = 10

#####################
# Recorded Future API
#####################
RF_TOKEN_ENV_VAR = 'RF_TOKEN'
RF_TOKEN_VALIDATION_REGEX = r'^[a-f0-9]{32}$'

#####################
# Recorded Future Portal
#####################
RF_PORTAL_BASE_URL = 'https://app.recordedfuture.com'

# 0: entity type, 1: entity name
INDICATOR_INTEL_CARD_URL = RF_PORTAL_BASE_URL + '/live/sc/entity/{}:{}'

#####################
# HTTP Client Defaults
#####################
# In seconds
REQUEST_TIMEOUT = 120
POOL_MAX_SIZE = 120

# Request RETRY configuration
RETRY_TOTAL = 5
BACKOFF_FACTOR = 1
STATUS_FORCELIST = [502, 503, 504]

SSL_VERIFY = True

#####################
# Misc
#####################
# Output
ROOT_DIR = sys.path[0]

# String for timestamp conversion
TIMESTAMP_STR = '%Y-%m-%d %H:%M:%S'

# Markdown truncation string
TRUNCATE_COMMENT = (
    '\n\nThis {type_} has been truncated due to a character limit imposed by this tool. '
    'View the full {type_} at {url}'
)

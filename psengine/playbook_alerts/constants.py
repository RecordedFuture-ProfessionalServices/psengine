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
from typing import Union

from .playbook_alerts import (
    PBA_CodeRepoLeakage,
    PBA_CyberVulnerability,
    PBA_DomainAbuse,
    PBA_Generic,
    PBA_IdentityNovelExposure,
    PBA_ThirdPartyRisk,
)

STATUS_PANEL_NAME = 'status'
DEFAULT_PBA_OUTPUT_DIR = 'playbook_alerts'
DEFAULT_PBA_FILE_NAME = 'playbook_alerts_{}.json'

PLAYBOOK_ALERT_TYPE = Union[
    PBA_Generic,
    PBA_CodeRepoLeakage,
    PBA_CyberVulnerability,
    PBA_DomainAbuse,
    PBA_IdentityNovelExposure,
    PBA_ThirdPartyRisk,
]

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
from pathlib import Path
from typing import Literal, Union

from ..constants import ROOT_DIR
from ..playbook_alerts.pa_category import PACategory
from .playbook_alerts import (
    PBA_CodeRepoLeakage,
    PBA_CyberVulnerability,
    PBA_DomainAbuse,
    PBA_GeopoliticsFacility,
    PBA_IdentityNovelExposure,
    PBA_MalwareReport,
    PBA_ThirdPartyRisk,
)

STATUS_PANEL_NAME = 'status'

DEFAULT_ALERTS_OUTPUT_DIR = Path(ROOT_DIR) / 'playbook_alerts'
PLAYBOOK_ALERTS_OUTPUT_FNAME = 'rf_playbook_alerts_'


PLAYBOOK_ALERT_TYPE = Union[
    PBA_CodeRepoLeakage,
    PBA_CyberVulnerability,
    PBA_DomainAbuse,
    PBA_IdentityNovelExposure,
    PBA_ThirdPartyRisk,
    PBA_GeopoliticsFacility,
    PBA_MalwareReport,
]
PLAYBOOK_ALERT_INST = (
    PBA_CodeRepoLeakage,
    PBA_CyberVulnerability,
    PBA_DomainAbuse,
    PBA_IdentityNovelExposure,
    PBA_ThirdPartyRisk,
    PBA_GeopoliticsFacility,
    PBA_MalwareReport,
)


PBA_WITH_IMAGES_TYPE = Union[PBA_DomainAbuse, PBA_GeopoliticsFacility]
PBA_WITH_IMAGES_VALIDATOR = Union[
    Literal[PACategory.DOMAIN_ABUSE.value], Literal[PACategory.GEOPOLITICS_FACILITY.value]
]
PBA_WITH_IMAGES_INST = (PBA_DomainAbuse, PBA_GeopoliticsFacility)

ALERTS_PER_PAGE = 50

BULK_LOOKUP_BATCH_SIZE = 200

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

from ..endpoints import (
    EP_PLAYBOOK_ALERT_CODE_REPO_LEAKAGE,
    EP_PLAYBOOK_ALERT_CYBER_VULNERABILITY,
    EP_PLAYBOOK_ALERT_DOMAIN_ABUSE,
    EP_PLAYBOOK_ALERT_IDENTITY_NOVEL_EXPOSURES,
    EP_PLAYBOOK_ALERT_THIRD_PARTY_RISK,
)
from .pa_category import PACategory
from .playbook_alerts import (
    PBA_CodeRepoLeakage,
    PBA_CyberVulnerability,
    PBA_DomainAbuse,
    PBA_IdentityNovelExposure,
    PBA_ThirdPartyRisk,
)

CATEGORY_ENDPOINTS = {
    PACategory.CODE_REPO_LEAKAGE.value: EP_PLAYBOOK_ALERT_CODE_REPO_LEAKAGE,
    PACategory.CYBER_VULNERABILITY.value: EP_PLAYBOOK_ALERT_CYBER_VULNERABILITY,
    PACategory.DOMAIN_ABUSE.value: EP_PLAYBOOK_ALERT_DOMAIN_ABUSE,
    PACategory.IDENTITY_NOVEL_EXPOSURES.value: EP_PLAYBOOK_ALERT_IDENTITY_NOVEL_EXPOSURES,
    PACategory.THIRD_PARTY_RISK.value: EP_PLAYBOOK_ALERT_THIRD_PARTY_RISK,
}

CATEGORY_TO_OBJECT_MAP = {
    PACategory.CODE_REPO_LEAKAGE.value: PBA_CodeRepoLeakage,
    PACategory.CYBER_VULNERABILITY.value: PBA_CyberVulnerability,
    PACategory.DOMAIN_ABUSE.value: PBA_DomainAbuse,
    PACategory.IDENTITY_NOVEL_EXPOSURES.value: PBA_IdentityNovelExposure,
    PACategory.THIRD_PARTY_RISK.value: PBA_ThirdPartyRisk,
}

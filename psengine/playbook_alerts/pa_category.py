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

from enum import Enum


class PACategory(Enum):
    """Playbook Alert categories as Enum."""

    def __str__(self):
        """String representation of the enum value."""
        return str(self.value)

    def lower(self):
        """Return the lower case version of the enum value.

        Returns:
            str: lower case version of the enum value
        """
        return self.value.lower()

    DOMAIN_ABUSE = 'domain_abuse'
    CYBER_VULNERABILITY = 'cyber_vulnerability'
    THIRD_PARTY_RISK = 'third_party_risk'
    CODE_REPO_LEAKAGE = 'code_repo_leakage'
    IDENTITY_NOVEL_EXPOSURES = 'identity_novel_exposures'
    UNMAPPED_ALERT = 'unmapped_alert'

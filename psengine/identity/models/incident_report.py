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

from typing import Optional

from pydantic.networks import IPvAnyAddress

from ...common_models import RFBaseModel
from .common_models import Compromise


class IncidentReportCredentials(RFBaseModel):
    authorization_domain: str
    email_or_login: str
    password: str
    password_sha1: str
    domain_category: Optional[str] = None
    domain_technology: Optional[str] = None
    contains_high_risk_technologies: bool
    contains_cookies: bool
    contains_active_cookies: bool


class IncidentReportDetails(Compromise):
    malware_family: str
    ip_address: Optional[IPvAnyAddress] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

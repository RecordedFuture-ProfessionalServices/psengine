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

from typing import Literal

from ..enrich import (
    EnrichedCompany,
    EnrichedDomain,
    EnrichedHash,
    EnrichedIP,
    EnrichedMalware,
    EnrichedURL,
    EnrichedVulnerability,
)

SOAR_POST_ROWS = 2000

ALLOWED_ENTITIES = Literal[
    'company',
    'company_by_domain',
    'company/by_domain',
    'domain',
    'hash',
    'ip',
    'malware',
    'url',
    'vulnerability',
    'Company',
    'Organization',
    'InternetDomainName',
    'Hash',
    'IpAddress',
    'Malware',
    'URL',
    'CyberVulnerability',
]

ENTITY_FIELDS = ['entity', 'risk', 'timestamps']
MALWARE_FIELDS = ['entity', 'timestamps']
TYPE_MAPPING = {
    'company/by_domain': 'company_by_domain',
    'Organization': 'company',
    'Company': 'company',
    'IpAddress': 'ip',
    'InternetDomainName': 'domain',
    'CyberVulnerability': 'vulnerability',
    'URL': 'url',
    'Malware': 'malware',
    'Hash': 'hash',
}


IOC_TO_MODEL = {
    'ip': EnrichedIP,
    'domain': EnrichedDomain,
    'hash': EnrichedHash,
    'url': EnrichedURL,
    'malware': EnrichedMalware,
    'vulnerability': EnrichedVulnerability,
    'company': EnrichedCompany,
    'company/by_domain': EnrichedCompany,
}
MESSAGE_404 = '404 received. Nothing known on this entity'

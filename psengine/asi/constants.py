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

DEFAULT_ASI_PAGE_SIZE = 50
MAX_ASI_PAGE_SIZE = 1000
ASSETS_PER_PAGE = 10


### Fields for Asset Search filters
AssetType = Literal['ip', 'domain', 'host']


EnrichmentType = Literal[
    'custom_tags',
    'dns_records',
    'whois',
    'ip_metadata',
    'open_tcp_ports',
    'open_udp_ports',
    'web_technologies',
    'certificates',
    'certificate_chain',
    'defenses',
    'exposures',
    'exposure_instance_details',
]

SortByType = Literal[
    'discovered_at',
    'added_to_project_at',
    'last_scanned_at',
    'exposure_score',
    'asset_id',
    'apex_domain',
]

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

REQUIRED_CA_FIELDS = ['id', 'log', 'title', 'rule']

ALL_CA_FIELDS = [
    'ai_insights',
    'enriched_entities',
    'hits',
    'owner_organisation_details',
    'review',
    'triggered_by',
    'type',
    'url',
] + REQUIRED_CA_FIELDS


DEFAULT_CA_OUTPUT_DIR = 'alerts'
ALERTS_PER_PAGE = 50

MARKDOWN_ENTITY_TYPES_TO_DEFANG = ['InternetDomainName', 'URL', 'IpAddress']

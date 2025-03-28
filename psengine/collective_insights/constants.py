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

ENTITY_IP = 'ip'
ENTITY_DOMAIN = 'domain'
ENTITY_HASH = 'hash'
ENTITY_URL = 'url'
ENTITY_VULNERABILITY = 'vulnerability'
VALID_ENTITY_TYPES = [ENTITY_IP, ENTITY_DOMAIN, ENTITY_HASH, ENTITY_URL, ENTITY_VULNERABILITY]

TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

DETECTION_TYPE_CORRELATION = 'correlation'
DETECTION_TYPE_PLAYBOOK = 'playbook'
DETECTION_TYPE_RULE = 'detection_rule'
VALID_DETECTION_TYPES = [DETECTION_TYPE_CORRELATION, DETECTION_TYPE_PLAYBOOK, DETECTION_TYPE_RULE]

DETECTION_SUB_TYPE_SIGMA = 'sigma'
DETECTION_SUB_TYPE_YARA = 'yara'
DETECTION_SUB_TYPE_SNORT = 'snort'
VALID_DETECTION_RULE_SUB_TYPES = ['sigma', 'yara', 'snort']
DETECTION_SUB_FORMAT_MAPPING = {
    'ioc_type': ['ioc', 'type'],
    'ioc_value': ['ioc', 'value'],
    'ioc_field': ['ioc', 'field'],
    'ioc_source_type': ['ioc', 'source_type'],
    'incident_id': ['incident', 'id'],
    'incident_name': ['incident', 'name'],
    'incident_type': ['incident', 'type'],
    'detection_id': ['detection', 'id'],
    'detection_name': ['detection', 'name'],
    'detection_type': ['detection', 'type'],
}
SUMMARY_DEFAULT = True

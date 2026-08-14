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

IS_READY_INCREMENT = 5

ADD_OP = 'add'
REMOVE_OP = 'remove'
UNCHANGED_NAME = 'unchanged'
ERROR_NAME = 'error'


class ListTagName(str, Enum):
    """The 57 predefined tag values accepted by `list/{id}/entity/tags`.

    Provided for discoverability only - `update_entity_tags` accepts plain strings too,
    and the API is the authority on which values are valid. `name` values here are the
    API values (`tier1`), not display names (`Tier 1`).

    See https://docs.recordedfuture.com/reference/lists-available-tags.
    """

    THIRD_PARTY = '3rd_party'
    FOURTH_PARTY = '4th_party'
    AVAILABILITY = 'availability'
    BUSINESS_CONTINUITY = 'business_continuity'
    C_SUITE = 'c_suite'
    CEO = 'ceo'
    CFO = 'cfo'
    CLOUD = 'cloud'
    CONFIDENTIAL_DATA = 'confidential_data'
    CONFIDENTIALITY = 'confidentiality'
    CONFIRMED = 'confirmed'
    COO = 'coo'
    CRITICAL = 'critical'
    CRITICAL_INFRASTRUCTURE = 'critical_infrastructure'
    CUSTOMER_DATA = 'customer_data'
    CYBER_VENDOR = 'cyber_vendor'
    DEVELOPMENT = 'development'
    DMZ = 'dmz'
    DORA = 'dora'
    ECOMMERCE = 'ecommerce'
    EOL = 'eol'
    EOS = 'eos'
    FALSE_NEGATIVE = 'false_negative'
    FALSE_POSITIVE = 'false_positive'
    FINANCIAL = 'financial'
    FINISHED_GOODS = 'finished_goods'
    GDPR = 'gdpr'
    HIGH = 'high'
    HIPAA = 'hipaa'
    INFORMATION_AND_COMMUNICATION_TECHNOLOGY = 'information_and_communication_technology'
    INTEGRITY = 'integrity'
    INTERNAL = 'internal'
    INTERNET_FACING = 'internet_facing'
    ISO_27001 = 'iso_27001'
    LOW = 'low'
    M_AND_A = 'm_and_a'
    MEDIUM = 'medium'
    MONITORING = 'monitoring'
    MOST_CRITICAL_SUPPLIER = 'most_critical_supplier'
    NETWORK_CONNECTIVITY = 'network_connectivity'
    NO_PATCH_AVAILABLE = 'no_patch_available'
    PCI_DSS = 'pci_dss'
    PII = 'pii'
    POTENTIAL = 'potential'
    PRODUCTION = 'production'
    PROTECTED_HEALTH_INFORMATION = 'protected_health_information'
    RAW_MATERIALS = 'raw_materials'
    SOX = 'sox'
    SUBSIDIARY = 'subsidiary'
    TEMP_INCIDENT = 'temp_incident'
    TIER0 = 'tier0'
    TIER1 = 'tier1'
    TIER2 = 'tier2'
    TIER3 = 'tier3'
    TRUE_NEGATIVE = 'true_negative'
    TRUE_POSITIVE = 'true_positive'
    UNPATCHED = 'unpatched'

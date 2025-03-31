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
import stix2

ENTITY_TYPE_MAP = {
    'ip': 'IpAddress',
    'domain': 'InternetDomainName',
    'url': 'URL',
    'hash': 'FileHash',
}

INDICATOR_TYPE_TO_RF_PORTAL_MAP = {
    'IpAddress': 'ip',
    'InternetDomainName': 'idn',
    'URL': 'url',
    'FileHash': 'hash',
}

IDENTITY_TYPE_TO_CLASS = {
    'Company': 'organization',
    'Organization': 'organization',
    'Person': 'individual',
}

CONVERT_ENTITY_KWARGS = 'description'
SUPPORTED_HUNTING_RULES = ('yara', 'snort', 'sigma')

# maps Insikt Report types to STIX2 report types
REPORT_TYPE_MAPPER = {
    'Actor Profile': 'Threat-Actor',
    'Analyst On-Demand Report': 'Threat-Report',
    'Cyber Threat Analysis': 'Threat-Report',
    'Flash Report': 'Threat-Report',
    'Geopolitical Flash Event': 'Threat-Report',
    'Geopolitical Intelligence Summary': 'Threat-Report',
    'Geopolitical Profile': 'Threat-Actor',
    'Geopolitical Threat Forecast': 'Threat-Actor',
    'Geopolitical Validated Event': 'Observed-Data',
    'Hunting Package': 'Attack-Pattern',
    'Indicator': 'Indicator',
    'Informational': 'Threat-Report',
    'Insikt Research Lead': 'Intrusion-Set',
    'Malware/Tool Profile': 'Malware',
    'Regular Vendor Vulnerability Disclosures': 'Vulnerability',
    'Sigma Rule': 'Attack-Pattern',
    'SNORT Rule': 'Indicator',
    'Source Profile': 'Observed-Data',
    'The Record by Recorded Future': 'Threat-Report',
    'Threat Lead': 'Threat-Actor',
    'TTP Instance': 'Attack-Pattern',
    'Validated Intelligence Event': 'Observed-Data',
    'Weekly Threat Landscape': 'Threat-Report',
    'YARA Rule': 'Indicator',
}

TLP_MAP = {
    'white': stix2.TLP_WHITE,
    'green': stix2.TLP_GREEN,
    'amber': stix2.TLP_AMBER,
    'red': stix2.TLP_RED,
}

RF_IDENTITY_UUID = 'identity--509cdfd1-b97f-5329-9e27-a841f8b2dbce'
RF_NAMESPACE = '7fb92aa3-456a-406a-ad7e-1400307c46b1'
INDICATOR_TYPES = ['IpAddress', 'InternetDomainName', 'URL', 'FileHash']
CONVERTED_TYPES = {
    'ip': 'IpAddress',
    'domain': 'InternetDomainName',
    'url': 'URL',
    'hash': 'FileHash',
}

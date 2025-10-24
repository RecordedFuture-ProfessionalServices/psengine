from pathlib import Path

MOCK_DIR = Path(__file__).parent / 'mocks'
FIELDS_ALL_COMMON = [
    'aiInsights',
    'analystNotes',
    'counts',
    'entity',
    'intelCard',
    'metrics',
    'relatedEntities',
    'sightings',
    'timestamps',
]
FIELDS_ALL_IP = FIELDS_ALL_COMMON + [
    'risk',
    'links',
    'enterpriseLists',
    'threatLists',
    'riskMapping',
    'dnsPortCert',
    'location',
    'riskyCIDRs',
]
FIELDS_ALL_DOMAIN = FIELDS_ALL_COMMON + [
    'risk',
    'links',
    'enterpriseLists',
    'threatLists',
    'riskMapping',
]
FIELDS_ALL_HASH = FIELDS_ALL_COMMON + [
    'risk',
    'links',
    'enterpriseLists',
    'threatLists',
    'riskMapping',
    'fileHashes',
    'hashAlgorithm',
]
FIELDS_ALL_URL = FIELDS_ALL_COMMON + ['risk', 'links', 'enterpriseLists', 'riskMapping']
FIELDS_ALL_VULNERABILITY = FIELDS_ALL_COMMON + [
    'risk',
    'links',
    'enterpriseLists',
    'threatLists',
    'riskMapping',
    'lifecycleStage',
    'linkedMalware',
    'cpe',
    'cpe22uri',
    'cvss',
    'cvssRatings',
    'cvssv3',
    'cvssv4',
    'nvdDescription',
    'nvdReferences',
    'rawRisk',
    'commonNames',
    'relatedLinks',
]
FIELDS_ALL_COMPANY = FIELDS_ALL_COMMON + ['risk', 'threatLists', 'riskMapping', 'curated']
FIELDS_ALL_MALWARE = FIELDS_ALL_COMMON + ['links', 'categories']

SINGLE_IP = '139.155.90.81'
IPS = [
    '108.137.174.209',
    '147.102.210.202',
    '152.65.223.64',
]
DOMS = [
    'qassar22.ddns.net',
    'marcelotatuape.ddns.net',
    'silentlegion.duckdns.org',
]
HASHS = [
    '3b175aa41333d86f3a5e63c9f9696452c0d51c212d07ebbb6e1bcee64da78df8',
    '4e51a45c3985349f93296e99d5f1a3d8e6dd499d0e8452e41bb1c502445d5538',
    '0f6b6c1596e38e840fb03420317db224739a18dbef0b98285637f5887e90a191',
]
VULNS = [
    'CVE-2022-1364',
    'CVE-2022-3656',
    'CVE-2023-34918',
]
URLS = [
    'https://pub-43afe9e8810c4c5e8ffcef393309937c.r2.dev/0.html',
    'https://linktoxic34.com/wp-content/themes/twentytwentytwo/dark.hta',
    'http://wfsdragon.ru/api/setStats.php',
]

MALWS = ['9AvGLt', 'Nz2mWw']
SINGLE_MALW = MALWS[0]

COMPS = ['COIhx', 'I-34Sj', 'CGHKG']
SINGLE_COMPANY = COMPS[0]
COMPANY_DOM = 'google.com'


IOCS = {
    'InternetDomainName': DOMS,
    'IpAddress': IPS,
    'URL': URLS,
    'CyberVulnerability': VULNS,
    'Hash': HASHS,
}

ALL = {
    'Company': COMPS,
    'CyberVulnerability': VULNS,
    'Hash': HASHS,
    'InternetDomainName': DOMS,
    'IpAddress': IPS,
    'Malware': MALWS,
    'URL': URLS,
}


IP_LOOKUP_MOCK = {
    'data': {
        'timestamps': {
            'lastSeen': '2022-10-20T00:15:34.244Z',
            'firstSeen': '2015-06-27T01:39:03.429Z',
        },
        'risk': {
            'criticalityLabel': 'Malicious',
            'riskString': '6/79',
            'rules': 6,
            'criticality': 3,
            'riskSummary': '6 of 79 Risk Rules currently observed.',
            'score': 80,
            'evidenceDetails': [
                {
                    'mitigationString': '',
                    'evidenceString': '200 sightings on 2 sources: Recorded Future Malware',
                    'rule': 'Historically Linked to Intrusion Method',
                    'criticality': 1,
                    'timestamp': '2020-07-04T00:05:00.000Z',
                    'criticalityLabel': 'Unusual',
                }
            ],
        },
        'entity': {'id': 'ip:218.54.31.165', 'name': '218.54.31.165', 'type': 'IpAddress'},
    }
}

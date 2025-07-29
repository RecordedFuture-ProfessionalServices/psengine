DETECTION_FILTERS = [
    (
        {
            'novel_only': True,
            'detection_type': 'External',
            'max_results': 10,
            'domains': 'norsegods.online',
        },
        10,
    ),
    (
        {
            'novel_only': True,
            'domains': ['norsegods.online'],
            'detection_type': 'External',
            'created_gte': '2024-03-02T15:42:07.195Z',
            'created_lt': '2025-05-02T15:42:07.195Z',
            'max_results': 1,
        },
        1,
    ),
    (
        {
            'novel_only': True,
            'domains': ['norsegods.online'],
            'detection_type': 'External',
            'created_lt': '2025-05-02T15:42:07.195Z',
            'max_results': 1,
        },
        1,
    ),
    (
        {
            'novel_only': True,
            'domains': ['norsegods.online'],
            'detection_type': 'External',
            'created_gte': '-3d',
            'created_lt': '2025-05-02T15:42:07.195Z',
            'max_results': 8,
        },
        8,
    ),
]

HOSTNAME_LOOKUP_FILTER = [
    (
        {
            'hostname': 'DESKTOP-UK91N65',
            'first_downloaded_gte': '2025-05-02T20:05:00.052Z',
            'properties': ['Letter'],
            'username_properties': ['Email'],
            'max_results': 1,
        },
        1,
    ),
    (
        {
            'hostname': 'DESKTOP-UK91N65',
            'first_downloaded_gte': '2025-05-08T20:05:00.052Z',
            'properties': ['Letter'],
            'username_properties': ['Email'],
            'max_results': 1,
        },
        0,
    ),
]


IP_LOOKUP_FILTER = [
    (
        {
            'ip': '152.59.220.149/8',
            'exfiltration_date_gte': '2012-05-08T13:03:16.570Z',
            'max_results': 200,
        },
        200,
    ),
    (
        {
            'ip': '152.59.220.149/8',
            'exfiltration_date_gte': '2012-05-08T13:03:16.570Z',
            'max_results': 200,
            'identities_per_page': 100,
        },
        200,
    ),
    (
        {
            'range_gte': '176.241.143.26',
            'range_lte': '176.241.143.29',
            'first_downloaded_gte': '2025-04-06T13:03:16.570Z',
            'max_results': 200,
            'identities_per_page': 100,
        },
        1,
    ),
]

CREDS_LOOKUP_FILTER_WITHOUT_RES = [
    {
        'subjects_sha1': ['7d7dd035e46e76477a05f192440b8bc2f9ca6fb8'],
        'breach_name': 'Stealer Malware Logs 2025-03-23',
        'breach_date': '2025-04-19T20:05:00.041Z',
    },
    {
        'subjects': ['jlarrestier@norsegods.online'],
        'breach_name': 'Stealer Malware Logs 2025-03-23',
    },
    {
        'subjects': ['jlarrestier@norsegods.online'],
        'dump_name': 'Stealer Malware Logs 2025-06-03',
        'dump_date': '2025-06-09T20:05:00.040Z',
    },
    {
        'subjects': ['jlarrestier@norsegods.online'],
        'dump_name': 'Stealer Malware Logs 2025-06-03',
    },
    {
        'subjects': ['alice@norsegods.online'],
        'subjects_login': [
            {
                'login': 'alice',
                'login_sha1': 'b89eaac7e61417341b710b727768294d0e6a277b',
                'domain': 'secure.domain',
            }
        ],
        'first_downloaded_gte': '2025-04-01T00:00:00Z',
        'latest_downloaded_gte': '2025-06-01T00:00:00Z',
        'exfiltration_date_gte': '2025-06-01T00:00:00Z',
        'properties': ['AtLeast8Characters'],
        'username_properties': ['Email'],
        'breach_name': 'BigBreach',
        'breach_date': '2025-02-01T00:00:00Z',
        'dump_name': 'LeakyBucket',
        'dump_date': '2025-01-15T00:00:00Z',
        'authorization_technologies': ['SSO'],
        'authorization_protocols': ['SAML'],
        'malware_families': ['TrickBot'],
    },
    {
        'subjects_sha1': ['6bf7fe8a6c94ef0d865875a6e42092bc20ba52e7'],
        'username_properties': ['Email'],
        'authorization_protocols': ['https'],
    },
]
CREDS_LOOKUP_FILTER_WITH_RES = [
    {
        'subjects': ['20170161@norsegods.online'],
        'first_downloaded_gte': '2025-01-01T00:00:00Z',
    },
    {
        'subjects_login': [
            {
                'login': 'usr01',
                'login_sha1': '41760fc9966ad2432a6984bb5133fcaeff1d33f1',
                'domain': 'norsegods.online',
            }
        ],
        'authorization_protocols': ['https'],
    },
    {
        'first_downloaded_gte': '2025-05-01T00:00:00Z',
        'latest_downloaded_gte': '2025-06-01T00:00:00Z',
        'malware_families': ['Vidar'],
        'subjects': ['amber.guiher@norsegods.online'],
    },
    {
        'subjects': ['jlarrestier@norsegods.online'],
        'properties': ['Letter', 'Number'],
        'username_properties': ['Email'],
    },
    {
        'subjects_login': [
            {
                'login': 'dlr30008419a04',
                'domain': 'norsegods.online',
            }
        ],
        'authorization_technologies': ['VPN'],
        'malware_families': ['RedlineVariant Stealer'],
    },
]

CREDS_SEARCH_FILTER = [
    (
        {
            'domains': ['norsegods.online'],
            'first_downloaded_gte': '2025-01-01T00:00:00Z',
        },
        10,
    ),
    (
        {
            'domains': 'norsegods.online',
            'max_results': 48,
        },
        48,
    ),
]

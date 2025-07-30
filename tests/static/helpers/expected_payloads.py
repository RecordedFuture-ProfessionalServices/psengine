expected_payloads = [
    {'risk': {'score': 24}},
    {
        'risk': {'score': 24},
        'timestamps': {
            'lastSeen': '2023-05-26T15:36:12.648Z',
            'firstSeen': '2009-01-15T21:00:08.000Z',
        },
    },
    {
        'timestamps': {
            'lastSeen': '2023-05-26T15:36:12.648Z',
            'firstSeen': '2009-01-15T21:00:08.000Z',
        },
        'risk': {'score': 24},
    },
    {},
    {},
    {
        'risk': {'score': 24, 'criticality': 1},
        'timestamps': {
            'lastSeen': '2023-05-26T15:36:12.648Z',
            'firstSeen': '2009-01-15T21:00:08.000Z',
        },
    },
    {
        'cpe': [
            'cpe:2.3:o:apple:mac_os_x:10.15:*:*:*:*:*:*:*',
            'cpe:2.3:o:apple:macos:11.0.1:*:*:*:*:*:*:*',
            'cpe:2.3:o:apple:mac_os_x:10.15.6:supplemental_update:*:*:*:*:*:*',
            'cpe:2.3:o:apple:macos:11.0:*:*:*:*:*:*:*',
            'cpe:2.3:o:apple:mac_os_x:10.15.3:*:*:*:*:*:*:*',
            'cpe:2.3:o:apple:mac_os_x:10.15.7:supplemental_update:*:*:*:*:*:*',
            'cpe:2.3:o:apple:macos:11.2.1:*:*:*:*:*:*:*',
            'cpe:2.3:o:apple:mac_os_x:10.15.4:*:*:*:*:*:*:*',
            'cpe:2.3:o:apple:mac_os_x:10.15.7:security_update_2020-001:*:*:*:*:*:*',
            'cpe:2.3:o:apple:mac_os_x:10.15.5:*:*:*:*:*:*:*',
            'cpe:2.3:o:apple:macos:11.1.0:*:*:*:*:*:*:*',
            'cpe:2.3:o:apple:macos:11.2:*:*:*:*:*:*:*',
            'cpe:2.3:o:apple:mac_os_x:10.15.7:security_update_2020:*:*:*:*:*:*',
            'cpe:2.3:o:apple:macos:11.1:*:*:*:*:*:*:*',
            'cpe:2.3:o:apple:mac_os_x:10.15.7:security_update_2020-007:*:*:*:*:*:*',
            'cpe:2.3:o:apple:mac_os_x:10.15.6:*:*:*:*:*:*:*',
            'cpe:2.3:o:apple:mac_os_x:10.15.1:*:*:*:*:*:*:*',
            'cpe:2.3:o:apple:mac_os_x:10.15.7:*:*:*:*:*:*:*',
            'cpe:2.3:a:apple:mac_os_x:10.15.2:*:*:*:*:*:*:*',
            'cpe:2.3:o:apple:mac_os_x:10.15.7:security_update_2020-005:*:*:*:*:*:*',
        ]
    },
    {
        'risk': {
            'score': 24,
            'criticalityLabel': 'Unusual',
            'evidenceDetails': [
                {
                    'rule': 'Historically Suspected Phishing Techniques',
                    'evidenceString': '6 sightings on 1 source: Anti-Phishing Working Group. https://facebook.com/profile.php?id=100089564287561 on facebook.com was reported as high confidence phishing impersonating IRS in a submission to the Anti-Phishing Working Group on May 11, 2023.',
                },
                {
                    'rule': 'Historically Reported as a Defanged DNS Name',
                    'evidenceString': '9 sightings on 3 sources: @silentpush_labs, @KeremiCacing, @drb_ra. Most recent tweet: #phishing meta-business-settings700122[.]web[.]app spoofing facebook[.]com; AS Name: FASTLY; Name server: *.googledomains.com; registrar: Markmonitor; Currently hosted on 199.36.158.100; Abuse report filed. https://t.co/qNTxOFWM97. Most recent link (Oct 12, 2022): https://twitter.com/silentpush_labs/statuses/1580256999165632512',
                },
                {
                    'rule': 'Historically Linked to Cyber Attack',
                    'evidenceString': '4 sightings on 2 sources: AbuseIP structurebase, @andpalmier. Most recent tweet: #phishing #facebook #paypal #bankofamerica #chase /35.188.36.185/facebook/27-03-2020/facebook.com/website reg: @google ☣️ 35.188.36.185 (AS15169) @n0p1shing @ActorExpose @Spam404 @malwrhunterteam @nullcookies https://t.co/PnhWddOTUB. Most recent link (Jul 20, 2020): https://twitter.com/andpalmier/statuses/1285290853884362753',
                },
                {
                    'rule': 'Historically Referenced by Insikt Group',
                    'evidenceString': '5 sightings on 1 source: Insikt Group. 5 reports including Killnet Post 10,000-Record structurebase Leak With Alleged PII of US FBI Agents. Most recent link (Dec 16, 2022): https://app.recordedfuture.com/portal/analyst-note/doc:pNuw1k',
                },
                {
                    'rule': 'Recently Referenced by Insikt Group',
                    'evidenceString': '1 sighting on 1 source: Insikt Group. 1 report: TAG-77 Trolling Operations in Support of Russia Continue to Target Western Officials, Executives, and Celebrities. Most recent link (May 03, 2023): https://app.recordedfuture.com/portal/analyst-note/doc:rFgomo. Mitigated by being in Host.io Top 500 Domains and IP Addresses (Allow List), Host.io Top 10k Domains and IP Addresses (Allow List).',
                },
                {
                    'rule': 'Trending in Recorded Future Analyst Community',
                    'evidenceString': '1 sighting on 1 source: Recorded Future Analyst Community Trending Indicators. Recently viewed by many analysts in many organizations in the Recorded Future community.',
                },
                {
                    'rule': 'Historically Reported in Threat List',
                    'evidenceString': 'Previous sightings on 2 sources: Recorded Future Analyst Community Trending Indicators, Recently Viewed Integrations Indicators. Observed between Apr 8, 2023, and Apr 10, 2023.',
                },
            ],
        }
    },
    {
        'risk': {
            'score': 24,
            'evidenceDetails': [
                {'criticality': 1, 'rule': 'Historically Suspected Phishing Techniques'},
                {'criticality': 1, 'rule': 'Historically Reported as a Defanged DNS Name'},
                {'criticality': 1, 'rule': 'Historically Linked to Cyber Attack'},
                {'criticality': 1, 'rule': 'Historically Referenced by Insikt Group'},
                {'rule': 'Recently Referenced by Insikt Group'},
                {'criticality': 1, 'rule': 'Trending in Recorded Future Analyst Community'},
                {'criticality': 1, 'rule': 'Historically Reported in Threat List'},
            ],
        }
    },
    {
        'risk': {
            'score': 24,
            'evidenceDetails': [
                {'criticality': 1},
                {'criticality': 1},
                {'criticality': 1},
                {'criticality': 1},
                {'criticality': 1},
                {'criticality': 1},
            ],
        }
    },
]

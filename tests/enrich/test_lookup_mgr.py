from urllib.parse import quote

import pytest
from constants import (
    ALL,
    COMPANY_DOM,
    DOMS,
    HASHS,
    IPS,
    MOCK_DIR,
    SINGLE_COMPANY,
    SINGLE_IP,
    SINGLE_MALW,
    URLS,
    VULNS,
)
from pydantic import ValidationError
from requests import HTTPError

from psengine.enrich import (
    EnrichedCompany,
    EnrichedDomain,
    EnrichedHash,
    EnrichedIP,
    EnrichedMalware,
    EnrichedURL,
    EnrichedVulnerability,
    EnrichmentData,
    EnrichmentLookupError,
    LookupMgr,
)
from psengine.enrich.constants import ENTITY_FIELDS, MALWARE_FIELDS


class Test_LookupMgr:
    params = [
        {'entity': None, 'entity_type': None},
        {
            'entity': 'google.com',
            'entity_type': None,
        },
        {'entity': None, 'entity_type': 'domain'},
        {
            'entity': 'google.com',
            'entity_type': 'a',
        },
    ]

    @pytest.mark.parametrize('params', params)
    def test_params_raises_ValidationError(self, lookup_mgr, params):
        with pytest.raises(ValidationError):
            lookup_mgr.lookup(**params)

    @pytest.mark.parametrize('type_', ['a', 'doms', 'ips', 1, 'whatever', 'moise'])
    def test_entity_type_raises_ValidationError(self, lookup_mgr, type_):
        with pytest.raises(ValidationError):
            lookup_mgr.lookup(entity='google.com', entity_type=type_)

    data = [
        ('ip:1.1.1.1', ENTITY_FIELDS, 'ip'),
        ('idn:google.com', ENTITY_FIELDS, 'domain'),
        ('url:http://images.google.com', ENTITY_FIELDS, 'url'),
        (
            'hash:1a9c27e5be8c58da1c02fc4245a07831d5d431cdd1a91cd35d2dd0ad62da71cd',
            ENTITY_FIELDS,
            'hash',
        ),
        ('KLjWwB', ENTITY_FIELDS, 'company'),
        ('nZWUH2', MALWARE_FIELDS, 'malware'),
        ('Gd91L', ENTITY_FIELDS, 'Organization'),
    ]

    @pytest.mark.parametrize(
        ('entity', 'expected', 'entity_type'), data, ids=list(range(len(data)))
    )
    def test_lookup_called_with_default_fields_while_overwritte(
        self,
        lookup_mgr: LookupMgr,
        mocker,
        entity,
        expected,
        entity_type,
        mock_request,
    ):
        mock = mock_request(MOCK_DIR / 'lookup_sample_ip.json')
        mocker.patch.object(lookup_mgr.rf_client, 'request', return_value=mock)
        spy = mocker.spy(lookup_mgr.rf_client, 'request')
        lookup_mgr.lookup(entity=entity, entity_type=entity_type)
        params = spy.call_args[1]['params']['fields']
        assert ','.join(sorted(expected)) == ','.join(sorted(params.split(',')))

    data = [
        ('1.1.1.1', 'ip/1.1.1.1', 'ip'),
        ('google.com', 'domain/google.com', 'domain'),
        ('CVE-2012-1535', 'vulnerability/CVE-2012-1535', 'vulnerability'),
    ]

    @pytest.mark.parametrize(
        ('entity', 'expected', 'expected_type'), data, ids=list(range(len(data)))
    )
    def test_lookup_called_with_name_get_right_type(
        self, lookup_mgr, mocker, entity, expected, expected_type, mock_request
    ):
        mock = mock_request(MOCK_DIR / 'lookup_sample_ip.json')
        mocker.patch.object(lookup_mgr.rf_client, 'request', return_value=mock)
        spy = mocker.spy(lookup_mgr.rf_client, 'request')
        lookup_mgr.lookup(entity=entity, entity_type=expected_type)
        assert spy.call_args[0][0] == 'get'
        assert expected in spy.call_args[0][1]

    def test_lookup_malware_by_name(self, lookup_mgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'lookup_sample_malware.json')
        mocker.patch.object(lookup_mgr.rf_client, 'request', return_value=mock)
        res = lookup_mgr.lookup(entity='Wintoken', entity_type='malware')
        assert isinstance(res, EnrichmentData)
        assert res.entity == 'Wintoken'
        assert res.entity_type == 'malware'
        assert res.is_enriched is True
        assert isinstance(res.content, EnrichedMalware)

    def test_lookup_with_correct_fields(self, lookup_mgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'lookup_sample_url.json')
        mocker.patch.object(lookup_mgr.rf_client, 'request', return_value=mock)
        entity = 'http://test.com/'

        res = lookup_mgr.lookup(entity=entity, entity_type='url', fields=['intelCard', 'metrics'])
        assert res.entity == entity
        assert res.entity_type == 'url'
        assert isinstance(res.content, EnrichedURL)
        assert res.content.intel_card.startswith('https://app.recordedfuture.com/')
        assert res.content.metrics
        assert res.content.risk.score

    def test_single_ip(self, lookup_mgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'lookup_sample_ip.json')
        mocker.patch.object(lookup_mgr.rf_client, 'request', return_value=mock)
        spy = mocker.spy(lookup_mgr.rf_client, 'request')
        result = lookup_mgr.lookup(entity=SINGLE_IP, entity_type='ip', fields=ENTITY_FIELDS)
        args1 = spy.call_args
        lookup_mgr.lookup(entity=SINGLE_IP, entity_type='ip')
        args2 = spy.call_args
        lookup_mgr.lookup(entity=SINGLE_IP, entity_type='IpAddress')
        args3 = spy.call_args

        assert args1 == args2 == args3
        assert isinstance(result.content, EnrichedIP)

    data = [
        (SINGLE_IP, 'ip', EnrichedIP, 'lookup_sample_ip.json'),
        (SINGLE_IP, 'IpAddress', EnrichedIP, 'lookup_sample_ip.json'),
        (f'ip:{SINGLE_IP}', 'IpAddress', EnrichedIP, 'lookup_sample_ip.json'),
        (SINGLE_COMPANY, 'company', EnrichedCompany, 'lookup_sample_company.json'),
        (COMPANY_DOM, 'company_by_domain', EnrichedCompany, 'lookup_sample_company.json'),
        (COMPANY_DOM, 'company/by_domain', EnrichedCompany, 'lookup_sample_company.json'),
        (DOMS[0], 'domain', EnrichedDomain, 'lookup_sample_domain.json'),
        (DOMS[0], 'InternetDomainName', EnrichedDomain, 'lookup_sample_domain.json'),
        (HASHS[0], 'hash', EnrichedHash, 'lookup_sample_hash.json'),
        (HASHS[0], 'Hash', EnrichedHash, 'lookup_sample_hash.json'),
        (SINGLE_MALW, 'malware', EnrichedMalware, 'lookup_sample_malware.json'),
        (SINGLE_MALW, 'Malware', EnrichedMalware, 'lookup_sample_malware.json'),
        (URLS[0], 'url', EnrichedURL, 'lookup_sample_url.json'),
        (URLS[0], 'URL', EnrichedURL, 'lookup_sample_url.json'),
        (SINGLE_COMPANY, 'Company', EnrichedCompany, 'lookup_sample_company.json'),
        (SINGLE_COMPANY, 'Organization', EnrichedCompany, 'lookup_sample_organization.json'),
        (VULNS[0], 'vulnerability', EnrichedVulnerability, 'lookup_sample_vuln.json'),
        (VULNS[0], 'CyberVulnerability', EnrichedVulnerability, 'lookup_sample_vuln.json'),
    ]

    @pytest.mark.parametrize(
        ('entity', 'e_type', 'expected', 'mock_file'), data, ids=list(range(len(data)))
    )
    def test_recorded_future_types(
        self, lookup_mgr, entity, e_type, expected, mock_file, mocker, mock_request
    ):
        mock = mock_request(MOCK_DIR / mock_file)
        mocker.patch.object(lookup_mgr.rf_client, 'request', return_value=mock)

        res = lookup_mgr.lookup(entity=entity, entity_type=e_type)
        assert isinstance(res.content, expected)
        assert isinstance(res, EnrichmentData)

    def test_multiple_ip(self, lookup_mgr, mocker, mock_request):
        mocks = [mock_request(MOCK_DIR / 'lookup_sample_ip.json')] * 6
        mocker.patch.object(lookup_mgr.rf_client, 'request', side_effect=mocks)
        spy = mocker.spy(lookup_mgr.rf_client, 'request')
        results1 = lookup_mgr.lookup_bulk(IPS, entity_type='ip', fields=ENTITY_FIELDS)
        args1 = spy.call_args
        lookup_mgr.lookup_bulk(IPS, entity_type='ip')
        args2 = spy.call_args

        assert all(isinstance(obj.content, EnrichedIP) for obj in results1)
        assert args1 == args2

    def test_comapny(self, lookup_mgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'lookup_sample_company.json')
        mocker.patch.object(lookup_mgr.rf_client, 'request', return_value=mock)
        spy = mocker.spy(lookup_mgr.rf_client, 'request')
        results1 = lookup_mgr.lookup(
            entity=SINGLE_COMPANY, entity_type='company', fields=ENTITY_FIELDS
        )
        args1 = spy.call_args
        lookup_mgr.lookup(entity=SINGLE_COMPANY, entity_type='company')
        args2 = spy.call_args
        lookup_mgr.lookup(entity=SINGLE_COMPANY, entity_type='Company')
        args3 = spy.call_args

        assert isinstance(results1.content, EnrichedCompany)
        assert args1 == args2 == args3

    def test_company_by_domain(self, lookup_mgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'lookup_sample_company.json')
        mocker.patch.object(lookup_mgr.rf_client, 'request', return_value=mock)
        spy = mocker.spy(lookup_mgr.rf_client, 'request')
        results1 = lookup_mgr.lookup(
            entity=COMPANY_DOM, entity_type='company_by_domain', fields=ENTITY_FIELDS
        )
        args1 = spy.call_args
        lookup_mgr.lookup(entity=COMPANY_DOM, entity_type='company_by_domain')
        args2 = spy.call_args
        lookup_mgr.lookup(entity=COMPANY_DOM, entity_type='company/by_domain')
        args3 = spy.call_args

        assert isinstance(results1.content, EnrichedCompany)
        assert args1 == args2 == args3

    def test_weird_urls(self, lookup_mgr, mocker, mock_request):
        url = 'http%3A%2F%2Flarsb.hopto.org%2Ffile_jose4j-0.9.6.jar.f57cb91efc5beaa940029f5515a888c2.685...'
        mock = mock_request(MOCK_DIR / 'lookup_sample_url.json')
        mocker.patch.object(lookup_mgr.rf_client, 'request', return_value=mock)
        spy = mocker.spy(lookup_mgr.rf_client, 'request')
        d = lookup_mgr.lookup(url, entity_type='url')
        assert spy.call_args[0][1] == f'https://api.recordedfuture.com/v2/url/{quote(url)}'
        assert isinstance(d, EnrichmentData)

    def test_malware(self, lookup_mgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'lookup_sample_malware.json')
        mocker.patch.object(lookup_mgr.rf_client, 'request', return_value=mock)
        spy = mocker.spy(lookup_mgr.rf_client, 'request')
        results1 = lookup_mgr.lookup(
            entity=SINGLE_MALW, entity_type='malware', fields=ENTITY_FIELDS
        )
        args1 = spy.call_args[0]
        lookup_mgr.lookup(entity=SINGLE_MALW, entity_type='malware')
        args2 = spy.call_args[0]

        assert isinstance(results1.content, EnrichedMalware)
        assert args1 == args2

    def test_all(self, lookup_mgr, mocker, mock_request):
        results1, results2 = [], []
        mocks = [
            *[
                *[mock_request(MOCK_DIR / 'lookup_sample_company.json')] * 3,
                *[mock_request(MOCK_DIR / 'lookup_sample_vuln.json')] * 3,
                *[mock_request(MOCK_DIR / 'lookup_sample_hash.json')] * 3,
                *[mock_request(MOCK_DIR / 'lookup_sample_domain.json')] * 3,
                *[mock_request(MOCK_DIR / 'lookup_sample_ip.json')] * 3,
                *[mock_request(MOCK_DIR / 'lookup_sample_malware.json')] * 3,
                *[mock_request(MOCK_DIR / 'lookup_sample_url.json')] * 3,
            ]
            * 2
        ]
        mocker.patch.object(lookup_mgr.rf_client, 'request', side_effect=mocks)
        spy = mocker.spy(lookup_mgr.rf_client, 'request')

        for e_types, e in ALL.items():
            results1.extend(lookup_mgr.lookup_bulk(e, e_types))
            args1 = spy.call_args[0]
            results2.extend(lookup_mgr.lookup_bulk(e, e_types, fields=ENTITY_FIELDS))
            args2 = spy.call_args[0]
            assert args1 == args2

        assert any(isinstance(obj.content, EnrichedIP) for obj in results1)
        assert any(isinstance(obj.content, EnrichedDomain) for obj in results1)
        assert any(isinstance(obj.content, EnrichedURL) for obj in results1)
        assert any(isinstance(obj.content, EnrichedHash) for obj in results1)
        assert any(isinstance(obj.content, EnrichedVulnerability) for obj in results1)
        assert any(isinstance(obj.content, EnrichedCompany) for obj in results1)
        assert any(isinstance(obj.content, EnrichedMalware) for obj in results1)
        assert all(obj.is_enriched is True for obj in results1)

    def test_lookup_raises_EnrichmentLookupError(self, lookup_mgr, mocker):
        mocker.patch.object(lookup_mgr.rf_client, 'request', side_effect=HTTPError)
        with pytest.raises(EnrichmentLookupError):
            lookup_mgr.lookup(entity='google.com', entity_type='domain')

    f = [
        (['risk'], ENTITY_FIELDS, ENTITY_FIELDS),
        (['timestamps'], ENTITY_FIELDS, ENTITY_FIELDS),
        (['counts'], ENTITY_FIELDS, ENTITY_FIELDS + ['counts']),
        (['risk', 'counts'], ENTITY_FIELDS, ENTITY_FIELDS + ['counts']),
        (['counts', 'analyst_notes'], ENTITY_FIELDS, ENTITY_FIELDS + ['counts', 'analyst_notes']),
        (ENTITY_FIELDS, ENTITY_FIELDS, ENTITY_FIELDS),
        ([], ENTITY_FIELDS, ENTITY_FIELDS),
    ]

    @pytest.mark.parametrize(('fields', 'default_fields', 'expected'), f)
    def test_merge_fields(self, lookup_mgr, fields, default_fields, expected):
        res = lookup_mgr._merge_fields(fields, default_fields)
        assert sorted(res) == sorted(expected)

    def test_lookup_404(self, lookup_mgr, mocker):
        mocker.patch.object(lookup_mgr, '_fetch_data', return_value=None)
        res = lookup_mgr.lookup(entity='test.com', entity_type='domain')
        assert res.content == '404 received. Nothing known on this entity'
        assert res.is_enriched is False

    def test_lookup_404_with_wrong_entity_type(self, lookup_mgr, mocker):
        mocker.patch.object(lookup_mgr, '_fetch_data', return_value=None)
        res = lookup_mgr.lookup(entity='test.com', entity_type='ip')
        assert res.content == '404 received. Nothing known on this entity'
        assert res.is_enriched is False

    def test_lookup_bulk_multithreaded(self, lookup_mgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'lookup_sample_malware.json')
        mocker.patch.object(lookup_mgr.rf_client, 'request', return_value=mock)
        spy = mocker.spy(lookup_mgr.rf_client, 'request')
        lookup_mgr.lookup_bulk(IPS, 'ip')
        args1 = spy.call_args
        lookup_mgr.max_workers = 2
        lookup_mgr.lookup_bulk(IPS, 'ip')
        args2 = spy.call_args

        assert args1 == args2

    def test_lookup_bulk_workers(self, lookup_mgr, mocker, make_response):
        IOCS = ['8.8.8.8', '1.1.1.1']

        dict_1 = {
            'data': {
                'timestamps': {
                    'lastSeen': '2024-10-31T08:31:07.659Z',
                    'firstSeen': '2010-04-27T12:46:51.000Z',
                },
                'risk': {
                    'criticalityLabel': 'None',
                    'riskString': '0/79',
                    'rules': 0,
                    'criticality': 0,
                    'riskSummary': 'No Risk Rules are currently observed.',
                    'score': 0,
                    'evidenceDetails': [],
                },
                'entity': {'id': 'ip:8.8.8.8', 'name': '8.8.8.8', 'type': 'IpAddress'},
            }
        }
        dict_2 = {
            'data': {
                'timestamps': {
                    'lastSeen': '2024-10-31T08:32:17.745Z',
                    'firstSeen': '2010-06-16T01:41:47.000Z',
                },
                'risk': {
                    'criticalityLabel': 'None',
                    'riskString': '0/79',
                    'rules': 0,
                    'criticality': 0,
                    'riskSummary': 'No Risk Rules are currently observed.',
                    'score': 0,
                    'evidenceDetails': [],
                },
                'entity': {'id': 'ip:1.1.1.1', 'name': '1.1.1.1', 'type': 'IpAddress'},
            }
        }

        side_effect = [make_response(dict_1), make_response(dict_2)]
        mocker.patch.object(lookup_mgr.rf_client, 'request', side_effect=side_effect)
        data = lookup_mgr.lookup_bulk(entity=IOCS, entity_type='ip', max_workers=2)
        assert isinstance(data, list)
        assert all(d.entity in IOCS for d in data)
        assert len(data) == 2
        assert all(isinstance(d, EnrichmentData) for d in data)

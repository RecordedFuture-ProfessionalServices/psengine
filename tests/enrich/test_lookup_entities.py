import pytest
from constants import (
    FIELDS_ALL_COMPANY,
    FIELDS_ALL_DOMAIN,
    FIELDS_ALL_HASH,
    FIELDS_ALL_IP,
    FIELDS_ALL_MALWARE,
    FIELDS_ALL_URL,
    FIELDS_ALL_VULNERABILITY,
    IPS,
    MALWS,
    MOCK_DIR,
)

from psengine.enrich import (
    EnrichedCompany,
    EnrichedDomain,
    EnrichedHash,
    EnrichedIP,
    EnrichedMalware,
    EnrichedURL,
    EnrichedVulnerability,
)

ENRICH_FIELDS_MAPS = {
    'fields_company': FIELDS_ALL_COMPANY,
    'fields_domain': FIELDS_ALL_DOMAIN,
    'fields_hash': FIELDS_ALL_HASH,
    'fields_ip': FIELDS_ALL_IP,
    'fields_malware': FIELDS_ALL_MALWARE,
    'fields_url': FIELDS_ALL_URL,
    'fields_vulnerability': FIELDS_ALL_VULNERABILITY,
}


to_enrich = [
    ('ip', '108.137.174.209', 'Test_Lookup.test_validation_108_137_174_209.json'),
    ('ip', '147.102.210.202', 'Test_Lookup.test_validation_147_102_210_202.json'),
    ('ip', '152.65.223.64', 'Test_Lookup.test_validation_152_65_223_64.json'),
    ('ip', '25.125.185.219', 'Test_Lookup.test_validation_25_125_185_219.json'),
    ('ip', '33.102.48.0', 'Test_Lookup.test_validation_33_102_48_0.json'),
    ('ip', '93.28.6.220', 'Test_Lookup.test_validation_93_28_6_220.json'),
    (
        'hash',
        '1b1388d525b99027bf5257ce406523cd3ff485e65381b1e07dec84be5b75f6c4',
        'Test_Lookup.test_validation_1b1388d5.json',
    ),
    (
        'hash',
        'b90506677bd87591d9a33f4f8a3f12d86516072885aba79c606277f05c4e7917',
        'Test_Lookup.test_validation_b905066.json',
    ),
    ('url', 'https://dude.clinic/', 'Test_Lookup.test_validation_https_dude.clinic.json'),
    ('url', 'https://tip.istanbul/', 'Test_Lookup.test_validation_https_tip_istanbul.json'),
    ('domain', 'hospitals.aquitaine', 'Test_Lookup.test_validation_hospital_acquitaine.json'),
    ('domain', 'necklace.london', 'Test_Lookup.test_validation_necklace_london.json'),
    ('domain', 'sewing.istanbul', 'Test_Lookup.test_validation_sewing_istanbul.json'),
    ('malware', '9AvGLt', 'Test_Lookup.test_validation_9AvGLt.json'),
    ('malware', 'Nz2mWw', 'Test_Lookup.test_validation_Nz2mWw.json'),
    ('company', '9QgSZ', 'Test_Lookup.test_validation_9QgSZ.json'),
    ('company', 'moTWQ', 'Test_Lookup.test_validation_moTWQ.json'),
    ('company', 'sAhqI', 'Test_Lookup.test_validation_sAhqI.json'),
    ('vulnerability', 'JMDXqF', 'Test_Lookup.test_validation_JMDXqF.json'),
    ('vulnerability', 'pgTwuF', 'Test_Lookup.test_validation_pgTwuF.json'),
    ('vulnerability', 'PLTMhZ', 'Test_Lookup.test_validation_PLTMhZ.json'),
    ('Organization', 'Xgwt9', 'Test_Lookup.test_validation_Xgwt9.json'),
    ('Organization', 'ZfiiH', 'Test_Lookup.test_validation_ZfiiH.json'),
]

FIELD_PARAM_MAP = {
    'ip': 'fields_ip',
    'domain': 'fields_domain',
    'url': 'fields_url',
    'hash': 'fields_hash',
    'vulnerability': 'fields_vulnerability',
    'malware': 'fields_malware',
    'company_by_domain': 'fields_company',
    'company': 'fields_company',
    'Organization': 'fields_company',
}

EXPECTED_CLASS_MAP = {
    'ip': EnrichedIP,
    'domain': EnrichedDomain,
    'url': EnrichedURL,
    'hash': EnrichedHash,
    'vulnerability': EnrichedVulnerability,
    'malware': EnrichedMalware,
    'company_by_domain': EnrichedCompany,
    'company': EnrichedCompany,
    'Organization': EnrichedCompany,
}


class Test_LookupModels:
    @pytest.mark.parametrize(
        ('type_', 'ioc', 'mock_file'),
        to_enrich,
        ids=[f'{i}_{e[0]}' for i, e in enumerate(to_enrich)],
    )
    def test_validation(self, type_, ioc, lookup_mgr, mocker, mock_request, mock_file):
        field_param_name = FIELD_PARAM_MAP.get(type_)
        expected_class = EXPECTED_CLASS_MAP.get(type_)
        mock = mock_request(MOCK_DIR / mock_file)
        mocker.patch.object(lookup_mgr.rf_client, 'request', return_value=mock)
        if field_param_name and expected_class:
            fields = ENRICH_FIELDS_MAPS[field_param_name]
            data = lookup_mgr.lookup(ioc, type_, fields)
            assert isinstance(data.content, expected_class)
            assert str(data)
            assert hash(data)
        else:
            pytest.skip(f'No field mapping or expected class for type: {type_}')

    def test_adt_methods_ip(self, lookup_mgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'Test_Lookup.test_validation_108_137_174_209.json'),
            mock_request(MOCK_DIR / 'Test_Lookup.test_validation_147_102_210_202.json'),
            mock_request(MOCK_DIR / 'Test_Lookup.test_validation_152_65_223_64.json'),
        ] * 2
        mocker.patch.object(lookup_mgr.rf_client, 'request', side_effect=mocks)
        ips = IPS + IPS
        data = lookup_mgr.lookup_bulk(ips, entity_type='ip')
        ip1 = {d for d in data if d.entity == '108.137.174.209'}.pop()
        ip2 = {d for d in data if d.entity == '147.102.210.202'}.pop()
        assert all(isinstance(d.content, EnrichedIP) for d in data)
        assert len(ips) == len(data)
        assert len(ips) / 2 == len(set(data))
        assert ip1 > ip2
        assert ip2 < ip1
        assert 'Last Seen' in str(ip1)
        assert 'Risk Score' in str(ip1)

    def test_adt_methods_404(self, lookup_mgr, mocker):
        mocker.patch.object(lookup_mgr, '_fetch_data', return_value=None)
        data = lookup_mgr.lookup('test', entity_type='company')
        data2 = lookup_mgr.lookup('test', entity_type='company')
        data3 = lookup_mgr.lookup('test.com', entity_type='domain')

        assert isinstance(data.content, str)
        assert data == data2
        assert len({data, data, data2, data3}) == 2
        assert data3 > data
        assert '404' in data.content
        assert '404' in str(data3)
        assert '404' in repr(data3)
        assert isinstance(data.content, str)

    def test_adt_methods_malware(self, lookup_mgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'Test_Lookup.test_validation_9AvGLt.json'),
            mock_request(MOCK_DIR / 'Test_Lookup.test_validation_Nz2mWw.json'),
        ] * 2
        mocker.patch.object(lookup_mgr.rf_client, 'request', side_effect=mocks)

        malwares = MALWS + MALWS
        data = lookup_mgr.lookup_bulk(malwares, entity_type='malware')

        malware1 = {d for d in data if d.entity == '9AvGLt'}.pop()
        malware2 = {d for d in data if d.entity == 'Nz2mWw'}.pop()
        assert all(isinstance(d.content, EnrichedMalware) for d in data)
        assert len(malwares) == len(data)
        assert len(malwares) / 2 == len(set(data))
        assert malware1 > malware2
        assert malware2 < malware1
        assert 'Last Seen' in str(malware1)

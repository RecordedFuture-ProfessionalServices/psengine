from copy import deepcopy

import pytest
from constants import MOCK_DIR

from psengine.enrich.soar import SOAREnrichedEntity, SOAREnrichIn, SOAREnrichOut
from psengine.enrich.soar_mgr import SoarMgr


class Test_SoarModels:
    data = [
        ('soar_ip', 'ip', 'Test_Soar.test_iocs_ip.json'),
        ('soar_domain', 'domain', 'Test_Soar.test_iocs_domain.json'),
        ('soar_hash', 'hash_', 'Test_Soar.test_iocs_hash.json'),
        ('soar_vuln', 'vulnerability', 'Test_Soar.test_iocs_vuln.json'),
        ('soar_url', 'url', 'Test_Soar.test_iocs_url.json'),
        ('soar_company', 'companybydomain', 'Test_Soar.test_iocs_company.json'),
    ]

    @pytest.mark.parametrize(
        ('infile', 'ioc_type', 'outfile'), data, ids=[ioc_type for _, ioc_type, _ in data]
    )
    def test_iocs(self, soar_mgr: SoarMgr, infile, outfile, ioc_type, mocker, mock_request):
        mock = mock_request(MOCK_DIR / outfile)
        mocker.patch.object(soar_mgr.rf_client, 'request', return_value=mock)
        mocker.patch.object(
            soar_mgr.rf_client,
            'request',
            side_effect=lambda *args, **kwargs: deepcopy(mock),  # noqa: ARG005
        )
        iocs = (MOCK_DIR.parent / 'static' / f'{infile}.csv').read_text().splitlines()
        data = soar_mgr.soar(**{ioc_type: iocs})
        (SOAREnrichedEntity.model_validate(d) for d in data)

    iocs = [
        ('8.8.8.8', 'ip', 'Test_Soar.test_iocs_low_risk_ip.json'),
        ('google.com', 'domain', 'Test_Soar.test_iocs_low_risk_domain.json'),
        (
            '7a7eae36a54dada555db57bd8f24e4a38a9b0f0432e13d19b16b538deb5e4142',
            'hash_',
            'Test_Soar.test_iocs_low_risk_hash.json',
        ),
        ('CVE-2015-3301', 'vulnerability', 'Test_Soar.test_iocs_low_risk_vuln.json'),
        ('http://www.test.test.md.ci', 'url', 'Test_Soar.test_iocs_low_risk_url.json'),
        (
            'perfectionplus.com',
            'companybydomain',
            'Test_Soar.test_iocs_low_risk_companybydomain.json',
        ),
    ]

    @pytest.mark.parametrize(
        ('ioc', 'ioc_type', 'infile'), iocs, ids=[ioc_type for _, ioc_type, _ in iocs]
    )
    def test_iocs_low_risk(self, soar_mgr, ioc, ioc_type, infile, mocker, mock_request):
        mock = mock_request(MOCK_DIR / infile)
        mocker.patch.object(soar_mgr.rf_client, 'request', return_value=mock)
        data = soar_mgr.soar(**{ioc_type: [ioc]})
        assert all(isinstance(d, SOAREnrichOut) for d in data)

    def test_soar_methods(self, soar_mgr, mocker, mock_request):
        data = {
            'url': ['https://phishing-example.net'],
            'ip': ['42.194.199.231'],
            'domain': ['recordedfuture.com'],
            'hash_': ['1a9c27e5be8c58da1c02fc4245a07831d5d431cdd1a91cd35d2dd0ad62da71cd'],
            'vulnerability': ['CVE-2021-44228'],
        }
        mocks = [
            mock_request(MOCK_DIR / 'Test_Soar.test_soar_methods_url.json'),
            mock_request(MOCK_DIR / 'Test_Soar.test_soar_methods_ip.json'),
            mock_request(MOCK_DIR / 'Test_Soar.test_soar_methods_domain.json'),
            mock_request(MOCK_DIR / 'Test_Soar.test_soar_methods_hash.json'),
            mock_request(MOCK_DIR / 'Test_Soar.test_soar_methods_vuln.json'),
        ]

        mocker.patch.object(soar_mgr.rf_client, 'request', side_effect=mocks)
        res = [soar_mgr.soar(**{ioc_type: ioc})[0].content for ioc_type, ioc in data.items()]
        url, ip, domain, hash_, vuln = res
        assert sorted(res) == [url, domain, hash_, ip, vuln]
        assert {ip, ip, ip, domain, ip} == {ip, domain}
        assert url < ip
        assert domain > url
        assert domain >= domain
        assert vuln != ip
        assert 'Risk Score' in str(vuln)

    @pytest.mark.parametrize(('ioc', 'ioc_type', 'discard'), iocs)
    def test_payload_sent(self, ioc, ioc_type, discard):  # noqa: ARG002
        all_iocs = {x[1]: [x[0]] for x in self.iocs}

        SOAREnrichIn.model_validate({ioc_type: [ioc]})
        SOAREnrichIn.model_validate({ioc_type: [ioc, ioc]})
        SOAREnrichIn.model_validate(all_iocs)

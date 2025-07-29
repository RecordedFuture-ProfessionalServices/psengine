import pytest
from constants import COMPANY_DOM, DOMS, HASHS, IPS, MOCK_DIR, URLS
from requests import HTTPError

from psengine.enrich import EnrichmentSoarError, SOAREnrichedEntity, SOAREnrichOut
from psengine.enrich.constants import SOAR_POST_ROWS
from psengine.enrich.soar_mgr import SoarMgr


class Test_SoarMgr:
    def test_soar(self, soar_mgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'Test_Soar.test_soar.json')
        mocker.patch.object(soar_mgr.rf_client, 'request', return_value=mock)
        model1 = soar_mgr.soar(ip=IPS, domain=DOMS, url=URLS, hash_=HASHS)
        assert all(isinstance(d.content, SOAREnrichedEntity) for d in model1)

    def test_soar_company(self, soar_mgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'Test_Soar.test_soar_company1.json'),
            mock_request(MOCK_DIR / 'Test_Soar.test_soar_companies.json'),
        ]
        mocker.patch.object(soar_mgr.rf_client, 'request', side_effect=mocks)
        model1 = soar_mgr.soar(companybydomain=[COMPANY_DOM])
        model2 = soar_mgr.soar(companybydomain=['google.com', 'facebook.com', 'amazon.com'])
        assert all(isinstance(d.content, SOAREnrichedEntity) for d in model1)
        assert all(isinstance(d.content, SOAREnrichedEntity) for d in model2)

    def test_soar_raises_EnrichmentSoarError(self, soar_mgr, mocker):
        mocker.patch.object(soar_mgr.rf_client, 'request', side_effect=HTTPError)
        with pytest.raises(EnrichmentSoarError):
            soar_mgr.soar(domain=['google.com'])

    def test_soar_multithread(self, mocker, mock_request):
        soar_mgr = SoarMgr()
        mock = mock_request(MOCK_DIR / 'Test_Soar.test_soar_multithreaded.json')
        mocker.patch.object(soar_mgr.rf_client, 'request', return_value=mock)
        res = soar_mgr.soar(
            domain=['google.com'],
            url=['http://alphastand.top/alien/fre.php'],
            ip=['124.71.84.65'],
            max_workers=5,
        )

        assert len(res) == 3
        assert all(isinstance(d, SOAREnrichOut) for d in res)

    def test_soar_batching(self, soar_mgr):
        data = {'ip': IPS, 'domain': DOMS, 'urls': URLS, 'companybydomain': [COMPANY_DOM]}
        expected = [
            {'ip': ['108.137.174.209', '147.102.210.202']},
            {
                'domain': ['qassar22.ddns.net'],
                'ip': ['152.65.223.64'],
            },
            {'domain': ['marcelotatuape.ddns.net', 'silentlegion.duckdns.org']},
            {
                'urls': [
                    'https://pub-43afe9e8810c4c5e8ffcef393309937c.r2.dev/0.html',
                    'https://linktoxic34.com/wp-content/themes/twentytwentytwo/dark.hta',
                ]
            },
            {'companybydomain': ['google.com'], 'urls': ['http://wfsdragon.ru/api/setStats.php']},
        ]
        res = soar_mgr._batched_cross_entity(data, 2)
        assert res == expected

    def test_soar_batchin_low(self, soar_mgr):
        data = {'ip': IPS}
        res = soar_mgr._batched_cross_entity(data, 2)

        expected = [{'ip': ['108.137.174.209', '147.102.210.202']}, {'ip': ['152.65.223.64']}]
        assert res == expected

    def test_soar_batching_full(self, soar_mgr):
        data = {'ip': IPS, 'domain': DOMS, 'urls': URLS, 'companybydomain': [COMPANY_DOM]}
        res = soar_mgr._batched_cross_entity(data, SOAR_POST_ROWS)
        assert res == [data]

    def test_soar_batching_exactly_divisible(self, soar_mgr):
        data = {
            'ip': ['1.1.1.1', '2.2.2.2', '3.3.3.3'],
            'domain': ['example.com', 'test.com', 'sample.com'],
        }
        res = soar_mgr._batched_cross_entity(data, 3)
        assert res == [
            {'ip': ['1.1.1.1', '2.2.2.2', '3.3.3.3']},
            {'domain': ['example.com', 'test.com', 'sample.com']},
        ]

    def test_soar_raise_ValueError(self, soar_mgr):
        with pytest.raises(ValueError):
            soar_mgr.soar()

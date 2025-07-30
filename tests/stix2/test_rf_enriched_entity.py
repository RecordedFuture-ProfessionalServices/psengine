import json
from pathlib import Path

import pytest

from psengine.enrich import LookupMgr
from psengine.stix2 import EnrichedIndicator
from tests.stix2.conftest import MOCK_DIR


class Test_EnrichedIndicator:
    def test_ip_riskrules(self, tests_dir, tmp_path):
        input_file = Path(tests_dir) / 'static' / 'stix2' / 'enriched_ip.json'
        infile = json.loads(input_file.read_text())

        ev = infile['data']['results'][0]['risk']['evidenceDetails']
        risk_score = infile['data']['results'][0]['risk']['score']
        mapping = infile['data']['results'][0]['riskMapping']
        entity = '124.71.84.65'
        ind = EnrichedIndicator(
            name=entity,
            type_='IpAddress',
            evidence_details=ev,
            risk_mapping=mapping,
            link_hits=[],
            confidence=risk_score,
            create_indicator=True,
            create_obs=True,
        )

        output_file = Path(tmp_path) / 'enriched_ip.json'
        output_file.write_text(ind.bundle.serialize())

    indicators = [
        ('http://mail.a620cwmendzh73xuso9i8b.duckdns.org/', 'url'),
        ('avsvmcloud.com', 'domain'),
        ('d6097e942dd0fdc1fb28ec1814780e6ecc169ec6d24f9954e71954eedbc4c70e', 'hash'),
        ('5.35.130.255', 'ip'),
    ]

    @pytest.mark.parametrize(
        ('indicator', 'type_'), indicators, ids=(i for i in range(len(indicators)))
    )
    def test_conversion(
        self,
        tmp_path,
        indicator,
        type_,
        request,
        mocker,
        mock_request,
    ):
        rfem = LookupMgr()
        node_id = request.node.callspec.id
        file = MOCK_DIR / f'test_conversion[{node_id}]_0.json'
        mock = mock_request(file)

        mocker.patch.object(rfem.rf_client, 'request', return_value=mock)

        data = rfem.lookup(indicator, type_, fields=['riskMapping', 'links', 'aiInsights'])
        result = data.content
        enriched_indicator = EnrichedIndicator(
            name=indicator,
            type_=data.entity_type,
            evidence_details=result.risk.evidence_details,
            link_hits=result.links.hits,
            risk_mapping=result.risk_mapping,
            confidence=result.risk.score,
            ai_insights=result.ai_insights,
        )

        output_file = Path(tmp_path) / f'enriched_{data.entity_type}.json'
        output_file.write_text(enriched_indicator.bundle.serialize())

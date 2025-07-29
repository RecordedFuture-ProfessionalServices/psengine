import pytest
from stix2 import Bundle

from psengine.analyst_notes import AnalystNoteMgr
from psengine.risklists import DefaultRiskList, RisklistMgr
from psengine.stix2 import RFBundle
from tests.stix2.conftest import MOCK_DIR

# tQHD_j - existing note without attachment
# tPtLVw - existing note with PDF attachment
# oJeqDP - existing note with yara attachment
# o6_lui - existing note with sigma attachment
# cynQie - existing note with snort attachment


class Test_RFBundle:
    @pytest.mark.parametrize(
        'note_id',
        ['tPtLVw', 'oJeqDP', 'o6_lui', 'cynQie'],
    )
    def test_from_analyst_note_with_attachment(
        self,
        an_mgr: AnalystNoteMgr,
        note_id: str,
        mocker,
        make_binary_response,
        request,
        mock_request,
    ):
        node_id = request.node.callspec.id
        file = MOCK_DIR / f'test_from_analyst_note_with_attachment[{node_id}]_0.json'

        mock = make_binary_response(b'abcd', {'Content-Disposition': 'filename=abc.ad'})
        mocks = [mock_request(file), mock]

        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=mocks)
        note = an_mgr.lookup(note_id)
        data, _ = an_mgr.fetch_attachment(note_id)
        note_bundle = RFBundle.from_analyst_note(note, data)

        assert isinstance(note_bundle, Bundle)

    @pytest.mark.parametrize(
        'note_id',
        ['tQHD_j', 'tmoHrc', 'tmoM4O', 'tmoTwJ'],
    )
    def test_from_analyst_note_no_attachment(
        self,
        an_mgr: AnalystNoteMgr,
        note_id: str,
        mocker,
        request,
        mock_request,
    ):
        node_id = request.node.callspec.id
        file = MOCK_DIR / f'test_from_analyst_note_no_attachment[{node_id}]_0.json'

        mocks = mock_request(file)

        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mocks)

        note = an_mgr.lookup(note_id)
        note_bundle = RFBundle.from_analyst_note(note)

        assert isinstance(note_bundle, Bundle)

    @pytest.mark.parametrize(
        ('risklist_name', 'entity_type'),
        [
            ('recentLinkedToAPT', 'ip'),
            ('linkedToCyberAttack', 'domain'),
            ('proxyUrl', 'url'),
            ('recentActiveMalware', 'hash'),
        ],
    )
    def test_from_default_risklist(
        self, risklist_name: str, entity_type: str, mocker, make_csv_response, request
    ):
        rsm = RisklistMgr()
        node_id = request.node.callspec.id
        mocks = make_csv_response(
            MOCK_DIR / f'test_from_default_risklist[{node_id}]_0.csv', gzip_compress=False
        )
        mocker.patch.object(rsm.rf_client, 'request', return_value=mocks)

        risklist = rsm.fetch_risklist(risklist_name, entity_type, validate=DefaultRiskList)
        risklist_bundle = RFBundle.from_default_risklist(risklist, entity_type)

        assert isinstance(risklist_bundle, Bundle)

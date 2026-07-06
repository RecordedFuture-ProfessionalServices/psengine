from copy import deepcopy
from datetime import datetime
from pathlib import Path

import pytest

from psengine.analyst_notes import AnalystNoteMgr
from psengine.analyst_notes.models import Attributes, NoteEvent
from psengine.analyst_notes.note import (
    AnalystNote,
    AnalystNotePublishIn,
    AnalystNotePublishOut,
)
from tests.analyst_notes.constants import MOCK_DIR

NOTES_MD_PATH = Path(__file__).parent.parent / 'static' / 'analyst_notes'
PREVIEW_PUBLISH_DATA = [
    {
        'attributes': {
            'title': 'Pro-Russian Hacktivist Groups Promote DDoS Stresser Service “TUCKER STRESS”',
            'text': 'Several pro-Russian hacktivist groups have promoted the',
            'published': '2023-11-03T13:31:56.878Z',
            'context_entities': [
                'B_FAG',
                'L470c8',
                'JQ0VYr',
                'JgElTW',
                'source:KZFCph',
                'source:TLzyKt',
            ],
            'validation_urls': ['url:https://app.recordedfuture.com/live/sc/5nb378wSKMOU'],
            'note_entities': ['tPo-Zi', 'iCqv44', '0f-N9', '9ht7w', 'mitre:T1498'],
            'topic': 'TXSFt5',
        }
    },
    {
        'attributes': {
            'title': 'test pytest',
            'text': 'test related to test.com',
            'context_entities': ['idn:test.com'],
            'note_entities': [],
        }
    },
    {
        'attributes': {
            'title': 'test pytest',
            'text': 'test related to test.com',
        }
    },
]


class Test_AnalystNotesModels:
    @pytest.mark.parametrize(
        'note_id',
        [
            'uytHPy',
            'rHJX0r',
            'svjcGx',
            'uPjLua',
            'tIt2k5',
            'ucDKeZ',
            'tTKpyP',
            'uQiDV0',
        ],
    )
    def test_analyst_note_model_validate(
        self, an_mgr: AnalystNoteMgr, note_id: str, mocker, mock_request
    ):
        mock = mock_request(MOCK_DIR / f'test_analyst_note_model_validate[{note_id}].json')
        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)
        an_mgr.lookup(note_id)

    def test_validate_search_analyst_notes(self, an_mgr: AnalystNoteMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_validate_search_analyst_notes_0.json'),
            mock_request(MOCK_DIR / 'test_validate_search_analyst_notes_1.json'),
        ]

        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=mocks)
        an_mgr.search()

    @pytest.mark.parametrize('data', PREVIEW_PUBLISH_DATA)
    def test_validate_preview_output(self, an_mgr: AnalystNoteMgr, data, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_validate_preview_output[data0].json'),
            mock_request(MOCK_DIR / 'test_validate_preview_output[data1].json'),
            mock_request(MOCK_DIR / 'test_validate_preview_output[data2].json'),
        ]

        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=mocks)

        attributes = data['attributes']
        an_mgr.preview(**attributes)

    @pytest.mark.parametrize('data', PREVIEW_PUBLISH_DATA)
    def test_validate_publish_output(self, an_mgr: AnalystNoteMgr, data, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_validate_publish_output[data0].json'),
            mock_request(MOCK_DIR / 'test_validate_publish_output[data1].json'),
            mock_request(MOCK_DIR / 'test_validate_publish_output[data2].json'),
        ]

        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=mocks)

        attributes = data['attributes']
        return_value = an_mgr.publish(**attributes)
        AnalystNotePublishOut.model_validate(return_value)

    @pytest.mark.parametrize('data', PREVIEW_PUBLISH_DATA)
    def test_validate_publish_input(self, data):
        AnalystNotePublishIn.model_validate(data)

    def test_hash(self, an_mgr: AnalystNoteMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'note_tQHD_j.json'),
            mock_request(MOCK_DIR / 'note_tQHD_j.json'),
            mock_request(MOCK_DIR / 'note_ytHPy.json'),
            mock_request(MOCK_DIR / 'note_ytHPy.json'),
        ]

        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=mocks)
        note1 = an_mgr.lookup('uytHPy')
        note1_twin = an_mgr.lookup('uytHPy')
        note2 = an_mgr.lookup('rHJX0r')
        note2_twin = an_mgr.lookup('rHJX0r')

        notes = [note1, note2, note1_twin, note2_twin]

        assert note1 == note1_twin
        assert note2 == note2_twin
        assert note1 != note2
        assert hash(note1)
        assert set(notes) == {note1, note2}

    def test_ordering(self):
        base = {
            'id': '12345',
            'attributes': {'title': 'abc', 'text': 'abc'},
            'source': {'id': 'abc', 'name': 'abc', 'type': 'abc'},
        }
        note = deepcopy(base)
        note['attributes']['published'] = '2023-11-03T13:31:56.878Z'
        note1 = AnalystNote.model_validate(note)

        note = deepcopy(base)
        note['attributes']['published'] = '2022-11-03T13:31:56.878Z'
        note2 = AnalystNote.model_validate(note)

        note = deepcopy(base)
        note['attributes']['published'] = '2024-11-03T13:31:56.878Z'
        note3 = AnalystNote.model_validate(note)

        note = deepcopy(base)
        note['attributes']['published'] = '2025-11-03T13:31:56.878Z'
        note['id'] = '5'
        note4 = AnalystNote.model_validate(note)

        note = deepcopy(base)
        note['attributes']['published'] = '2025-11-03T13:31:56.878Z'
        note['id'] = '7'
        note5 = AnalystNote.model_validate(note)

        notes = [note1, note2, note3, note4, note5]
        assert sorted(notes) == [note2, note1, note3, note4, note5]
        assert note2 < note1
        assert note1 <= note3
        assert note1 <= note1
        assert note1 != note2

    @pytest.mark.parametrize(
        ('note', 'att_type', 'mock_file'),
        [
            ('o6_lui', 'sigma', 'test_attachment_type[o6_lui-sigma].json'),
            ('oJeqDP', 'yara', 'test_attachment_type[oJeqDP-yara].json'),
            ('tQHD_j', None, 'test_attachment_type[tQHD_j-None].json'),
            ('cynQie', 'snort', 'test_attachment_type[cynQie-snort].json'),
            ('tPtLVw', None, 'test_attachment_type[tPtLVw-None].json'),
        ],
    )
    def test_attachment_type(self, an_mgr, note, att_type, mock_file, mocker, mock_request):
        mock = mock_request(MOCK_DIR / mock_file)

        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)
        note = an_mgr.lookup(note)
        note = AnalystNote.model_validate(note)
        assert note.detection_rule_type == att_type

    def test_skip_unknown_note_event(self):
        event_1 = NoteEvent(type='unknown', attributes={'a': 1})
        event_2 = NoteEvent(
            type='Coup', attributes={'start': datetime.now(), 'stop': datetime.now()}
        )
        attr = Attributes(
            title='moise', text='moise', published=datetime.now(), events=[event_1, event_2]
        )

        assert attr.events == [event_2]

    @pytest.mark.parametrize('id_', ['zBRMl5', 'wtnmzO', '5n_C21', '5ICOTn', 'wazc3I'])
    @pytest.mark.parametrize('html', [True, False])
    def test_markdown(self, an_mgr, id_, html, mocker, mock_request):
        mock_file = f'test_markdown[{html}-{id_}].json'
        mock = mock_request(MOCK_DIR / mock_file)

        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)
        note = an_mgr.lookup(id_)
        file = NOTES_MD_PATH / f'{id_}_html_{html}.md'
        data = note.markdown(html_tags=html)
        assert file.read_text() == data

    def test_markdown_without_entities(self, an_mgr: AnalystNoteMgr, mocker, mock_request):
        mock_file = 'test_markdown_without_entities.json'
        mock = mock_request(MOCK_DIR / mock_file)

        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)
        note = an_mgr.lookup('zBRMl5')

        assert 'Entities' not in note.markdown(extract_entities=False)

    def test_markdown_preserves_note_tables(self):
        table = (
            '| Indicator | Type |\n| -- | -- |\n| example.com | Domain |\n| 1.2.3.4 | IP Address |'
        )
        note = AnalystNote.model_validate(
            {
                'id': 'table-note',
                'source': {
                    'id': 'source',
                    'name': 'Recorded Future',
                    'type': 'Source',
                },
                'attributes': {
                    'title': 'Table Note',
                    'text': f'Before\n\n{table}\n\nAfter',
                    'published': '2025-01-01T00:00:00.000Z',
                    'topic': {
                        'id': 'topic',
                        'name': 'Threat Research',
                        'type': 'Topic',
                    },
                },
            }
        )

        data = note.markdown(extract_entities=False, diamond_model=False)

        assert table in data

    @pytest.mark.parametrize('defang', [True, False])
    @pytest.mark.parametrize('diamond_model', [True, False])
    def test_defang_iocs(self, an_mgr: AnalystNoteMgr, defang, diamond_model, mocker, mock_request):
        id_ = 'wazc3I'
        mock_file = f'test_defang_iocs[{defang}-{diamond_model}].json'
        mock = mock_request(MOCK_DIR / mock_file)

        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)
        note = an_mgr.lookup(id_)
        file = NOTES_MD_PATH / f'{id_}_defang_{defang}_diamond_{diamond_model}.md'
        data = note.markdown(
            defang_malicious_infrastructure=defang, diamond_model=diamond_model, html_tags=True
        )
        assert file.read_text() == data

    @pytest.mark.parametrize('html', [True, False])
    def test_multiple_diamond_models(self, an_mgr: AnalystNoteMgr, html, mocker, mock_request):
        id_ = '5N-9wh'

        mock_file = f'test_multiple_diamond_models[{html}].json'
        mock = mock_request(MOCK_DIR / mock_file)
        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)
        note = an_mgr.lookup(id_)
        file = NOTES_MD_PATH / f'{id_}_html_{html}.md'
        data = note.markdown(html_tags=html)

        assert file.read_text() == data

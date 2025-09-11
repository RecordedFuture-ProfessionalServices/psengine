import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from requests import ConnectionError, ConnectTimeout, HTTPError, ReadTimeout  # noqa: A004
from requests.models import Response

from psengine.analyst_notes import (
    AnalystNote,
    AnalystNoteAttachmentError,
    AnalystNoteDeleteError,
    AnalystNoteLookupError,
    AnalystNoteMgr,
    AnalystNotePreviewError,
    AnalystNotePreviewOut,
    AnalystNotePublishError,
    AnalystNoteSearchError,
    save_attachment,
    save_note,
)
from psengine.endpoints import (
    EP_ANALYST_NOTE_PREVIEW,
    EP_ANALYST_NOTE_PUBLISH,
)
from psengine.errors import WriteFileError
from tests.analyst_notes.constants import MOCK_DIR

# tQHD_j - existing note without attachment
# tPtLVw - existing note with PDF attachment
# oJeqDP - existing note with yara attachment
# o6_lui - existing note with sigma attachment
# cynQie - existing note with snort attachment
# mjit-b - existing note with xlsx attachment


class Test_AnalystNotesMgr:
    def test_lookup(self, an_mgr: AnalystNoteMgr, mock_request, mocker):
        mock = mock_request(MOCK_DIR / 'note_tQHD_j.json')
        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)
        note = an_mgr.lookup('tQHD_j')
        assert isinstance(note, AnalystNote)

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_lookup_raises_AnalystNoteLookupError(self, an_mgr: AnalystNoteMgr, exception, mocker):
        response = Response()
        response.status_code = 500
        excp_obj = exception('Error')
        excp_obj.response = response
        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=excp_obj)
        with pytest.raises(AnalystNoteLookupError):
            an_mgr.lookup('tQHD_j')

    def test_lookup_return_None_on_404(self, an_mgr: AnalystNoteMgr, mocker):
        response = Response()
        response.status_code = 404
        excp_obj = HTTPError('Not found')
        excp_obj.response = response
        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=excp_obj)
        assert an_mgr.lookup('tQHD_j') is None

    def test_fetch_attachment_returns_none_on_404(self, an_mgr: AnalystNoteMgr, mocker):
        response = Response()
        response.status_code = 404
        excp_obj = HTTPError('Not found')
        excp_obj.response = response
        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=excp_obj)

        result = an_mgr.fetch_attachment('tQHD_j')
        assert result == (b'', None)

    @pytest.mark.parametrize(
        ('note_id', 'exp_ext'),
        [
            ('tPtLVw', 'pdf'),
            ('oJeqDP', 'yar'),
            ('o6_lui', 'yml'),
            ('cynQie', 'txt'),
            ('mjit-b', 'xlsx'),
        ],
    )
    def test_fetch_attachment_check_extension(
        self, an_mgr: AnalystNoteMgr, note_id, exp_ext, mocker, make_binary_response
    ):
        mock = make_binary_response(b'abcd', {'Content-Disposition': f'filename=abc.{exp_ext}'})
        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)

        data, ext = an_mgr.fetch_attachment(note_id)
        assert isinstance(data, bytes)
        assert ext == exp_ext

    def test_fetch_attachment_raises_AnalystNoteAttachmentError(
        self, an_mgr: AnalystNoteMgr, mocker
    ):
        response = Response()
        response.status_code = 500
        http_error = HTTPError()
        http_error.response = response

        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=http_error)
        with pytest.raises(AnalystNoteAttachmentError):
            an_mgr.fetch_attachment('qwert')

    @pytest.mark.parametrize(
        ('note_id', 'exp_ext'),
        [('tPtLVw', 'pdf'), ('oJeqDP', 'yar'), ('o6_lui', 'yml'), ('cynQie', 'txt')],
    )
    def test_save_attachment_file(
        self, an_mgr: AnalystNoteMgr, tmp_path, note_id, exp_ext, mocker, make_binary_response
    ):
        mock = make_binary_response(b'abcd', {'Content-Disposition': f'filename=abc.{exp_ext}'})
        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)
        att, ext = an_mgr.fetch_attachment(note_id)

        save_attachment(note_id, att, ext, tmp_path.as_posix())
        out_file = Path(tmp_path) / f'{note_id}.{ext}'
        assert exp_ext == ext
        assert out_file.exists()
        assert out_file.stat().st_size

    def test_save_note(self, an_mgr: AnalystNoteMgr, tmp_path, mocker, mock_request):
        mock_file = MOCK_DIR / 'note_tQHD_j.json'
        mock = mock_request(mock_file)
        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)

        note_id = 'tQHD_j'
        rf_note = an_mgr.lookup(note_id)
        save_note(rf_note, tmp_path.as_posix())
        out_file = Path(tmp_path) / f'{note_id}.json'
        assert out_file.exists()
        assert out_file.stat().st_size

    def test_save_attachment_raises_WriteFileError(self, mocker):
        mocker.patch('psengine.helpers.OSHelpers.mkdir', side_effect=OSError)
        with pytest.raises(WriteFileError):
            save_attachment('xyz123', 'qwerty', b'', 'pdf')

    def test_search_ok_without_param(self, an_mgr: AnalystNoteMgr, mocker, mock_request):
        mocks = [
            'test_search_ok_without_param_0.json',
            'test_search_ok_without_param_1.json',
        ]
        mocks = [mock_request(MOCK_DIR / x) for x in mocks]
        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=mocks)

        output = an_mgr.search()

        assert isinstance(output, list)
        assert all(isinstance(note, AnalystNote) for note in output)
        assert all(note.attributes.title for note in output)

    def test_search_raises_SearchErorr_dueto_KeyError(self, an_mgr: AnalystNoteMgr, mocker):
        mocker.patch.object(
            an_mgr.rf_client,
            'request',
            return_value=mocker.Mock(json=lambda: {'wrong': {'results': []}}),
        )
        with pytest.raises(AnalystNoteSearchError):
            an_mgr.search()

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_search_raises_AnalystNoteSearchError(self, an_mgr: AnalystNoteMgr, exception, mocker):
        response = Response()
        response.status_code = 500
        excp_obj = exception('Error')
        excp_obj.response = response

        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=excp_obj)
        with pytest.raises(AnalystNoteSearchError):
            an_mgr._search({}, 20)

    data = [
        (None, 'TestEntity', None, None, 'TestTopic', None, None, False, None, 10, 5),
        ('2023-02-02', None, None, None, None, None, None, True, 'full', 5, 10),
        (None, 'EntityC', None, 'TitleC', None, None, None, False, 'min', 15, 20),
        ('2023-03-03', 'EntityD', None, None, 'TopicD', None, None, False, None, 25, 10),
        (None, 'EntityF', None, 'TitleF', 'TopicF', None, None, True, None, 20, 100),
    ]

    @pytest.mark.parametrize(
        (
            'pub',
            'entity',
            'author',
            'title',
            'topic',
            'label',
            'source',
            'tagged_text',
            'serial',
            'max_results',
            'notes_per_page',
        ),
        data,
        ids=range(len(data)),
    )
    def test_search_parameters(
        self,
        an_mgr,
        pub,
        entity,
        author,
        title,
        topic,
        label,
        source,
        tagged_text,
        serial,
        max_results,
        notes_per_page,
        mocker,
        mock_request,
    ):
        pattern = re.compile(r'^test_search_parameters\[\d+\]_\d+\.json$')
        files = [f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name)]
        mocks = [mock_request(MOCK_DIR / f) for f in files]
        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=mocks)
        spy_get = mocker.spy(an_mgr.rf_client, 'request')

        notes = an_mgr.search(
            published=pub,
            entity=entity,
            author=author,
            title=title,
            topic=topic,
            label=label,
            source=source,
            tagged_text=tagged_text,
            serialization=serial,
            max_results=max_results,
            notes_per_page=notes_per_page,
        )
        assert spy_get.call_args[1]['method'] == 'post'
        assert spy_get.call_args[1]['data'] is not None
        assert isinstance(spy_get.call_args[1]['data'], dict)
        assert len(spy_get.call_args[1]['data']) > 1
        assert spy_get.call_args[1]['url'] == 'https://api.recordedfuture.com/analyst-note/search'
        assert isinstance(notes, list)

    def test_search_from_list_of_topic_mock_search(self, an_mgr: AnalystNoteMgr, mocker):
        mocked = mocker.patch.object(an_mgr, '_search', return_value=[])
        an_mgr.search(topic=['TXSFt2', 'UrMRnT'])
        assert mocked.call_count == 2

    def test_search_from_list_of_topic(self, an_mgr: AnalystNoteMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_search_from_list_of_topic_0.json'),
            mock_request(MOCK_DIR / 'test_search_from_list_of_topic_1.json'),
            mock_request(MOCK_DIR / 'test_search_from_list_of_topic_2.json'),
            mock_request(MOCK_DIR / 'test_search_from_list_of_topic_3.json'),
        ]

        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=mocks)
        results = an_mgr.search(topic=['TXSFt2', 'UrMRnT'])
        assert len(set(results)) == len(results)

    def test_search_from_empty_topic_list(self, an_mgr: AnalystNoteMgr, mocker, mock_request):
        mocks = [
            mock_request(MOCK_DIR / 'test_search_from_empty_topic_list_0.json'),
            mock_request(MOCK_DIR / 'test_search_from_empty_topic_list_1.json'),
        ]

        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=mocks)
        results = an_mgr.search(topic=[])
        assert len(set(results)) == len(results)
        assert len(results)

    @pytest.mark.parametrize('nums', [1, 5, 10, 100])
    def test_search_with_different_limits(self, an_mgr: AnalystNoteMgr, nums, mocker, mock_request):
        pattern = re.compile(r'^test_search_with_different_limits\[\d+\]_\d+\.json$')
        files = [f for f in Path(MOCK_DIR).iterdir() if pattern.match(f.name)]
        mocks = [mock_request(MOCK_DIR / f) for f in files]
        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=mocks)

        results = an_mgr.search(max_results=nums)
        assert len(results) <= nums
        assert len(results) > 0

    @pytest.mark.parametrize('note_id', ['123456', 'tQHD_j'])
    def test_delete_404_returns_False(self, an_mgr: AnalystNoteMgr, note_id, mocker):
        response = Response()
        response.status_code = 404
        excp_obj = HTTPError('Not found')
        excp_obj.response = response
        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=excp_obj)

        assert an_mgr.delete(note_id) is False

    def test_delete_raises_ValidationError(self, an_mgr: AnalystNoteMgr):
        with pytest.raises(ValidationError):
            an_mgr.delete(1)

    def test_delete_ok(self, an_mgr: AnalystNoteMgr, mocker, make_response):
        data = {'status': 'Ok'}
        mock = make_response(data)
        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)
        spy = mocker.spy(an_mgr.rf_client, 'request')
        an_mgr.delete('abc')
        assert spy.call_args[0][0] == 'delete'
        assert (
            spy.call_args[1]['url'] == 'https://api.recordedfuture.com/analyst-note/delete/doc:abc'
        )

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_delete_raises_AnalystNoteDeleteError_connection_exception(
        self,
        an_mgr,
        exception,
        mocker,
    ):
        response = Response()
        response.status_code = 500
        excp_obj = exception('Error')
        excp_obj.response = response

        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=excp_obj)
        with pytest.raises(AnalystNoteDeleteError):
            an_mgr.delete('tQHD_j')

    def test_preview_ok(self, an_mgr: AnalystNoteMgr, mocker, mock_request):
        mock = mock_request(MOCK_DIR / 'test_preview_ok.json')
        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)
        note = an_mgr.preview(
            title='test pytest', text='test related to test.com', context_entities=['idn:test.com']
        )
        assert isinstance(note, AnalystNotePreviewOut)
        assert note.attributes.title == 'test pytest'
        assert note.attributes.text == 'test related to test.com'

    def test_preview_raises_ValidationError(self, an_mgr: AnalystNoteMgr):
        with pytest.raises(ValidationError):
            an_mgr.preview(title=123)

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_preview_raises_AnalystNotePreviewError_connection_exception(
        self,
        an_mgr,
        exception,
        mocker,
    ):
        response = Response()
        response.status_code = 500
        excp_obj = exception('Error')
        excp_obj.response = response

        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=excp_obj)
        with pytest.raises(AnalystNotePreviewError):
            an_mgr.preview(title='test pytest', text='test related to test.com')

    @pytest.mark.parametrize('topics', [['TXSFt2'], 'TXSFt2', ['TXSFt2', 'TXSFt3']])
    def test_preview_topics(self, an_mgr: AnalystNoteMgr, mocker, topics, mock_request):
        mock = mock_request(MOCK_DIR / 'test_preview_ok.json')
        mock_request = mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)

        an_mgr.preview(title='moise', text='moise', topic=topics)
        expected = topics if isinstance(topics, list) else [topics]
        call_args, params = mock_request.call_args
        assert call_args[0] == 'post'
        assert call_args[1] == EP_ANALYST_NOTE_PREVIEW
        assert params['data']['attributes']['topic'] == expected

    @pytest.mark.parametrize('topics', [['TXSFt2'], 'TXSFt2', ['TXSFt2', 'TXSFt3']])
    def test_publish_topics(self, an_mgr: AnalystNoteMgr, mocker, make_response, topics):
        data = {'note_id': 'doc:vqqO35'}

        mock = make_response(data)
        mock_request = mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)

        an_mgr.publish(
            title='test pytest',
            text='test related to test.com',
            context_entities=['idn:test.com'],
            topic=topics,
        )
        expected = topics if isinstance(topics, list) else [topics]
        call_args, params = mock_request.call_args
        assert call_args[0] == 'post'
        assert call_args[1] == EP_ANALYST_NOTE_PUBLISH
        assert params['data']['attributes']['topic'] == expected

    def test_publish_ok(self, an_mgr: AnalystNoteMgr, mocker, make_response):
        data = {'note_id': 'doc:vqqO35'}

        mock = make_response(data)
        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)

        output = an_mgr.publish(
            title='test pytest', text='test related to test.com', context_entities=['idn:test.com']
        )
        assert re.match('{"note_id": "doc:......"}', json.dumps(output.json()))

    def test_publish_raises_ValidationError(self, an_mgr: AnalystNoteMgr):
        with pytest.raises(ValidationError):
            an_mgr.publish(title=123, published=123)

    @pytest.mark.parametrize('exception', [HTTPError, ConnectTimeout, ConnectionError, ReadTimeout])
    def test_publish_raises_AnalystNotePublishError(self, an_mgr, exception, mocker):
        response = Response()
        response.status_code = 500
        excp_obj = exception('Error')
        excp_obj.response = response

        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=excp_obj)
        with pytest.raises(AnalystNotePublishError):
            an_mgr.publish(
                title='test pytest',
                text='test related to test.com',
                context_entities=['idn:test.com'],
            )

    def test_get_analyst_note_attachment_no_extension(self, an_mgr, mocker, make_binary_response):
        note_id = 'test_note_id'
        mock = make_binary_response(
            b'abcd', {'Content-Disposition': 'attachment; filename="file_without_extension"'}
        )
        mocker.patch.object(an_mgr.rf_client, 'request', return_value=mock)
        content, ext = an_mgr.fetch_attachment(note_id)

        assert content == b'abcd'
        assert ext == ''

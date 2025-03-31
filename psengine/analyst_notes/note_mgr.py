##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

import logging
import re
from itertools import chain
from typing import Optional, Union

from pydantic import Field, validate_call

from ..constants import DEFAULT_LIMIT
from ..endpoints import (
    EP_ANALYST_NOTE_ATTACHMENT,
    EP_ANALYST_NOTE_DELETE,
    EP_ANALYST_NOTE_LOOKUP,
    EP_ANALYST_NOTE_PREVIEW,
    EP_ANALYST_NOTE_PUBLISH,
    EP_ANALYST_NOTE_SEARCH,
)
from ..helpers import debug_call
from ..helpers.helpers import connection_exceptions
from ..rf_client import RFClient
from .constants import NOTES_PER_PAGE
from .errors import (
    AnalystNoteAttachmentError,
    AnalystNoteDeleteError,
    AnalystNoteLookupError,
    AnalystNotePreviewError,
    AnalystNotePublishError,
    AnalystNoteSearchError,
)
from .note import (
    AnalystNote,
    AnalystNotePreviewIn,
    AnalystNotePreviewOut,
    AnalystNotePublishIn,
    AnalystNotePublishOut,
    AnalystNoteSearchIn,
)


class AnalystNoteMgr:
    """Manages requests for Recorded Future analyst notes."""

    def __init__(self, rf_token: str = None):
        """Initializes the AnalystNoteMgr object.

        Args:
            rf_token (str, optional): Recorded Future API token. Defaults to None
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    def search(
        self,
        published: Optional[str] = None,
        entity: Optional[str] = None,
        author: Optional[str] = None,
        title: Optional[str] = None,
        topic: Optional[Union[str, list]] = None,
        label: Optional[str] = None,
        source: Optional[str] = None,
        serialization: Optional[str] = None,
        tagged_text: Optional[bool] = None,
        max_results: Optional[int] = Field(ge=1, le=1000, default=DEFAULT_LIMIT),
        notes_per_page: Optional[int] = Field(ge=1, le=1000, default=NOTES_PER_PAGE),
    ) -> list[AnalystNote]:
        """Execute a search for the analyst notes based on the parameters provided. Every parameter
        that has not been set up will be discarded.
        If more than one topic is specified, a search for each topic is executed and the
        AnalystNotes will be deduplicated.

        ``max_results`` is the maximum number of references, not notes.

        Endpoint:
            ``/analystnote/search``

        Args:
           published (str): Notes published after this date. Defaults to -1d.
           entity (str): Notes referring entity, RF ID.
           author (str): Notes by author, RF ID.
           title (str): Notes by title.
           topic (Union[str, list]): Notes by topic, RF ID.
           label (str): Notes by label, by name.
           source (str): source of note.
           tagged_text (bool): Should text contain tags. Defaults to False.
           serialization (str): Entity serializer (id, min, full, raw).
           max_results (int): Maximum number of references (not notes), at most 1000. Default 10.
           notes_per_page (int): Number of notes for each paged request.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            AnalystNoteSearchError: if API error occurs.

        Returns:
            List[AnalystNote]: List of deduplicated AnalystNote objects.
        """
        responses = []
        topic = None if topic == [] else topic
        data = {
            'published': published,
            'entity': entity,
            'author': author,
            'title': title,
            'topic': topic,
            'label': label,
            'source': source,
            'serialization': serialization,
            'taggedText': tagged_text,
            'limit': min(max_results, notes_per_page),
        }
        data = {key: val for key, val in data.items() if val is not None}

        max_results = DEFAULT_LIMIT if max_results is None else max_results

        responses = []
        if isinstance(topic, list) and len(topic):
            for t in topic:
                data['topic'] = t
                responses.append(self._search(data, max_results))
            return list(set(chain.from_iterable(responses)))

        return list(set(self._search(data, max_results)))

    @debug_call
    @validate_call
    @connection_exceptions(
        ignore_status_code=[404],
        exception_to_raise=AnalystNoteLookupError,
    )
    def lookup(
        self, note_id: str, tagged_text: bool = False, serialization: str = 'full'
    ) -> AnalystNote:
        """Lookup an analyst note by ID.

        Endpoint:
            ``/analystnote/lookup/{note_id}``

        Args:
           note_id (str): The ID of the analyst note to lookup
           tagged_text (bool): Add RF IDs to note entities, default to False.
           serialization (str): Serialization type of payload. Default to full.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            AnalystNoteLookupError: if API error occurs.

        Returns:
            AnalystNote: Requested note.
        """
        if not note_id.startswith('doc:'):
            note_id = f'doc:{note_id}'

        data = {'tagged_text': tagged_text, 'serialization': serialization}
        self.log.info(f'Looking up analyst note: {note_id}')
        response = self.rf_client.request(
            'post', EP_ANALYST_NOTE_LOOKUP.format(note_id), data=data
        ).json()
        return AnalystNote.model_validate(response)

    @debug_call
    @validate_call
    @connection_exceptions(
        ignore_status_code=[404], exception_to_raise=AnalystNoteDeleteError, on_ignore_return=False
    )
    def delete(self, note_id: str) -> bool:
        """Delete Analyst Note.

        Endpoint:
            ``/analystnote/delete/{note_id}``

        Args:
            note_id (str): The ID of the note to delete

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            AnalystNoteDeleteError: if connection error occurs.

        Returns:
            Union[bool, None]: True if delete ok else False
        """
        if not note_id.startswith('doc:'):
            note_id = f'doc:{note_id}'

        self.log.info(f'Deleting note {note_id}')
        self.rf_client.request('delete', url=EP_ANALYST_NOTE_DELETE.format(note_id))
        return True

    @debug_call
    @validate_call
    @connection_exceptions(
        ignore_status_code=[404],
        exception_to_raise=AnalystNotePreviewError,
    )
    def preview(
        self,
        title: str,
        text: str,
        published: Optional[str] = None,
        topic: Union[str, list[str], None] = None,
        context_entities: Optional[list[str]] = None,
        note_entities: Optional[list[str]] = None,
        validation_urls: Optional[list[str]] = None,
        source: Optional[str] = None,
    ) -> AnalystNotePreviewOut:
        """Preview of the AnalystNote. It does not create a note, it just return how the note
        will look like.

        Endpoint:
            ``/analystnote/preview``

        Args:
            title (str): title of the note.
            text (str): text of the note.
            published (Optional[str]): date when the note was published.
            topic (Optional[List[str]]): topic of the note.
            context_entities (Optional[List[str]]): context entities of the note.
            note_entities (Optional[List[str]]): note entities of the note.
            source (Optional[List[str]]): source of the note.
            validation_urls (Optional[List[str]]): validation urls of the note.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            AnalystNotePreviewRequest: if connection error occurs.

        Returns:
            AnalystNotePreviewOut: note that will be created.
        """
        if topic:
            topic = topic if isinstance(topic, list) else [topic]

        data = {
            'attributes': {
                'title': title,
                'text': text,
                'published': published,
                'context_entities': context_entities,
                'note_entities': note_entities,
                'validation_urls': validation_urls,
                'topic': topic,
            },
            'source': source,
        }

        note = AnalystNotePreviewIn.model_validate(data)
        self.log.info(f'Previewing note: {note.attributes.title}')
        resp = self.rf_client.request('post', EP_ANALYST_NOTE_PREVIEW, data=note.json()).json()

        return AnalystNotePreviewOut.model_validate(resp)

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[404], exception_to_raise=AnalystNotePublishError)
    def publish(
        self,
        title: str,
        text: str,
        published: Optional[str] = None,
        topic: Union[str, list[str], None] = None,
        context_entities: Optional[list[str]] = None,
        note_entities: Optional[list[str]] = None,
        validation_urls: Optional[list[str]] = None,
        source: Optional[str] = None,
        note_id: Optional[str] = None,
    ) -> AnalystNotePublishOut:
        """Publish of data. This method does create a note and returns the id.

        Endpoint:
            ``/analystnote/publish``

        Args:
            title (str): title of the note.
            text (str): text of the note.
            published (Optional[str]): date when the note was published.
            topic (Optional[List[str]]): topic of the note.
            context_entities (Optional[List[str]]): context entities of the note.
            note_entities (Optional[List[str]]): note entities of the note.
            entities (Optional[List[str]]): entities of the note.
            validation_urls (Optional[List[str]]): validation urls of the note.
            note_id (Optional[str]): id of the note, use if you want to modify an existing note.
            source (Optional[str]): source of the note.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            AnalystNotePublishError: if connection error occurs.

        Returns:
            AnalystNotePublishOut: published note
        """
        if topic:
            topic = topic if isinstance(topic, list) else [topic]

        data = {
            'attributes': {
                'title': title,
                'text': text,
                'published': published,
                'context_entities': context_entities,
                'note_entities': note_entities,
                'validation_urls': validation_urls,
                'topic': topic,
            },
            'source': source,
            'note_id': note_id,
        }
        note = AnalystNotePublishIn.model_validate(data)
        self.log.info(f'Publishing note: {note.attributes.title}')
        resp = self.rf_client.request('post', EP_ANALYST_NOTE_PUBLISH, data=note.json()).json()
        return AnalystNotePublishOut.model_validate(resp)

    @debug_call
    @validate_call
    @connection_exceptions(
        ignore_status_code=[404],
        exception_to_raise=AnalystNoteAttachmentError,
        on_ignore_return=(b'', None),
    )
    def fetch_attachment(self, note_id: str) -> tuple[bytes, str]:
        """Get Analyst Note Attachment. To work with the attachment is the same no matter the ext.


        Example:
            Fetch and save an attachment from an Analyst Note:

            .. code-block:: python
                :linenos:

                from psengine.analyst_notes import save_attachment

                # note with pdf attachment
                attachment, extension = note_mgr.fetch_attachment('tPtLVw')
                save_attachment('tPtLVw', attachment, extension)

                # note with yar attachment
                attachment, extension = note_mgr.fetch_attachment('oJeqDP')
                save_attachment('oJeqDP', attachment, extension)


        Endpoint:
            ``/analystnote/attachment/{note_id}``


        Args:
            note_id (str): id of the note

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            AnalystNoteAttachmentError: if connection error occurs.

        Returns:
            Tuple[bytes, str]: content of the attachment in bytes and extension of the file

        """
        if not note_id.startswith('doc:'):
            note_id = f'doc:{note_id}'

        self.log.info(f"Looking up analyst note's {note_id} attachment")
        response = self.rf_client.request('get', EP_ANALYST_NOTE_ATTACHMENT.format(note_id))

        content_disp = response.headers.get('Content-Disposition')
        ext = re.findall(r'filename=.*\.(\w+)', content_disp)

        ext = ext[-1] if ext else ''

        return response.content, ext

    @connection_exceptions(ignore_status_code=[404], exception_to_raise=AnalystNoteSearchError)
    def _search(self, data: dict, max_results: int) -> list[AnalystNote]:
        """Search for Analayst notes.

        Raises:
            AnalystNoteSearchError: if connection error occurs.

        Return:
            dict: json data for 'data.results' for the analayst notes found by the search.
        """
        self.log.info(f'Searching analyst notes with query: {data}')
        search_data = AnalystNoteSearchIn.model_validate(data)
        response = self.rf_client.request_paged(
            method='post',
            url=EP_ANALYST_NOTE_SEARCH,
            data=search_data.json(),
            offset_key='from',
            results_path='data',
            max_results=max_results,
        )

        return [AnalystNote.model_validate(d) for d in response]

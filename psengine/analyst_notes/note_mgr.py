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
from typing import Annotated, Optional, Union

from pydantic import Field, validate_call
from typing_extensions import Doc

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
        """Initializes the `AnalystNoteMgr` object.

        Args:
            rf_token (str, optional): Recorded Future API token.
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    def search(
        self,
        published: Annotated[Optional[str], Doc('Notes published after a date.')] = None,
        entity: Annotated[Optional[str], Doc('An entity the note refers to, RF ID.')] = None,
        author: Annotated[Optional[str], Doc('An author of the note, RF ID.')] = None,
        title: Annotated[Optional[str], Doc('A title of the note.')] = None,
        topic: Annotated[Optional[Union[str, list]], Doc('A topic of the note, RF ID.')] = None,
        label: Annotated[Optional[str], Doc('A label of the note, by name.')] = None,
        source: Annotated[Optional[str], Doc('The source of the note.')] = None,
        serialization: Annotated[
            Optional[str], Doc('An entity serializer (id, min, full, raw).')
        ] = None,
        tagged_text: Annotated[Optional[bool], Doc('Should the text contain tags.')] = None,
        max_results: Annotated[
            Optional[int],
            Doc('The maximum number of references (not notes), max 1000.'),
        ] = Field(ge=1, le=1000, default=DEFAULT_LIMIT),
        notes_per_page: Annotated[
            Optional[int], Doc('The number of notes for each paged request.')
        ] = Field(ge=1, le=1000, default=NOTES_PER_PAGE),
    ) -> Annotated[list[AnalystNote], Doc('A list of deduplicated AnalystNote objects.')]:
        """Execute a search for the analyst notes based on the parameters provided.
        Every parameter that has not been set up will be discarded.

        If more than one topic is specified, a search for each topic is executed and the
        `AnalystNotes` will be deduplicated.

        `max_results` is the maximum number of references, not notes.

        Endpoint:
            `/analystnote/search`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            AnalystNoteSearchError: If API error occurs.
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
    @connection_exceptions(ignore_status_code=[404], exception_to_raise=AnalystNoteLookupError)
    def lookup(
        self,
        note_id: Annotated[str, Doc('The ID of the analyst note to look up.')],
        tagged_text: Annotated[bool, Doc('Add RF IDs to the note entities.')] = False,
        serialization: Annotated[str, Doc('The serialization type of the payload.')] = 'full',
    ) -> Annotated[AnalystNote, Doc('The requested note.')]:
        """Look up an analyst note by ID.

        Endpoint:
            `/analystnote/lookup/{note_id}`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            AnalystNoteLookupError: If API error occurs.
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
    def delete(
        self, note_id: Annotated[str, Doc('The ID of the analyst note to look up.')]
    ) -> Annotated[bool, Doc('True if delete is successful, False otherwise.')]:
        """Delete an analyst note.

        Endpoint:
            `/analystnote/delete/{note_id}`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            AnalystNoteDeleteError: If connection error occurs.
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
        title: Annotated[str, Doc('The title of the note.')],
        text: Annotated[str, Doc('The text of the note.')],
        published: Annotated[Optional[str], Doc('The date when the note was published.')] = None,
        topic: Annotated[Union[str, list[str], None], Doc('The topic of the note.')] = None,
        context_entities: Annotated[
            Optional[list[str]], Doc('The context entities of the note.')
        ] = None,
        note_entities: Annotated[Optional[list[str]], Doc('The note entities of the note.')] = None,
        validation_urls: Annotated[
            Optional[list[str]], Doc('The validation URLs of the note.')
        ] = None,
        source: Annotated[Optional[str], Doc('The source of the note.')] = None,
    ) -> Annotated[AnalystNotePreviewOut, Doc('The note that will be created.')]:
        """Preview of the AnalystNote. It does not create a note; it just returns how the note
        will look.

        Endpoint:
            `/analystnote/preview`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            AnalystNotePreviewRequest: If connection error occurs.
        """
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
        title: Annotated[str, Doc('The title of the note.')],
        text: Annotated[str, Doc('The text of the note.')],
        published: Annotated[Optional[str], Doc('The date when the note was published.')] = None,
        topic: Annotated[Union[str, list[str], None], Doc('The topic of the note.')] = None,
        context_entities: Annotated[
            Optional[list[str]], Doc('The context entities of the note.')
        ] = None,
        note_entities: Annotated[Optional[list[str]], Doc('The note entities of the note.')] = None,
        validation_urls: Annotated[
            Optional[list[str]], Doc('The validation URLs of the note.')
        ] = None,
        source: Annotated[Optional[str], Doc('The source of the note.')] = None,
        note_id: Annotated[
            Optional[str], Doc('The ID of the note. Use if you want to modify an existing note.')
        ] = None,
    ) -> Annotated[AnalystNotePublishOut, Doc('The published note.')]:
        """Publish data. This method creates a note and returns its ID.

        Endpoint:
            `/analystnote/publish`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            AnalystNotePublishError: If connection error occurs.
        """
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
    def fetch_attachment(
        self,
        note_id: Annotated[str, Doc('The ID of the note.')],
    ) -> Annotated[
        tuple[bytes, str],
        Doc('A tuple containing the file content (bytes) and the file extension (str).'),
    ]:
        """Get an analyst note attachment.

        To work with the attachment is the same regardless of the file extension.

        Endpoint:
            `/analystnote/attachment/{note_id}`

        Example:
            Fetch and save an attachment from an analyst note:

            ```python
            from pathlib import Path

            from psengine.analyst_notes import AnalystNoteMgr, save_attachment

            OUTPUT_DIR = Path(__file__).parent / 'attachments'
            OUTPUT_DIR.mkdir(exist_ok=True)

            # Note with PDF attachment
            attachment, extension = note_mgr.fetch_attachment('tPtLVw')
            save_attachment('tPtLVw', attachment, extension, OUTPUT_DIR)

            # Note with YAR attachment
            attachment, extension = note_mgr.fetch_attachment('oJeqDP')
            save_attachment('oJeqDP', attachment, extension, OUTPUT_DIR)

            ```

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            AnalystNoteAttachmentError: If connection error occurs.
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
            AnalystNoteSearchError: If connection error occurs.
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

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
from typing import Annotated, Optional

from pydantic import validate_call
from typing_extensions import Doc

from psengine import RFClient

from ..common_models import IdName
from ..helpers import connection_exceptions, debug_call
from .constants import (
    EP_LINKS_METADATA_ENTITIES,
    EP_LINKS_METADATA_EVENTS,
    EP_LINKS_METADATA_SECTIONS,
    EP_LINKS_SEARCH,
)
from .errors import LinksMetadataError, LinksSearchError, LinksValidationError
from .requests import LinksFilterObjects, LinksLimitsObjects, LinksSearchIn
from .response import (
    LinksSearchResponse,
    MetadataEntityTypesResponse,
    MetadataEvent,
    MetadataEventsResponse,
    MetadataSection,
    MetadataSectionsResponse,
)


class LinksMgr:
    """Manager for interacting with the Recorded Future Links API."""

    def __init__(
        self,
        rf_token: Annotated[Optional[str], Doc('Recorded Future API token.')] = None,
    ):
        """Initialize the `LinksMgr` object."""
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

        # Cache variables for lazy loading (Lean caches)
        self._cache_sections: Optional[set[str]] = None
        self._cache_entity_types: Optional[set[str]] = None
        self._cache_events: Optional[set[str]] = None

    def _validate_filters(self, filters: LinksFilterObjects) -> None:
        """Domain validation for search filters against live caches."""
        # Section validation
        if filters.sections:
            invalid_sections = [s for s in filters.sections if s not in self.valid_sections]
            if invalid_sections:
                raise LinksValidationError(f'Invalid section IDs: {invalid_sections}')

        # Entity type validation
        if filters.entity_types:
            invalid_types = [t for t in filters.entity_types if t not in self.valid_entity_types]
            if invalid_types:
                raise LinksValidationError(f'Invalid entity types: {invalid_types}')

        # Source validation
        valid_sources = ['technical', 'insikt']
        if filters.sources:
            for source in filters.sources:
                if source not in valid_sources:
                    raise LinksValidationError(
                        f'Invalid source: {source}. Valid sources are: {", ".join(valid_sources)}'
                    )

        # Timeframe validation done with Pydantic

        # Event validation
        if filters.technical and filters.technical.events:
            invalid_events = [e for e in filters.technical.events if e not in self.valid_events]
            if invalid_events:
                raise LinksValidationError(f'Invalid event IDs: {invalid_events}')

    @property
    @debug_call
    def valid_sections(self) -> set[str]:
        """Lazy load and return a set of valid section IDs for validation."""
        if self._cache_sections is None:
            self.log.debug('Populating sections cache.')
            sections = self.list_sections()
            self._cache_sections = {item.id_ for item in sections}
        if self._cache_sections is None:
            raise RuntimeError('Sections cache failed to populate.')
        return self._cache_sections

    @property
    @debug_call
    def valid_events(self) -> set[str]:
        """Lazy load and return a set of valid events for validation."""
        if self._cache_events is None:
            self.log.debug('Populating events cache.')
            events = self.list_events()
            self._cache_events = {item.id_ for item in events}
        if self._cache_events is None:
            raise RuntimeError('Events cache failed to populate.')
        return self._cache_events

    @property
    @debug_call
    def valid_entity_types(self) -> set[str]:
        """Lazy load and return a set of valid entity types for validation."""
        if self._cache_entity_types is None:
            self.log.debug('Populating entities cache.')
            entities = self.list_entity_types()
            self._cache_entity_types = {item.id_ for item in entities}
        if self._cache_entity_types is None:
            raise RuntimeError('Entity types cache failed to populate.')
        return self._cache_entity_types

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=LinksMetadataError)
    def list_sections(self) -> list[MetadataSection]:
        """List all valid sections available for Link searches.

        Returns:
            list[MetadataSection]: Full objects containing id, name, and description.

        Raises:
            LinksMetadataError: If the API request or validation fails.
        """
        self.log.debug(f'Fetching metadata from {EP_LINKS_METADATA_SECTIONS}')

        response = self.rf_client.request(method='GET', url=EP_LINKS_METADATA_SECTIONS)

        validated = MetadataSectionsResponse.model_validate(response.json())
        return validated.data

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=LinksMetadataError)
    def list_events(self) -> list[MetadataEvent]:
        """List all valid events available for Link searches."""
        self.log.debug(f'Fetching metadata from {EP_LINKS_METADATA_EVENTS}')

        response = self.rf_client.request(method='GET', url=EP_LINKS_METADATA_EVENTS)

        validated = MetadataEventsResponse.model_validate(response.json())
        return validated.data

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=LinksMetadataError)
    def list_entity_types(self) -> list[IdName]:
        """List all supported entity types for Link Searches."""
        self.log.debug(f'Fetching metadata from {EP_LINKS_METADATA_ENTITIES}')

        response = self.rf_client.request(method='GET', url=EP_LINKS_METADATA_ENTITIES)

        validated = MetadataEntityTypesResponse.model_validate(response.json())
        return validated.data

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=LinksSearchError)
    def search(
        self,
        entities: Annotated[
            list[str], Doc('List of Recorded Future entity IDs to search for links against')
        ],
        filters: Annotated[
            Optional[LinksFilterObjects], Doc('Filter objects for the search')
        ] = None,
        limits: Annotated[
            Optional[LinksLimitsObjects], Doc('Limits objects for the search')
        ] = None,
    ) -> Annotated[LinksSearchResponse, Doc('The structured search results')]:
        """Perform a Link search using the provided parameters."""
        if filters:
            self._validate_filters(filters)

        payload = LinksSearchIn(entities=entities, filters=filters, limits=limits)

        self.log.info(f'Executing links search for {len(entities)} entities.')
        response = self.rf_client.request(
            method='POST',
            url=EP_LINKS_SEARCH,
            data=payload.model_dump(exclude_none=True, by_alias=True),
        )

        return LinksSearchResponse.model_validate(response.json())

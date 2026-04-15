import logging
from typing import Annotated, Optional, Union

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
from .errors import LinksMetadataError, LinksSearchError
from .requests import LinksFilterObjects, LinksLimitsObjects, LinksSearchIn
from .response import (
    MetadataEntityTypesResponse,
    LinksSearchResponse,
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

    @property
    @debug_call
    def valid_sections(self) -> set[str]:
        """Lazy load and return a set of valid section IDs for validation."""
        if self._cache_sections is None:
            self.log.debug('Populating sections cache.')
            sections = self.list_sections()
            self._cache_sections = {item.id_ for item in sections}
        assert self._cache_sections is not None
        return self._cache_sections

    @property
    @debug_call
    def valid_events(self) -> set[str]:
        """Lazy load and return a set of valid events for validation"""
        if self._cache_events is None:
            self.log.debug('Populating events cache.')
            events = self.list_events()
            self._cache_events = {item.id_ for item in events}
        assert self._cache_events is not None
        return self._cache_events

    @property
    @debug_call
    def valid_entity_types(self) -> set[str]:
        if self._cache_entity_types is None:
            self.log.debug('Populating entities cache.')
            entities = self.list_entity_types()
            self._cache_entity_types = {item.id_ for item in entities}
        assert self._cache_entity_types is not None
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
        """List all supported entity types for Link Searches"""
        self.log.debug(f'Fetching metadata from {EP_LINKS_METADATA_ENTITIES}')

        response = self.rf_client.request(method='GET', url=EP_LINKS_METADATA_ENTITIES)

        validated = MetadataEntityTypesResponse.model_validate(response.json())
        return validated.data
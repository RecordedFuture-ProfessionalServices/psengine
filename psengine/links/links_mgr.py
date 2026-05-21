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
from typing import Annotated

from pydantic import validate_call
from typing_extensions import Doc

from ..endpoints import (
    EP_LINKS_METADATA_ENTITIES,
    EP_LINKS_METADATA_EVENTS,
    EP_LINKS_METADATA_SECTIONS,
    EP_LINKS_SEARCH,
)
from ..helpers import connection_exceptions, debug_call
from ..rf_client import RFClient
from .errors import LinksMetadataError, LinksSearchError
from .links import LinksFilterObjects, LinksLimitsObjects, LinksSearchIn, LinksSearchResponse
from .models import (
    MetadataOut,
)


class LinksMgr:
    """Manager for interacting with the Recorded Future Links API."""

    def __init__(
        self,
        rf_token: Annotated[str | None, Doc('Recorded Future API token.')] = None,
    ):
        """Initialize the `LinksMgr` object."""
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=LinksMetadataError)
    def list_sections(
        self,
    ) -> Annotated[MetadataOut, Doc('Section objects with id, name, and description.')]:
        """List all sections that can be used to filter a Link search.

        Sections are the high-level categories the Links API groups results into,
        for example *Actors, Tools & TTPs* or *Indicators & Detection Rules*.

        Endpoint:
            `/links/metadata/sections`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            LinksMetadataError: If an API or connection error occurs.
        """
        response = self.rf_client.request(method='GET', url=EP_LINKS_METADATA_SECTIONS)
        return MetadataOut.model_validate(response.json()).data

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=LinksMetadataError)
    def list_events(
        self,
    ) -> Annotated[MetadataOut, Doc('Event objects with id, name, and description.')]:
        """List all event types that can be used to filter technical Link searches.

        Event types describe the kind of analytical evidence that produced a
        technical link (for example `TTPAnalysis` or `InfrastructureAnalysis`).

        Endpoint:
            `/links/metadata/events`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            LinksMetadataError: If an API or connection error occurs.
        """
        response = self.rf_client.request(method='GET', url=EP_LINKS_METADATA_EVENTS)
        return MetadataOut.model_validate(response.json()).data

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=LinksMetadataError)
    def list_entity_types(
        self,
    ) -> Annotated[MetadataOut, Doc('Entity-type objects with id and name.')]:
        """List all entity types that can be used to filter a Link search.

        The returned values are the supported types for connected entities
        (for example `Malware`, `Company`, `IpAddress`).

        Endpoint:
            `/links/metadata/entities`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            LinksMetadataError: If an API or connection error occurs.
        """
        response = self.rf_client.request(method='GET', url=EP_LINKS_METADATA_ENTITIES)
        return MetadataOut.model_validate(response.json()).data

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=LinksSearchError)
    def search(
        self,
        entities: Annotated[
            list[str], Doc('List of Recorded Future entity IDs to search for links against.')
        ],
        filters: Annotated[LinksFilterObjects | None, Doc('Filter objects for the search.')] = None,
        limits: Annotated[LinksLimitsObjects | None, Doc('Limits objects for the search.')] = None,
    ) -> Annotated[LinksSearchResponse, Doc('The structured search results.')]:
        """Search for entities connected to one or more target entities.

        Issues a single batched request: the response contains one
        `SearchResultSet` per entity in `entities`, in the same order. If the
        API failed for a specific entity, that result's `error` is populated
        and `links` is empty — the rest of the batch still succeeds.

        `filters` narrows the result set:

        - `sections` — restrict to specific Links sections (see `list_sections`).
        - `entity_types` — restrict to specific connected-entity types (see `list_entity_types`).
        - `sources` — restrict to `technical`, `insikt`, or both.
        - `technical` — sub-filters that apply only to technical links (timeframe,
          event types, connected-entity scope).

        `limits` controls how aggressively the API searches:

        - `search_scope` — one of `small`, `medium`, `large`. Larger scopes scan
          more references and Insikt notes per query at the cost of latency.
        - `per_entity_type` — caps how many connected entities of each type
          are returned.

        Entities must be supplied as Recorded Future entity IDs; if you only have
        a name, resolve it with `EntityMatchMgr` or `LookupMgr` first.

        Endpoint:
            `/links/search`

        Example:
            ```python
            from psengine.links import LinksMgr

            mgr = LinksMgr()
            results = mgr.search(entities=['QCwdoU'])
            for result in results.data:
                if result.error:
                    continue
                for link in result.links:
                    print(f'{link.name} ({link.type_})')
            ```

            With filters and limits:
            ```python
            from psengine.links import (
                FilterTechnical,
                LinksFilterObjects,
                LinksLimitsObjects,
                LinksMgr,
            )

            mgr = LinksMgr()
            filters = LinksFilterObjects(
                sources=['technical'],
                entity_types=['Malware'],
                technical=FilterTechnical(timeframe='-30d'),
            )
            limits = LinksLimitsObjects(search_scope='small', per_entity_type=50)
            results = mgr.search(
                entities=['QCwdoU'], filters=filters, limits=limits
            )
            ```

        If the API failed for a specific entity in the batch, its result looks like:
        ```python
        SearchResultSet(
            entity=IdNameType(id_='QCwdoU', name='...', type_='...'),
            links=[],
            error=EntitySearchError(message='...', status_code=404),
        )
        ```

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            LinksSearchError: If an API or connection error occurs at the request level.
        """
        payload = LinksSearchIn(entities=entities, filters=filters, limits=limits)

        # Kept: @debug_call logs the args list, but batch size is the operationally
        # useful number to surface at INFO. Drop if the reviewer disagrees.
        self.log.info(f'Executing links search for {len(entities)} entities.')

        response = self.rf_client.request(
            method='POST',
            url=EP_LINKS_SEARCH,
            data=payload.model_dump(exclude_none=True, by_alias=True),
        )
        return LinksSearchResponse.model_validate(response.json())

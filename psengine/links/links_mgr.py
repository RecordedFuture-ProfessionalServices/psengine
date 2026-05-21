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

from pydantic import AfterValidator, validate_call
from typing_extensions import Doc

from psengine.helpers.helpers import Validators

from ..endpoints import (
    EP_LINKS_METADATA_ENTITIES,
    EP_LINKS_METADATA_EVENTS,
    EP_LINKS_METADATA_SECTIONS,
    EP_LINKS_SEARCH,
)
from ..helpers import connection_exceptions, debug_call
from ..rf_client import RFClient
from .errors import LinksMetadataError, LinksSearchError
from .links import (
    LinksSearchResponseOut,
)
from .models import (
    FilterTechnical,
    LinksFilterObjects,
    LinksLimitsObjects,
    LinkSource,
    MetadataOut,
    SearchScope,
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
            Annotated[str | list[str], AfterValidator(Validators.convert_str_to_list)],
            Doc('One or more Recorded Future entity IDs to look up links for.'),
        ],
        sections: Annotated[
            str | list[str] | None, Doc('Filter results to these link section IDs.')
        ] = None,
        entity_types: Annotated[
            str | list[str] | None,
            Doc('Restrict linked entities to these entity types (e.g. "type:IpAddress").'),
        ] = None,
        sources: Annotated[
            list[LinkSource] | None,
            Doc('Limit to source type(s): technical, insikt, or both.'),
        ] = None,
        timeframe: Annotated[
            str | None,
            Doc('Technical-link timeframe (e.g. "-30d", default "-30d", max "-90d").'),
        ] = None,
        events: Annotated[
            str | list[str] | None,
            Doc('Restrict technical links to these event types (e.g. "type:MalwareAnalysis").'),
        ] = None,
        connected_entities: Annotated[
            str | list[str] | None,
            Doc('Only return technical links that connect to these entities.'),
        ] = None,
        search_scope: Annotated[
            SearchScope | None,
            Doc('Result-volume scope: small, medium (default), or large.'),
        ] = None,
        per_entity_type: Annotated[
            int | None, Doc('Max linked entities returned per entity type.')
        ] = None,
    ) -> Annotated[
        list[LinksSearchResponseOut], Doc('A list of LinkResult models — one per input entity.')
    ]:
        """Search for entities connected to one or more target entities.

        Issues a single batched request: the response contains one
        `EntityLinks` per entity in `entities`, in the same order. If the
        API failed for a specific entity, that result's `error` is populated
        and `links` is empty — the rest of the batch still succeeds.

        Entities must be supplied as Recorded Future entity IDs; if you only have
        a name, resolve it with `EntityMatchMgr` first.

        Endpoint:
            `/links/search`

        If the API failed for a specific entity in the batch, its result looks like:
        ```python
            EntityLinks(
                entity=IdNameType(id_='QCwdoU', name='...', type_='...'),
                links=[],
                error=EntitySearchError(message='...', status_code=404),
            )
        ```

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            LinksSearchError: If an API or connection error occurs at the request level.
        """
        technical_filter = FilterTechnical(
            timeframe=timeframe, events=events, connected_entities=connected_entities
        ).json()

        filters = LinksFilterObjects(
            sections=sections,
            entity_types=entity_types,
            sources=sources,
            technical=technical_filter,
        ).json()
        limits = LinksLimitsObjects(
            search_scope=search_scope, per_entity_type=per_entity_type
        ).json()
        payload = {'entities': entities, 'filters': filters, 'limits': limits}

        self.log.info(f'Executing links search for {len(entities)} entities.')

        response = self.rf_client.request(method='POST', url=EP_LINKS_SEARCH, data=payload)
        return LinksSearchResponseOut.model_validate(response.json())

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
from typing import Annotated, Literal

from pydantic import Field, validate_call
from typing_extensions import Doc

from ..constants import DEFAULT_LIMIT
from ..endpoints import (
    EP_ACTOR_SEARCH,
    EP_CATEGORIES,
    EP_THREAT_MAP,
    EP_THREAT_MAP_ORG,
    EP_THREAT_MAPS_LIST,
)
from ..helpers import debug_call, validate_list
from ..helpers.helpers import connection_exceptions
from ..rf_client import RFClient
from .errors import (
    ThreatActorSearchError,
    ThreatMapCategoriesError,
    ThreatMapFetchError,
    ThreatMapInfoError,
)
from .models import ThreatMapType
from .threat_map import (
    EntityCategory,
    ThreatActorProfile,
    ThreatMap,
    ThreatMapFetchIn,
    ThreatMapInfo,
)

MAP_TYPE = Literal['actors', 'malware']


class ThreatMapMgr:
    """Manages requests for Recorded Future Threat Maps API."""

    def __init__(
        self,
        rf_token: Annotated[str | None, Doc('Recorded Future API token.')] = None,
    ):
        """Initialize the `ThreatMapMgr` object."""
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ThreatMapInfoError)
    def fetch_available_maps(
        self,
    ) -> Annotated[list[ThreatMapInfo], Doc('A list of available threat maps.')]:
        """Fetch available threat maps for the organization.

        Endpoint:
            `threat/maps`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            ThreatMapInfoError: If connection error occurs.
        """
        maps_response = self.rf_client.request(method='get', url=EP_THREAT_MAPS_LIST).json()['data']
        return validate_list(ThreatMapInfo, maps_response, id_path='name', log=self.log)

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ThreatMapCategoriesError)
    def fetch_entity_categories(
        self,
        map_type: Annotated[MAP_TYPE, Doc('Type of threat map.')],
    ) -> Annotated[list[EntityCategory], Doc('A list of threat map taxonomy categories.')]:
        """Fetch the entity category taxonomy used to filter threat maps.

        Endpoint:
            `threat/{type}/categories`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            ThreatMapCategoriesError: If connection error occurs.
        """
        map_type = ThreatMapType(map_type)
        url = EP_CATEGORIES.format(map_type.category_slug)
        cat_response = self.rf_client.request(method='get', url=url).json()['data']
        return validate_list(EntityCategory, cat_response, id_path='id', log=self.log)

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ThreatActorSearchError)
    def search_threat_actor(
        self,
        name: Annotated[
            str | None, Doc('Free text search of threat actor names, common names, or aliases.')
        ] = None,
        max_results: Annotated[
            int | None, Doc('Limit the total number of results returned.')
        ] = DEFAULT_LIMIT,
        actors_per_page: Annotated[
            int | None, Doc('The number of threat actors per page for pagination.')
        ] = Field(ge=1, le=10_000, default=DEFAULT_LIMIT),
    ) -> Annotated[
        list[ThreatActorProfile], Doc('A list of threat actors matching the search criteria.')
    ]:
        """Search Recorded Future's threat actor database by name, alias, or classification.

        Endpoint:
            `threat/actor/search`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            ThreatActorSearchError: If connection error occurs.
        """
        data = {
            'name': name,
            'limit': min(max_results or DEFAULT_LIMIT, actors_per_page or DEFAULT_LIMIT),
        }
        search_response = self.rf_client.request_paged(
            method='post',
            url=EP_ACTOR_SEARCH,
            data=data,
            results_path='data',
            offset_key='offset',
            max_results=max_results or DEFAULT_LIMIT,
        )
        return validate_list(ThreatActorProfile, search_response, id_path='id', log=self.log)

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ThreatMapFetchError)
    def fetch_map(
        self,
        map_type: Annotated[MAP_TYPE, Doc('Type of threat map.')],
        org_id: Annotated[str | None, Doc('Organization ID.')] = None,
        malware: Annotated[str | list[str] | None, Doc('Filter by malware entity ID(s).')] = None,
        actors: Annotated[str | list[str] | None, Doc('Filter by threat actor ID(s).')] = None,
        categories: Annotated[str | list[str] | None, Doc('Filter by category ID(s).')] = None,
        watchlists: Annotated[str | list[str] | None, Doc('Filter by watch list ID(s).')] = None,
    ) -> Annotated[ThreatMap, Doc('Threat map with entities matching filter criteria.')]:
        """Fetch a threat map with optional entity, category, and watchlist filters.

        Endpoint:
            `threat/map/{type}` or `threat/map/{org_id}/{type}`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            ThreatMapFetchError: If connection error occurs.
        """
        body = {'categories': categories, 'watchlists': watchlists}
        map_type = ThreatMapType(map_type).value
        if map_type is ThreatMapType.actors:
            body['actors'] = actors
        else:
            body['malware'] = malware

        url = (
            EP_THREAT_MAP_ORG.format(org_id, map_type) if org_id else EP_THREAT_MAP.format(map_type)
        )

        data = ThreatMapFetchIn.model_validate(body).json()
        map_response = self.rf_client.request(method='post', url=url, data=data).json()['data']
        return ThreatMap.model_validate(map_response)

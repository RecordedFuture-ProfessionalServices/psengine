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
from typing import Annotated, Optional, Union
from urllib.parse import quote

from pydantic import Field, validate_call

from ..common_models import IdNameType
from ..constants import DEFAULT_LIMIT, DEFAULT_MAX_WORKERS
from ..endpoints import EP_ENTITY_LOOKUP, EP_ENTITY_MATCH
from ..helpers import MultiThreadingHelper, connection_exceptions, debug_call
from ..rf_client import RFClient
from .entity_match import EntityLookup, EntityMatchIn, ResolvedEntity
from .errors import MatchApiError


class EntityMatchMgr:
    """Manages requests for Recorded Future Entity Match API."""

    def __init__(self, rf_token: str = None):
        """Initializes the EntityMatchMgr object.

        Args:
            rf_token (str, optional): Recorded Future API token. Defaults to None
        """
        self.log = logging.getLogger(__name__)
        self.rf_client = RFClient(api_token=rf_token) if rf_token else RFClient()

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=MatchApiError)
    def match(
        self,
        entity_name: str,
        entity_type: Optional[Union[list, str]] = None,
        limit: int = DEFAULT_LIMIT,
    ) -> list[ResolvedEntity]:
        """Matches a text string on entity match API.

        Endpoint:
            ``entity-match/match``

        Args:
            entity_name (str): name of the entity.
            entity_type (Optional[Union[list, str]): the type(s) of the entity, if known.
            limit (int, optional): maximum number of matches to return. Default to 10.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            MatchApiError: if connection error occurs.

        Returns:
            list: list of ResolvedEntity
        """
        if entity_type is not None:
            entity_type = entity_type if isinstance(entity_type, list) else [entity_type]

        request_body = EntityMatchIn(name=entity_name, type=entity_type, limit=limit)
        response = self.rf_client.request('post', EP_ENTITY_MATCH, data=request_body.json())
        response = [IdNameType.model_validate(d) for d in response.json()]
        return (
            [ResolvedEntity(entity=d.name, is_found=bool(d.id_), content=d) for d in response]
            if response
            else [ResolvedEntity(entity=entity_name, is_found=False, content='Entity ID not found')]
        )

    @debug_call
    @validate_call
    def resolve_entity_id(
        self,
        entity_name: str,
        entity_type: Optional[Annotated[str, Field(min_length=2)]] = None,
        limit: Optional[int] = DEFAULT_LIMIT,
    ) -> ResolvedEntity:
        """Resolves an entity name and type (optional) to an ID.

        Endpoint:
            ``entity-match/match``

        Args:
            entity_name (str): name of the entity.
            entity_type (Optional[str]): the type of the entity, if known.
            limit (Optional[int]): limit of results to check for matches. Default 10

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            MatchApiError: if connection error occurs.

        Returns:
            ResolvedEntity
        """
        matches = self.match(entity_name, entity_type=entity_type, limit=limit)
        if len(matches) > 1:
            exact_count = 0
            exact_match = None
            for match in matches:
                if match.entity == entity_name:
                    if entity_type is not None and match.content.type_ != entity_type:
                        continue
                    exact_match = match
                    exact_count += 1
            if (not exact_match) or exact_count > 1:
                message = f"Multiple matches found for '{entity_name}'"
                if entity_type is None:
                    message += '. No type set. Consider specifying entity type'
                else:
                    message += f" of type '{entity_type}'"
                return ResolvedEntity(entity=entity_name, is_found=False, content=message)
        else:
            return matches[0]

        return exact_match

    @debug_call
    @validate_call
    def _bulk_resolution_helper(
        self, entity: tuple[str, Optional[str]], limit: Optional[int] = DEFAULT_LIMIT
    ) -> ResolvedEntity:
        """Helper function for multithreading.

        Args:
            entity (Tuple[str, Optional[str]]): entity name and type tuple.
            limit (Optional[int]): limit of results to check for matches. Default 10

        Returns:
            ResolvedEntity: resolved entity object.
        """
        return self.resolve_entity_id(entity[0], entity[1], limit)

    @debug_call
    @validate_call
    def resolve_entity_ids(
        self,
        entities: Union[list[str], list[tuple[str, str]]],
        limit: Optional[int] = DEFAULT_LIMIT,
        max_workers: Optional[int] = DEFAULT_MAX_WORKERS,
    ) -> list[ResolvedEntity]:
        """Resolves a list of entities to IDs.

        Endpoint:
            ``entity-match/match``

        Args:
            entities (list): list of entity name strings or entity name, type tuples
            limit (Optional[int]): limit of results to return. Default 10
            max_workers (int, optional): number of workers to multithread requests.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            MatchApiError: if connection error occurs.

        Returns:
            list of ResolvedEntity objects for each entity
        """
        lookup_entities = [
            (entity, None) if isinstance(entity, str) else entity for entity in entities
        ]
        if max_workers > 1:
            results = MultiThreadingHelper.multithread_it(
                max_workers,
                self._bulk_resolution_helper,
                iterator=lookup_entities,
                limit=limit,
            )

        else:
            results = [
                self.resolve_entity_id(entity_name, entity_type, limit)
                for entity_name, entity_type in lookup_entities
            ]

        return results

    @debug_call
    @validate_call
    @connection_exceptions(ignore_status_code=[404], exception_to_raise=MatchApiError)
    def lookup(self, id_: str) -> EntityLookup:
        """Lookup a Recorded Future ID for entity details.

        Endpoint:
            ``entity-match/entity/{id}``

        Args:
            id_ (str): id to lookup.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            MatchApiError: if connection error occurs.

        Returns:
            EntityLookup object
        """
        id_ = quote(id_, safe='.')
        response = self.rf_client.request('get', EP_ENTITY_LOOKUP.format(id_)).json()['data']
        return EntityLookup.model_validate(response)

    @debug_call
    @validate_call
    def lookup_bulk(self, ids: list[str], max_workers: Optional[int] = 0) -> list[EntityLookup]:
        """Lookup multiple Recorded Future ID for entity details.

        Endpoint:
            ``entity-match/entity/{id}``

        Args:
            ids (str): id to lookup.
            max_workers (int, optional): number of workers to multithread requests.

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            MatchApiError: if connection error occurs.

        Returns:
            List[EntityLookup] object
        """
        ids = [quote(id_, safe='.') for id_ in ids]
        if max_workers:
            return MultiThreadingHelper.multithread_it(
                max_workers,
                self.lookup,
                iterator=ids,
            )
        return [self.lookup(id_) for id_ in ids]

#################################### TERMS OF USE ###########################################
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
import time
from datetime import datetime
from functools import total_ordering
from typing import Optional, Union

from pydantic import ConfigDict, Field, validate_call

from ..common_models import IdNameType, RFBaseModel
from ..constants import TIMESTAMP_STR
from ..endpoints import EP_LIST
from ..entity_match import EntityMatchMgr, MatchApiError
from ..helpers import debug_call
from ..helpers.helpers import connection_exceptions
from ..rf_client import RFClient
from .constants import ADD_OP, ERROR_NAME, IS_READY_INCREMENT, REMOVE_OP, UNCHANGED_NAME
from .errors import ListApiError
from .models import (
    AddEntityRequestModel,
    ListEntityOperationResponse,
    OwnerOrganisationDetails,
    RemoveEntityRequestModel,
)


class ListInfoOut(RFBaseModel):
    """Validate data received from ``/{listId}/info`` endpoint."""

    id_: str = Field(alias='id')
    name: str
    type_: str = Field(alias='type')
    created: datetime
    updated: datetime
    owner_organisation_details: OwnerOrganisationDetails = Field(
        default_factory=OwnerOrganisationDetails
    )
    owner_id: str
    owner_name: str
    organisation_id: str
    organisation_name: str


class ListStatusOut(RFBaseModel):
    """Validate data received from ``/{listId}/status`` endpoint."""

    size: int
    status: str


@total_ordering
class ListEntity(RFBaseModel):
    """Validate data received from ``/{listId}/entities`` endpoint."""

    entity: IdNameType
    context: Optional[dict] = None
    status: str
    added: datetime

    def __hash__(self):
        return hash(self.entity.id_)

    def __eq__(self, other: 'ListEntity'):
        return self.entity.id_ == other.entity.id_

    def __gt__(self, other: 'ListEntity'):
        return (self.entity.name, self.added) > (other.entity.name, other.added)

    def __str__(self):
        return (
            f'{self.entity.type_}: {self.entity.name}, added {self.added.strftime(TIMESTAMP_STR)}'
        )


class EntityList(RFBaseModel):
    """Validate data received from ``/create`` endpoint."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    rf_client: RFClient = Field(exclude=True)
    match_mgr: EntityMatchMgr = Field(exclude=True)
    log: logging.Logger = Field(exclude=True, default=logging.getLogger(__name__))
    id_: str = Field(alias='id')
    name: str
    type_: str = Field(alias='type')
    created: datetime
    updated: datetime
    owner_id: str
    owner_name: str
    organisation_id: Optional[str] = None
    organisation_name: Optional[str] = None
    owner_organisation_details: OwnerOrganisationDetails = Field(
        default_factory=OwnerOrganisationDetails
    )

    def __hash__(self):
        return hash(self.id_)

    def __eq__(self, other: 'EntityList'):
        return self.id_ == other.id_

    def __str__(self):
        """String representation of the list.

        Returns:
            str: list data with standard info + entities
        """

        def format_date(date):
            return date.strftime(TIMESTAMP_STR)

        def format_field(name, value):
            return f"{name}: {value or 'None'}"

        main_fields = [
            format_field('id', self.id_),
            format_field('name', self.name),
            format_field('type', self.type_),
            format_field('created', format_date(self.created)),
            format_field('last updated', format_date(self.updated)),
            format_field('owner id', self.owner_id),
            format_field('owner name', self.owner_name),
            format_field('organisation id', self.organisation_id),
            format_field('organisation name', self.organisation_name),
        ]

        org_details = self.owner_organisation_details
        org_fields = [
            format_field('owner id', org_details.owner_id),
            format_field('owner name', org_details.owner_name),
            format_field('enterprise id', org_details.enterprise_id),
            format_field('enterprise name', org_details.enterprise_name),
        ]

        sub_orgs = org_details.organisations
        if sub_orgs:
            sub_org_str = '\n    '.join(
                f'organisation id: {org.organisation_id}\n'
                f'    organisation name: {org.organisation_name}'
                for org in sub_orgs
            )
            org_fields.append(f'sub-organisations:\n    {sub_org_str}')
        else:
            org_fields.append('sub-organisations: None')

        return (
            '\n'.join(main_fields) + '\nowner organisation details:\n  ' + '\n  '.join(org_fields)
        )

    @debug_call
    @validate_call
    def add(
        self, entity: Union[str, tuple[str, str]], context: dict = None
    ) -> ListEntityOperationResponse:
        """Add entity to list.

        Endpoint:
            ``list/{id}/entity/add``

        Args:
            entity (str, tuple): ID or (name, type) tuple of entity to add
            context (dict, optional): context object for entity. Defaults to None

        Raises:
            ListApiError: if connection error occurs.

        Returns:
            ListEntityOperationResponse: list/{id}/entity/add response
        """
        return self._list_op(entity, ADD_OP, context=context or {})

    @debug_call
    @validate_call
    def remove(self, entity: Union[str, tuple[str, str]]) -> ListEntityOperationResponse:
        """Remove entity from list.

        Endpoint:
            ``list/{id}/entity/remove``

        Args:
            entity (str, tuple): ID or (name, type) tuple of entity to remove

        Raises:
            ListApiError: if connection error occurs.

        Returns:
            ListEntityOperationResponse: list/{id}/entity/remove response
        """
        return self._list_op(entity, REMOVE_OP)

    @debug_call
    @validate_call
    def bulk_add(self, entities: list[Union[str, tuple[str, str]]]) -> dict:
        """Bulk add entities to list.

        Adds entities 1 at a time due to List API requirement. Logs progress every 10%.

        Endpoint:
            ``list/{id}/entity/add``

        Args:
            entities (list[Union[str, tuple[str, str]]]): list of entity string IDs or
            entity (name, type) tuples to add

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            ValueError: if wrong operation is supplied
            ListApiError: if connection error occurs

        Returns:
            dict: results JSON with added, unchanged, error keys containing lists of entities
        """
        result = self._bulk_op(entities, ADD_OP)
        status = self.status()
        while status.status != 'ready':
            self.log.info(f"Awaiting list 'ready' status, current status '{status.status}'")
            status = self.status()
            time.sleep(IS_READY_INCREMENT)

        return result

    @debug_call
    @validate_call
    def bulk_remove(self, entities: list[Union[str, tuple[str, str]]]) -> dict:
        """Bulk remove entities from list.

        Removes entities 1 at a time due to List API requirement. Logs progress every 10%.

        Endpoint:
            ``list/{id}/entity/remove``

        Args:
            entities (list): list of entity string IDs or entity (name, type) tuples to remove

        Raises:
            ValidationError if any supplied parameter is of incorrect type.
            ValueError: if wrong operation is supplied
            ListApiError: if connection error occurs

        Returns:
            dict: results JSON with removed, unchanged, error keys containing lists of entities
        """
        result = self._bulk_op(entities, REMOVE_OP)
        status = self.status()
        while status.status != 'ready':
            self.log.info(f"Awaiting list 'ready' status, current status '{status.status}'")
            status = self.status()
            time.sleep(IS_READY_INCREMENT)

        return result

    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ListApiError)
    def entities(self) -> list[ListEntity]:
        """Get entities for list.

        Endpoint:
            ``list/{id}/entities``

        Raises:
            ListApiError: if connection error occurs.

        Returns:
            list[ListEntity]: list/{id}/entities JSON response
        """
        url = EP_LIST + '/' + self.id_ + '/entities'
        response = self.rf_client.request('get', url)
        return [ListEntity.model_validate(entity) for entity in response.json()]

    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ListApiError)
    def text_entries(self) -> list[str]:
        """Get text entries for list.

        Endpoint:
            ``list/{id}/textEntries``

        Raises:
            ListApiError: if connection error occurs.

        Returns:
            list[str]: list/{id}/textEntries JSON response
        """
        url = EP_LIST + '/' + self.id_ + '/textEntries'
        return self.rf_client.request('get', url).json()

    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ListApiError)
    def status(self) -> ListStatusOut:
        """Get status information about list.

        Endpoint:
            ``list/{id}/status``

        Raises:
            ListApiError: if connection error occurs

        Returns:
            ListStatusOut: list/{id}/status response
        """
        self.log.debug(f"Getting list status for '{self.name}'")
        url = EP_LIST + f'/{self.id_}/status'
        response = self.rf_client.request('get', url)
        validated_status = ListStatusOut.model_validate(response.json())
        self.log.debug(
            f"List '{self.name}' status: {validated_status.status}, entities: {validated_status.size}"  # noqa: E501
        )

        return validated_status

    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ListApiError)
    def info(self) -> ListInfoOut:
        """Get info for list.

        Endpoint:
            ``list/{id}/info``

        Raises:
            ListApiError: if connection error occurs

        Returns:
            ListInfoOut: list/{id}/info response
        """
        self.log.debug(f"Getting list status for '{self.name}'")
        url = EP_LIST + f'/{self.id_}/info'
        response = self.rf_client.request('get', url)
        validated_info = ListInfoOut.model_validate(response.json())

        return validated_info

    @debug_call
    def _bulk_op(self, entities: list[Union[str, tuple[str, str]]], operation: str) -> dict:
        """Bulk add or remove entities from list.

        List API requires that entities are added one at a time. Logs progress every 10%

        Args:
            entities (list): list of entity string IDs or (name, type) tuples to add
            operation (str): the operation to perform on the list. Can be 'added' or 'removed'.

        Raises:
            ValueError: if wrong operation is supplied
            ListApiError: if connection error occurs

        Returns:
            dict: results JSON with added, unchanged, error keys containing lists of entities added
        """
        if operation == ADD_OP:
            op_func = self.add
            op_name = 'added'
        elif operation == REMOVE_OP:
            op_func = self.remove
            op_name = 'removed'
        else:
            raise ValueError(f"Operation must be either '{ADD_OP}' or '{REMOVE_OP}'")
        result = {op_name: [], UNCHANGED_NAME: [], ERROR_NAME: []}
        total = len(entities)
        step = 10
        for idx, entity in enumerate(entities):
            try:
                if isinstance(entity, str):
                    entity_id = entity
                else:  # entity is tuple
                    entity_id = self.match_mgr.resolve_entity_id(entity[0], entity_type=entity[1])
                    if not entity_id.is_found:
                        result[ERROR_NAME].append({'message': entity_id.content, 'id': entity})
                        continue
                    else:
                        entity_id = entity_id.content.id_
                response = op_func(entity)
                if response.result == op_name:
                    result[op_name].append(entity_id)
                elif response.result == UNCHANGED_NAME:
                    result[UNCHANGED_NAME].append(entity_id)
            except (TypeError, ListApiError, MatchApiError) as err:
                result[ERROR_NAME].append({'message': str(err), 'id': entity})
            if ((idx + 1) / total) * 100 >= step:
                self.log.info(f'{op_name.capitalize()} {step}% of entities')
                step += 10

        return result

    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ListApiError)
    def _list_op(
        self, entity: Union[str, tuple[str, str]], op_name: str, context: dict = None
    ) -> ListEntityOperationResponse:
        """Add or remove an entity from list.

        Args:
            entity (str, tuple): ID or (name, type) tuple of entity to add
            op_name (str): operation to perform. Either 'added' or 'removed'
            context (dict, optional): context object for entity. Defaults to {}

        Raises:
            ListApiError: if connection error occurs

        Returns:
            ListEntityOperationResponse: list/{id}/entity/[add|remove] response
        """
        if isinstance(entity, str):
            resolved_entity_id = entity
        else:
            resolved_entity = self.match_mgr.resolve_entity_id(entity[0], entity_type=entity[1])
            if not resolved_entity.is_found:
                return ListEntityOperationResponse(result=resolved_entity.content)
            resolved_entity_id = resolved_entity.content.id_

        url = EP_LIST + f'/{self.id_}/entity/' + op_name
        request_body = {'entity': {'id': resolved_entity_id}}

        if context:
            request_body['context'] = context
        if op_name == ADD_OP:
            AddEntityRequestModel.model_validate(request_body)
        else:
            RemoveEntityRequestModel.model_validate(request_body)
        response = self.rf_client.request('post', url, data=request_body)
        validated_response = ListEntityOperationResponse.model_validate(response.json())
        if validated_response.result != UNCHANGED_NAME:
            self.log.debug(f'Entity {entity} {validated_response.result} to list {self.id_}')

        return validated_response

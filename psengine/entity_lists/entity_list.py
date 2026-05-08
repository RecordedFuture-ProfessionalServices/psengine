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
from typing import Annotated, Optional, Union

from pydantic import ConfigDict, Field, validate_call
from typing_extensions import Doc

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
    """Validate data received from `/{listId}/info` endpoint."""

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
    """Validate data received from `/{listId}/status` endpoint."""

    size: int
    status: str


@total_ordering
class ListEntity(RFBaseModel):
    """Validate data received from `/{listId}/entities` endpoint."""

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
    """Validate data received from `/create` endpoint."""

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

    def __str__(self) -> Annotated[str, Doc('List data with standard info and entities.')]:
        """Return the string representation of the list."""

        def format_date(date):
            return date.strftime(TIMESTAMP_STR)

        def format_field(name, value):
            return f'{name}: {value or "None"}'

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
        self,
        entity: Annotated[
            Union[str, tuple[str, str]], Doc('ID or (name, type) tuple of the entity to add.')
        ],
        context: Annotated[Optional[dict], Doc('Context object for the entity.')] = None,
    ) -> Annotated[
        ListEntityOperationResponse, Doc('Response from the `list/{id}/entity/add` endpoint.')
    ]:
        """Add an entity to a list.

        Endpoint:
            `list/{id}/entity/add`

        Raises:
            ValidationError: if any supplied parameter is of incorrect type.
            ListApiError: If connection error occurs.
        """
        return self._list_op(entity, ADD_OP, context=context or {})

    @debug_call
    @validate_call
    def remove(
        self,
        entity: Annotated[
            Union[str, tuple[str, str]], Doc('ID or (name, type) tuple of the entity to remove.')
        ],
    ) -> Annotated[
        ListEntityOperationResponse, Doc('Response from the `list/{id}/entity/remove` endpoint.')
    ]:
        """Remove an entity from a list.

        Endpoint:
            `list/{id}/entity/remove`

        Raises:
            ValidationError: if any supplied parameter is of incorrect type.
            ListApiError: If connection error occurs.
        """
        return self._list_op(entity, REMOVE_OP)

    @debug_call
    @validate_call
    def bulk_add(
        self,
        entities: Annotated[
            list[Union[str, tuple[str, str]]],
            Doc('List of entity string IDs or (name, type) tuples to add.'),
        ],
    ) -> Annotated[
        dict,
        Doc(
            "Results JSON with 'added', 'unchanged', and 'error' keys containing lists of entities."
        ),
    ]:
        """Bulk add entities to a list.

        Adds entities one at a time due to List API requirement. Logs progress every 10%.

        Endpoint:
            `list/{id}/entity/add`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            ValueError: If an invalid operation is supplied.
            ListApiError: If connection error occurs.
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
    def bulk_remove(
        self,
        entities: Annotated[
            list[Union[str, tuple[str, str]]],
            Doc('List of entity string IDs or (name, type) tuples to remove.'),
        ],
    ) -> Annotated[
        dict,
        Doc(
            "Results JSON with 'removed', 'unchanged', and 'error' keys with the lists of entities."
        ),
    ]:
        """Bulk remove entities from a list.

        Removes entities one at a time due to List API requirement. Logs progress every 10%.

        Endpoint:
            `list/{id}/entity/remove`

        Raises:
            ValidationError: If any supplied parameter is of incorrect type.
            ValueError: If an invalid operation is supplied.
            ListApiError: If connection error occurs.
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
    def entities(
        self,
    ) -> Annotated[list[ListEntity], Doc('Response from the `list/{id}/entities` endpoint.')]:
        """Get entities for a list.

        Endpoint:
            `list/{id}/entities`

        Raises:
            ListApiError: If connection error occurs.
        """
        url = EP_LIST + '/' + self.id_ + '/entities'
        response = self.rf_client.request('get', url)
        return [ListEntity.model_validate(entity) for entity in response.json()]

    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ListApiError)
    def text_entries(
        self,
    ) -> Annotated[list[str], Doc('Response from the `list/{id}/textEntries` endpoint.')]:
        """Get text entries for a list.

        Endpoint:
            `list/{id}/textEntries`

        Raises:
            ListApiError: If connection error occurs.
        """
        url = EP_LIST + '/' + self.id_ + '/textEntries'
        return self.rf_client.request('get', url).json()

    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ListApiError)
    def status(self) -> ListStatusOut:
        """Get status information about list.

        Endpoint:
            `list/{id}/status`

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
            f"List '{self.name}' status: {validated_status.status}, "
            f'entities: {validated_status.size}'
        )

        return validated_status

    @debug_call
    @connection_exceptions(ignore_status_code=[], exception_to_raise=ListApiError)
    def info(self) -> Annotated[ListInfoOut, Doc('Response from the `list/{id}/info` endpoint.')]:
        """Get info for a list.

        Endpoint:
            `list/{id}/info`

        Raises:
            ListApiError: If connection error occurs.
        """
        self.log.debug(f"Getting list status for '{self.name}'")
        url = EP_LIST + f'/{self.id_}/info'
        response = self.rf_client.request('get', url)
        return ListInfoOut.model_validate(response.json())

    @debug_call
    def _bulk_op(
        self,
        entities: Annotated[
            list[Union[str, tuple[str, str]]],
            Doc('List of entity string IDs or (name, type) tuples to process.'),
        ],
        operation: Annotated[
            str, Doc("The operation to perform on the list. Must be 'added' or 'removed'.")
        ],
    ) -> Annotated[
        dict,
        Doc(
            "Results JSON with 'added', 'unchanged', and 'error' keys with the processed entities."
        ),
    ]:
        """Bulk add or remove entities from a list.

        The List API requires entities to be processed one at a time. Logs progress every 10%.

        Raises:
            ValueError: If an invalid operation is supplied.
            ListApiError: If connection error occurs.
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
        self,
        entity: Annotated[
            Union[str, tuple[str, str]], Doc('ID or (name, type) tuple of the entity to process.')
        ],
        op_name: Annotated[str, Doc("Operation to perform. Must be 'added' or 'removed'.")],
        context: Annotated[Optional[dict], Doc('Optional context object for the entity.')] = None,
    ) -> Annotated[
        ListEntityOperationResponse,
        Doc('Response from the `list/{id}/entity/[add|remove]` endpoint.'),
    ]:
        """Add or remove an entity from a list.

        Raises:
            ListApiError: If connection error occurs.
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

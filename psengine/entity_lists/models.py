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


from pydantic import Field

from ..common_models import IdName, RFBaseModel


class EntityID(RFBaseModel):
    id_: str = Field(alias='id')


class ListEntityTag(IdName):
    """Validate a single tag received from `/{listId}/entitiesWithTags` endpoint.

    Tags are **not** free-text. They are a fixed set of 57 predefined values, populated only for
    lists whose type has tagging enabled (currently Third-Parties Watch Lists), so arbitrary tag
    strings cannot be supplied or expected. `id` always has the form
    `enum:EntityListTag:<name>`, for example `enum:EntityListTag:tier1`.

    `name` is the tag's API value (`tier1`), not its display name (`Tier 1`).

    See https://docs.recordedfuture.com/reference/lists-available-tags for the full list of
    valid tags.
    """


class Organisation(RFBaseModel):
    organisation_id: str
    organisation_name: str


class OwnerOrganisationDetails(RFBaseModel):
    owner_id: str | None = None
    owner_name: str | None = None
    organisations: list[Organisation] | None = []
    enterprise_id: str | None = None
    enterprise_name: str | None = None


class CreateRequestModel(RFBaseModel):
    """Validate data sent to `/create` endpoint."""

    name: str
    type_: str = Field(alias='type', default=None)


class SearchInModel(RFBaseModel):
    """Validate data sent to `/search` endpoint."""

    name: str | None = None
    type_: str = Field(alias='type', default=None)
    limit: int | None = None


class InfoRequestModel(RFBaseModel):
    """Validate data sent to `/{listId}/info` endpoint."""

    list_id: str


class StatusRequestModel(RFBaseModel):
    """Validate data sent to `/{listId}/status` endpoint."""

    list_id: str


class EntitiesRequestModel(RFBaseModel):
    """Validate data sent to `/{listId}/entities` endpoint."""

    list_id: str


class AddEntityRequestModel(RFBaseModel):
    """Validate data sent to `/{listId}/entity/add` endpoint."""

    entity: EntityID
    context: dict | None = None


class RemoveEntityRequestModel(RFBaseModel):
    """Validate data sent to `/{listId}/entity/remove` endpoint."""

    entity: EntityID


class ListEntityOperationResponse(RFBaseModel):
    """Validate data received from `/{listId}/entity/remove` endpoint."""

    result: str

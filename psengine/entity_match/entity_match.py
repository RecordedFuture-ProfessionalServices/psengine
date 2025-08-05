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

from typing import Optional, Union

from pydantic import Field

from ..common_models import IdNameType, RFBaseModel
from .models import Attributes


class EntityMatchIn(RFBaseModel):
    """Model to validate data sent to `entity-match/match` endpoint."""

    name: str
    type_: Optional[list[str]] = Field(alias='type', default=[])
    limit: int = Field(default=10)


class EntityLookup(RFBaseModel):
    """Model to validate data received from the `entity-match/entity/{id}` endpoint.

    This class supports string representation, equality comparison, and hashing of `EntityLookup`
    instances.

    String Representation:
        Returns a string representation of the `EntityLookup` instance including the
        entity match name, type, and ID.

        ```python
        >>> print(entity)
        Entity Name: BlueDelta, Type: Organization, ID: L37nw-'
        ```

    Equality:
        Validates equality between two `EntityLookup` objects based on the entity ID.

    Hashing:
        Defines uniqueness of an `EntityLookup` object by the entity ID.
    """

    id_: str = Field(alias='id')
    type_: str = Field(alias='type')
    attributes: Attributes

    def __hash__(self):
        return hash(self.id_)

    def __eq__(self, other: 'EntityLookup'):
        return self.id_ == other.id_

    def __str__(self):
        return f'Entity Name: {self.attributes.name}, Type: {self.type_}, ID: {self.id_}'


class ResolvedEntity(RFBaseModel):
    """Model to validate data received from the `entity-match/match` endpoint.

    This class supports string representation of `ResolvedEntity` instances.

    String Representation:
        Returns a string representation of the `ResolvedEntity` instance including the
        entity match name, type, and ID.

        ```python
        >>> print(entity_match)
        Entity: Wannacry, Type: Username, ID: Ub_GAO
        ```
    """

    entity: str
    is_found: bool
    content: Union[str, IdNameType]

    def __str__(self):
        if isinstance(self.content, IdNameType):
            return f'Entity: {self.entity}, Type: {self.content.type_}, ID: {self.content.id_}'
        return f'Entity: {self.entity}, {self.content}'

    def __repr__(self):
        if isinstance(self.content, IdNameType):
            return f'Entity: {self.entity}, Type: {self.content.type_}, ID: {self.content.id_}'
        return f'Entity: {self.entity}, {self.content}'
